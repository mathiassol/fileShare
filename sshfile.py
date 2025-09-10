import socket
import threading
import time

PORT = 5001
BROADCAST_PORT = 5002
BROADCAST_INTERVAL = 2

peers = set()


# --- Broadcast presence ---
def broadcaster():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    msg = f"P2P_FILE_SHARE:{local_ip}".encode()
    while True:
        s.sendto(msg, ('<broadcast>', BROADCAST_PORT))
        time.sleep(BROADCAST_INTERVAL)


# --- Listen for other peers ---
def listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', BROADCAST_PORT))
    while True:
        data, addr = s.recvfrom(1024)
        msg = data.decode()
        if msg.startswith("P2P_FILE_SHARE:"):
            peer_ip = msg.split(":")[1]
            peers.add(peer_ip)


# --- Receive files ---
def handle_client(conn, addr):
    # Receive filename
    name_bytes = b""
    while True:
        b = conn.recv(1)
        if b == b'\0':
            break
        name_bytes += b
    file_name = name_bytes.decode()
    print(f"[+] Incoming file '{file_name}' from {addr[0]}")

    # Save file
    with open(file_name, 'wb') as f:
        while chunk := conn.recv(4096):
            f.write(chunk)
    print(f"[+] File '{file_name}' saved.")

    conn.close()


def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', PORT))
        s.listen()
        print(f"[*] Listening for incoming files on port {PORT}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    threading.Thread(target=server, daemon=True).start()
    threading.Thread(target=broadcaster, daemon=True).start()
    threading.Thread(target=listener, daemon=True).start()

    print("[*] Receiver running. Broadcasting presence and waiting for files...")
    while True:
        # Show detected peers periodically
        if peers:
            print("Detected peers:", ", ".join(sorted(peers)))
        time.sleep(5)
