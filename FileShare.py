import socket, threading, os, time, customtkinter as ctk, pystray
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw

PORT = 5001
BROADCAST_PORT = 5002
BROADCAST_INTERVAL = 2

peers = set()
file_to_send = None

# --- File sending ---
def send_file(file_path, addr):
    def _send():
        try:
            with socket.socket() as s:
                s.connect((addr, PORT))
                s.sendall(os.path.basename(file_path).encode() + b'\0')
                with open(file_path, 'rb') as f:
                    while chunk := f.read(4096):
                        s.sendall(chunk)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Error", str(e)))
    threading.Thread(target=_send, daemon=True).start()

# --- File receiving ---
def handle_client(conn, addr):
    name = b""
    while True:
        b = conn.recv(1)
        if b == b'\0': break
        name += b
    file_name = name.decode()

    def ask_accept():
        if messagebox.askyesno("File incoming", f"{addr[0]} wants to send {file_name}. Accept?"):
            with open(file_name, 'wb') as f:
                while data := conn.recv(4096):
                    f.write(data)
        conn.close()

    root.after(0, ask_accept)  # schedule on main thread

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

# --- GUI to select file and send to peers ---
def open_send_window():
    global file_to_send
    file_path = filedialog.askopenfilename(title="Select file to send")
    if not file_path:
        return
    file_to_send = file_path

    win = ctk.CTkToplevel(root)
    win.title("Send File to Peers")
    win.geometry("300x400")

    label = ctk.CTkLabel(win, text=f"File: {os.path.basename(file_to_send)}")
    label.pack(pady=10)

    frame = ctk.CTkScrollableFrame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_peers():
        for widget in frame.winfo_children():
            widget.destroy()
        for ip in sorted(peers):
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=ip).pack(side="left", padx=5)
            ctk.CTkButton(row, text="Send", width=60,
                           command=lambda ip=ip: send_file(file_to_send, ip)).pack(side="right", padx=5)
        win.after(2000, refresh_peers)

    refresh_peers()

# --- Tray icon ---
def create_icon():
    image = Image.new('RGB', (64, 64), color='black')
    draw = ImageDraw.Draw(image)
    draw.rectangle((16,16,48,48), fill='white')
    return image

def start_tray():
    icon = pystray.Icon(
        "P2P",
        create_icon(),
        "P2P File Transfer",
        menu=pystray.Menu(pystray.MenuItem("Send File", lambda icon, item: root.after(0, open_send_window)))
    )
    # On Linux, run in detached mode so it doesn't block
    icon.run_detached()

# --- Main ---
root = ctk.CTk()
root.withdraw()  # start hidden

threading.Thread(target=server, daemon=True).start()
threading.Thread(target=broadcaster, daemon=True).start()
threading.Thread(target=listener, daemon=True).start()
threading.Thread(target=start_tray, daemon=True).start()

root.mainloop()
