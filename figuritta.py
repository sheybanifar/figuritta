import socket
import struct
from pathlib import Path

INFORM = 'INFORM_FILE_DATA'

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

class Header:
    def __init__(self, msg_type=None, payload_size=None) -> None:
        self.msg_type = msg_type
        self.payload_size = payload_size

class Payload:
    def __init__(self) -> None:
        self.filename_len = None
        self.filename = None
        self.filesize = None
        self.file_data = None
    
    def get_size(self):


def header_send(sock: socket.socket, file: str | Path):
    filename, filesize = get_size(file)
    # initializing header
    fmt = '!QQ'
    fname_b = filename.encode()
    fname_length = len(fname_b)

    header = struct.pack(fmt, filesize, fname_length)
    packet = header + fname_b

    sock.sendall(packet)

def header_recv(sock):
        fmt = '!QQ'
        fmt_size = struct.calcsize(fmt)

        header = recv_all(sock, fmt_size)

        filesize, fname_length = struct.unpack(fmt, header)
        # print(filesize, fname_length)
        fname_b = recv_all(sock, fname_length)
        print(fname_b)

if __name__ == '__main__':
    while True:
        try:
            print('1- Send')
            print('2- Receive')
            choice = input('Which one? ')

            if choice in ('1', '2') and choice == '1':
                with socket.create_connection(('127.0.0.1', 2001)) as client:
                    header_send(client, r"")
            elif choice in ('1', '2') and choice == '2':
                with socket.create_server(('127.0.0.1', 2001)) as server:
                    connection, address = server.accept()
                    # print(f'Established: "{address[0]:{address[1]}}"')
                    header_recv(connection)
            else:
                print('Invalid response!')
                continue
        except KeyboardInterrupt:
            break