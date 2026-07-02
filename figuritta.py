from tqdm import tqdm

import socket
import struct
from pathlib import Path
from enum import IntEnum

class OperationError(Exception):
    pass

def get_size(file: str | Path):
    if isinstance(file, Path) and file.exists():
        filename = file.name
        filesize = file.stat().st_size
        return (filename, filesize)
    else:
        path_obj = Path(file)
        if path_obj.exists():
            filename = path_obj.name
            filesize = path_obj.stat().st_size
            return (filename, filesize)
        raise FileNotFoundError('File not found!')

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

class MessageType(IntEnum):
    FILE_INFO = 1
    FILE_CHUNK = 2
    END_OF_FILE = 3
    END_OF_TRANSFER = 4

def send_message(sock: socket.socket, msg_type: int, payload):
    version = 1
    header = HEADER_STRUCT.pack(version, msg_type, len(payload), 0)
    packet = header + payload

    sock.sendall(packet)

def recv_message(sock: socket.socket):
    header = recv_all(sock, HEADER_STRUCT.size)
    version, msg_type, payload_length, reserved = HEADER_STRUCT.unpack(header)
    payload = recv_all(sock, payload_length)
    return msg_type, payload


def send_file(sock: socket.socket, file: str | Path):
    filename, filesize = get_size(file)
    filename_b = filename.encode()
    filename_len = len(filename_b)

    file_info = struct.pack(
        '!HQ', filename_len, filesize
    )

    packet = file_info + filename_b

    sock.sendall(packet)

    with open(file, mode='br') as f, tqdm(
        total=filesize,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        desc='Sending'
    ) as progress:
        while read_bytes := f.read(1024):
            sock.sendall(read_bytes)
            progress.update(len(read_bytes))

def receive_file_info(sock):
    expected_bytes = struct.calcsize('!HQ')
    received_bytes = recv_all(sock, expected_bytes)

    filename_len, filesize = struct.unpack('!HQ', received_bytes)

    filename_b = recv_all(sock, filename_len)
    filename = filename_b.decode()

    return filename, filesize

def receive_file(sock):
    filename, filesize = receive_file_info(sock)

    with open(f'inbox/{filename}', 'wb') as f:
        received_bytes = 0
        with tqdm(
            total=filesize,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            desc='Receiving'
        ) as progress:
            while received_bytes < filesize:
                remaining = filesize - received_bytes
                chunk = recv_all(sock, min(remaining, 1024 * 64))
                if chunk:
                    f.write(chunk)
                    received_bytes += len(chunk)
                    progress.update(len(chunk))
    
    return received_bytes

if __name__ == '__main__':
    try:
        print('1- Send')
        print('2- Receive')
        choice = input('Which one? ')

        if choice in ('1', '2') and choice == '1':
            file = input('Enter file path to send: ')
            with socket.create_connection(('127.0.0.1', 2001)) as client:
                send_file(client, file)
        elif choice in ('1', '2') and choice == '2':
            with socket.create_server(('127.0.0.1', 2001)) as server:
                connection, address = server.accept()
                receive_file(connection)
        else:
            print('Invalid response!')
    except (KeyboardInterrupt, EOFError):
        exit()