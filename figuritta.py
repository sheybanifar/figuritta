import socket
import struct
from pathlib import Path

INFORM_FILE_DATA = 1

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
        raise OperationError('File not found!')

def recv_all(sock, total):
    expected_bytes = total
    received_bytes = 0

    stream = bytes()

    while received_bytes < expected_bytes:
        chunk = sock.recv(expected_bytes - received_bytes)
        received_bytes += len(chunk)
        stream += chunk
    
    return stream

def inform(sock: socket.socket, file: str | Path):
    filename, filesize = get_size(file)
    fname_b = filename.encode()
    fname_length = len(fname_b)

    payload = (
        struct.pack('!H', fname_length)
        + fname_b
        + struct.pack('!Q', filesize)
    )

    header = struct.pack('!HQ', INFORM_FILE_DATA, len(payload))

    packet = header + payload

    sock.sendall(packet)

def get_inform(sock, payload_len):
    offset = 0
    payload = recv_all(sock, payload_len)

    fname_len = struct.unpack(
        '!H',
        payload[offset:offset + struct.calcsize('!H')]
    )[0]

    offset += struct.calcsize('!H')

    filename = payload[offset:offset + fname_len].decode()

    offset += fname_len

    filesize = struct.unpack(
        '!Q',
        payload[offset:]
    )[0]

    print(f'{filename} -> {filesize} B')

if __name__ == '__main__':
    while True:
        try:
            print('1- Send')
            print('2- Receive')
            choice = input('Which one? ')

            if choice in ('1', '2') and choice == '1':
                file = input('Enter file path to send: ')
                with socket.create_connection(('127.0.0.1', 2001)) as client:
                    inform(client, file)
            elif choice in ('1', '2') and choice == '2':
                with socket.create_server(('127.0.0.1', 2001)) as server:
                    connection, address = server.accept()
                    fmt = '!HQ'
                    fmt_size = struct.calcsize(fmt)

                    header = recv_all(connection, fmt_size)

                    msg_type, payload_len = struct.unpack(fmt, header)
                    if msg_type == INFORM_FILE_DATA:
                        get_inform(connection, payload_len)
            else:
                print('Invalid response!')
                continue
        except KeyboardInterrupt:
            break