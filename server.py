import socket
import os
import threading

HOST = '0.0.0.0'
PORT = 5001

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        # Ask server user for file path
        file_path = input("Enter the path of the file to send: ").strip()
        if not os.path.isfile(file_path):
            print("File does not exist.")
            conn.sendall(b'ERROR: File not found')
            conn.close()
            return

        file_name = os.path.basename(file_path)
        conn.sendall(file_name.encode())

        # Receive Y/N from client
        response = conn.recv(1024).decode().strip().upper()
        if response == 'Y':
            print(f"Client {addr} accepted the file. Sending...")
            with open(file_path, 'rb') as f:
                while chunk := f.read(1024):
                    conn.sendall(chunk)
            print(f"File sent to {addr} successfully.")
        else:
            print(f"Client {addr} declined the file.")

    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        conn.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
