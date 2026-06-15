import socket
from pathlib import Path

def file_parser(file: str | Path):
    if isinstance(file, Path) and file.exists():
        pass
    else:
        path_obj = Path(file)
        if path_obj.is_absolute():
            return

def send_file(sock: socket.socket, file: str | Path):
    pass