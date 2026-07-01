import socket
import struct
from pathlib import Path

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

        if not chunk:
            raise ConnectionError('Connection was broken while receiving data!')

        received_bytes += len(chunk)
        stream += chunk
    
    return stream

def send_file(sock: socket.socket, file: str | Path):
    filename, filesize = get_size(file)
    filename_b = filename.encode()
    filename_len = len(filename_b)

    file_info = struct.pack(
        '!HQ', filename_len, filesize
    )

    packet = file_info + filename_b

    sock.sendall(packet)

    with open(file, mode='br') as f:
        while read_bytes := f.read(1024):
            sock.sendall(read_bytes)

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
        remaining = 0
        while received_bytes < filesize:
            remaining = filesize - received_bytes
            chunk = recv_all(sock, min(remaining, 1024 * 64))
            if chunk:
                f.write(chunk)
                received_bytes += len(chunk)
    
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