import socket
import threading
import os

PORT = 5001


def handle_client(conn, addr):
    # Receive file name
    name_bytes = b""
    while True:
        b = conn.recv(1)
        if b == b'\0':
            break
        name_bytes += b
    file_name = name_bytes.decode()

    print(f"[+] Incoming file '{file_name}' from {addr[0]}")

    # Save file
    with open(file_name, "wb") as f:
        while chunk := conn.recv(4096):
            f.write(chunk)
    print(f"[+] File '{file_name}' saved.")

    conn.close()


def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", PORT))
        s.listen()
        print(f"[*] Listening for incoming files on port {PORT}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    server()
