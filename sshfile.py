import socket, threading, os, time

PORT = 5001
BROADCAST_PORT = 5002
BROADCAST_INTERVAL = 2

peers = set()
file_to_send = None

# --- File sending ---
def send_file(file_path, addr):
    try:
        with socket.socket() as s:
            s.connect((addr, PORT))
            s.sendall(os.path.basename(file_path).encode() + b'\0')
            with open(file_path, 'rb') as f:
                while chunk := f.read(4096):
                    s.sendall(chunk)
        print(f"[+] Sent {file_path} to {addr}")
    except Exception as e:
        print(f"[!] Failed to send to {addr}: {e}")

# --- File receiving ---
def handle_client(conn, addr):
    name = b""
    while True:
        b = conn.recv(1)
        if b == b'\0': break
        name += b
    file_name = name.decode()

    answer = input(f"{addr[0]} wants to send {file_name}. Accept? [y/N]: ").strip().lower()
    if answer == 'y':
        with open(file_name, 'wb') as f:
            while data := conn.recv(4096):
                f.write(data)
        print(f"[+] Received file {file_name}")
    else:
        print(f"[-] Declined file {file_name}")
    conn.close()

def server():
    with socket.socket() as s:
        s.bind(('', PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# --- Broadcast presence ---
def broadcaster():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = b"P2P_FILE_SHARE"
    while True:
        s.sendto(msg, ('<broadcast>', BROADCAST_PORT))
        time.sleep(BROADCAST_INTERVAL)

def listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', BROADCAST_PORT))
    while True:
        data, addr = s.recvfrom(1024)
        if data == b"P2P_FILE_SHARE":
            peers.add(addr[0])

# --- CLI File Selection ---
def select_file():
    global file_to_send
    while True:
        path = input("Enter path of file to send: ").strip()
        if os.path.isfile(path):
            file_to_send = path
            break
        print("[!] Invalid file path, try again.")

def main_loop():
    while True:
        print("\nDetected peers:")
        for ip in sorted(peers):
            print(" -", ip)
        print("Options:")
        print("1. Send file to a peer")
        print("2. Send file to all peers")
        print("3. Select a new file")
        choice = input("Choose an option [1-3]: ").strip()
        if choice == '1':
            if not file_to_send:
                print("[!] No file selected")
                continue
            target = input("Enter peer IP: ").strip()
            if target in peers:
                send_file(file_to_send, target)
            else:
                print("[!] Peer not detected")
        elif choice == '2':
            if not file_to_send:
                print("[!] No file selected")
                continue
            for ip in peers:
                send_file(file_to_send, ip)
        elif choice == '3':
            select_file()
        else:
            print("[!] Invalid choice")

if __name__ == "__main__":
    threading.Thread(target=server, daemon=True).start()
    threading.Thread(target=broadcaster, daemon=True).start()
    threading.Thread(target=listener, daemon=True).start()

    print("[*] LAN peer discovery started")
    select_file()
    main_loop()
