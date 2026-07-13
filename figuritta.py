import socket
import struct
from pathlib import Path
from enum import IntEnum
from collections.abc import Iterable

PROTOCOL_VERSION = 1
CHUNK_SIZE = 1024 * 64

class OperationError(Exception):
    pass

def get_file_info(file: str | Path):
    path = Path(file)
    if not path.exists():
        raise FileNotFoundError('File not found!')
    return path.name, path.stat().st_size

def recv_all(sock, total):
    expected_bytes = total
    received_bytes = 0

    stream = bytearray()

    while received_bytes < expected_bytes:
        chunk = sock.recv(expected_bytes - received_bytes)

        if not chunk:
            raise ConnectionError('Connection was broken while receiving data!')

        received_bytes += len(chunk)
        stream.extend(chunk)
    
    return bytes(stream)

HEADER_STRUCT = struct.Struct('!BBQH')
STRUCT16 = struct.Struct('!H')
STRUCT64 = struct.Struct('!Q')

class MessageType(IntEnum):
    FILE_INFO = 1
    FILE_CHUNK = 2
    END_OF_TRANSFER = 3

def build_file_info_payload(file: str | Path):
    filename, filesize = get_file_info(file)
    filename_b = filename.encode()
    filename_len = len(filename_b)

    payload = (
        STRUCT16.pack(filename_len)
        + filename_b
        + STRUCT64.pack(filesize)
    )

    return payload

def parse_file_info_payload(payload: bytes):
    filename_len = STRUCT16.unpack_from(payload)[0]
    offset = STRUCT16.size

    filename = payload[offset:offset + filename_len].decode()
    offset += filename_len

    filesize: int = STRUCT64.unpack_from(payload, offset)[0]

    return filename, filesize

def send_message(sock: socket.socket, msg_type: MessageType, payload: bytes):
    version = PROTOCOL_VERSION
    header = HEADER_STRUCT.pack(version, msg_type, len(payload), 0)
    packet = header + payload

    sock.sendall(packet)

def recv_message(sock: socket.socket) -> tuple[MessageType, bytes]:
    header = recv_all(sock, HEADER_STRUCT.size)
    version, msg_type, payload_length, reserved = HEADER_STRUCT.unpack(header)
    msg_type = MessageType(msg_type)

    if version != PROTOCOL_VERSION:
        raise OperationError('Incorrect protocol version!')
    
    if reserved != 0:
        raise OperationError('Bad Header!')

    payload = recv_all(sock, payload_length)
    return msg_type, payload

def send_file(sock: socket.socket, file: str | Path):
    file_info_payload = build_file_info_payload(file)
    send_message(
        sock, MessageType.FILE_INFO, file_info_payload
    )
    with open(file, mode='rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            send_message(
                sock, MessageType.FILE_CHUNK, chunk
            )

def send_files(sock: socket.socket, files: Iterable[str | Path]):
    for file in files:
        send_file(sock, file)

    send_message(
        sock,
        MessageType.END_OF_TRANSFER,
        b''
    )

def receive_file_chunks(
        sock: socket.socket,
        filename: str,
        filesize: int,
        dst_dir: str | Path
        ):
    path = Path(dst_dir) / filename
    with open(path, 'bx+') as f:
        received_bytes = 0
        while received_bytes < filesize:
            # Protocol guarantees that every FILE_CHUNK
            # after FILE_INFO belongs to the current file.
            msg_type, chunk = recv_message(sock)
            if msg_type != MessageType.FILE_CHUNK:
                raise OperationError('Invalid message type!')
            
            f.write(chunk)
            received_bytes += len(chunk)
    
    return path

def receive_file(sock: socket.socket, dst_dir: str | Path):
    msg_type, payload = recv_message(sock)

    if msg_type != MessageType.FILE_INFO:
        raise OperationError('Expected FILE_INFO.')
    
    filename, filesize = parse_file_info_payload(payload)

    return receive_file_chunks(sock, filename, filesize, dst_dir)

def receive_files(sock: socket.socket, dst_dir: str | Path):
    received_files = []
    while True:
        msg_type, payload = recv_message(sock)

        if msg_type == MessageType.END_OF_TRANSFER:
            break
        if msg_type != MessageType.FILE_INFO:
            raise OperationError('Expected FILE_INFO or END_OF_TRANSFER!')
        
        filename, filesize = parse_file_info_payload(payload)

        path = receive_file_chunks(sock, filename, filesize, dst_dir)
        if path:
            received_files.append(path)
    
    return receive_files

def path_extract(user_input: str):
    

if __name__ == '__main__':
    print('1- Send')
    print('2- Receive')
    try:
        choice = input('Which one? ')
    except (KeyboardInterrupt, EOFError):
        exit()
    if choice in ('1', '2') and choice == '1':
        file = input('Enter file path to send: ')
        with socket.create_connection(('127.0.0.1', 2001)) as client:
            send_file(client, file)
    elif choice in ('1', '2') and choice == '2':
        with socket.create_server(('127.0.0.1', 2001)) as server:
            connection, address = server.accept()
            receive_file(connection, 'inbox/')
    else:
        print('Invalid response!')
    