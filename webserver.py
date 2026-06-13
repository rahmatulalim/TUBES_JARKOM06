import socket
import threading
import os
from datetime import datetime

# Konfigurasi Alamat dan Port sesuai Modul
HOST = '0.0.0.0' 
TCP_PORT = 8000
UDP_PORT = 9000

# Path folder status untuk error handling
STATUS_FOLDER = 'status'

def send_error_response(client_socket, status_code, status_msg):
    """Fungsi untuk mengirim file HTML dari folder 'status'"""
    filepath = os.path.join(STATUS_FOLDER, f"{status_code}.html")
    
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as f:
            content = f.read()
    else:
        # Fallback jika file .html tidak ditemukan di folder status
        content = f"<h1>{status_code} {status_msg}</h1>".encode()

    response_header = (
        f"HTTP/1.1 {status_code} {status_msg}\r\n"
        f"Content-Type: text/html\r\n"
        f"Content-Length: {len(content)}\r\n"
        "\r\n"
    )
    client_socket.sendall(response_header.encode() + content)

def handle_tcp_client(client_socket, client_address):
    try:
        request = client_socket.recv(2048).decode(errors='ignore')
        if not request: return

        lines = request.split('\r\n')
        if len(lines) > 0:
            first_line = lines[0].split()
            if len(first_line) >= 2:
                method = first_line[0]
                filename = first_line[1]

                # Ambil waktu sekarang untuk timestamp log
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if method != "GET":
                    send_error_response(client_socket, 500, "Internal Server Error")
                    return

                if filename == '/': filename = '/index.html'
                filepath = filename.lstrip('/')

                if os.path.isfile(filepath):
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    
                    # Penentuan MIME Type berdasarkan ekstensi
                    if filepath.endswith(".html"):
                        ctype = "text/html; charset=utf-8"
                    elif filepath.endswith(".css"):
                        ctype = "text/css"
                    elif filepath.endswith(".png"):
                        ctype = "image/png"
                    elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
                        ctype = "image/jpeg"
                    elif filepath.endswith(".mp4"):
                        ctype = "video/mp4"
                    else:
                        ctype = "application/octet-stream"

                    # 4. Kirim HTTP Response 200 OK (Indentasi sudah diperbaiki)
                    header = (
                        "HTTP/1.1 200 OK\r\n"
                        f"Content-Type: {ctype}\r\n"
                        f"Content-Length: {len(content)}\r\n"
                        "\r\n"
                    )
                    client_socket.sendall(header.encode() + content)
                    # Sesuai ketentuan: IP Proxy, Jalur berkas, Timestamp, Status Code
                    print(f"\033[92m[TCP] {timestamp} | Status: 200 OK | File: {filename} | Proxy IP: {client_address[0]}\033[0m")
                else:
                    print(f"\033[91m[TCP] {timestamp} | Status: 404 Not Found | File: {filename} | Proxy IP: {client_address[0]}\033[0m")
                    send_error_response(client_socket, 404, "Not Found")

    except Exception as e:
        print(f"\033[91m[ERROR] Server Error: {e}\033[0m")
        try:
            send_error_response(client_socket, 500, "Internal Server Error")
        except:
            pass
    finally:
        client_socket.close()

def start_udp_server():
    """UDP Echo Server untuk pengujian QoS (RTT, Jitter, Loss)"""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))
    print(f"[*] UDP Echo Server active on port {UDP_PORT}")
    
    while True:
        data, addr = udp_sock.recvfrom(2048)
        
        # --- LOG UDP REQ ---
        print(f"\033[94m[UDP] Paket QoS diterima & dipantulkan ke {addr}\033[0m")
        
        # Pantulkan data tanpa modifikasi untuk pengukuran presisi
        udp_sock.sendto(data, addr)

def start_tcp_server():
    """TCP Server menggunakan Model Thread-per-Connection"""
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind((HOST, TCP_PORT))
    tcp_sock.listen(10)
    print(f"[*] TCP Web Server active on port {TCP_PORT}")

    while True:
        client_sock, addr = tcp_sock.accept()
        # Multithreading agar mendukung banyak client konkuren
        thread = threading.Thread(target=handle_tcp_client, args=(client_sock, addr))
        thread.start()

if __name__ == "__main__":
    # Menjalankan dual-protocol server (TCP & UDP)
    udp_thread = threading.Thread(target=start_udp_server, daemon=True)
    udp_thread.start()
    
    start_tcp_server()