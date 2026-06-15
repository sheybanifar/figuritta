import socket
import struct
from pathlib import Path

class OperationError(Exception):
    pass

def file_parser(file: str | Path):
    if isinstance(file, Path) and file.exists():
        filename = file.name
        filesize = file.stat().st_size
        return (filename, filesize)
    else:
        path_obj = Path(file)
        if path_obj.is_absolute():
            filename = file.name
            filesize = file.stat().st_size
            return (filename, filesize)
        raise OperationError('File not found!')

def recv_all(sock, total):
    

def send_file(sock: socket.socket, file: str | Path):
    filename, filesize = file_parser(file)
    # initializing header
    fmt = '!Q'
    fname_b = bytes(filename)
    fsize_b = bytes(filesize)
    stream = fname_b + fsize_b
    header = struct.pack(fmt, stream)

    sock.sendall(header)

    with socket.create_connection(('127.0.0.1', 2001)) as connection:
        send_file(connection, r'I:\MyProjects\figuritta\goals.txt')

        while True:
            msg = recv_all()