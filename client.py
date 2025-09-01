import socket
import os
from pathlib import Path

SERVER_IP = '127.0.0.1'  # Change to server IP
PORT = 5001

# Get the user's Downloads folder
downloads_folder = str(Path.home() / "Downloads")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((SERVER_IP, PORT))

    # Receive the filename
    file_name = s.recv(1024).decode()
    if file_name.startswith("ERROR"):
        print(file_name)
    else:
        choice = input(f"Do you want to download '{file_name}'? (Y/N): ").strip().upper()
        s.sendall(choice.encode())

        if choice == 'Y':
            save_path = os.path.join(downloads_folder, file_name)
            with open(save_path, 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
            print(f"File downloaded successfully to {save_path}.")
        else:
            print("File declined.")
