import socket
import threading
import os
import time  # <-- Modul ini wajib ditambahkan agar fungsi perhitungan waktu berjalan!

# --- KONFIGURASI ---
PROXY_HOST = '0.0.0.0'
PROXY_PORT = 8080
SERVER_HOST = '127.0.0.1'  # Alamat Web Server
SERVER_PORT = 8000
CACHE_DIR = "cache"
STATUS_DIR = "status"

# Buat folder cache jika belum ada
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def kirim_halaman_status(client_socket, status_code, status_msg):
    """Mengirim halaman error (502/504) dari folder status"""
    path_error = os.path.join(STATUS_DIR, f"{status_code}.html")
    if os.path.isfile(path_error):
        with open(path_error, 'rb') as f:
            konten = f.read()
    else:
        konten = f"<h1>{status_code} {status_msg}</h1>".encode()
    
    header = f"HTTP/1.1 {status_code} {status_msg}\r\nContent-Type: text/html\r\n\r\n"
    client_socket.sendall(header.encode() + konten)

def tangani_koneksi(client_sock, addr):
    # Catat waktu awal request masuk ke proxy
    waktu_mulai = time.time()
    
    try:
        request = client_sock.recv(4096).decode(errors='ignore')
        if not request: return

        baris_pertama = request.split('\n')[0]
        url = baris_pertama.split()[1]
        
        nama_cache = url.replace("/", "_").lstrip("_") or "index.html"
        path_cache = os.path.join(CACHE_DIR, nama_cache)

        # --- CEK CACHE ---
        if os.path.isfile(path_cache):
            with open(path_cache, 'rb') as f:
                client_sock.sendall(f.read())
            # Hitung selisih waktu respons
            waktu_respon = (time.time() - waktu_mulai) * 1000
            print(f"\033[94m[PROXY] CACHE HIT | Client: {addr[0]} | URL: {url} | Waktu Respons: {waktu_respon:.2f}ms\033[0m")
        else:
            # Hubungkan ke Web Server
            try:
                server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_sock.settimeout(5.0)
                server_sock.connect((SERVER_HOST, SERVER_PORT))
                server_sock.sendall(request.encode())

                respon_full = b""
                while True:
                    data = server_sock.recv(4096)
                    if not data: break
                    respon_full += data
                
                if b"200 OK" in respon_full:
                    with open(path_cache, 'wb') as f:
                        f.write(respon_full)
                
                client_sock.sendall(respon_full)
                server_sock.close()
                
                # Hitung selisih waktu respons
                waktu_respon = (time.time() - waktu_mulai) * 1000
                print(f"\033[93m[PROXY] CACHE MISS | Client: {addr[0]} | URL: {url} | Waktu Respons: {waktu_respon:.2f}ms\033[0m")

            except socket.timeout:
                kirim_halaman_status(client_sock, 504, "Gateway Timeout")
            except:
                kirim_halaman_status(client_sock, 502, "Bad Gateway")

    except Exception as e:
        print(f"\033[91m[ERROR] {e}\033[0m")
    finally:
        client_sock.close()

# --- JALANKAN PROXY ---
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy_socket.bind((PROXY_HOST, PROXY_PORT))
proxy_socket.listen(10) # Mendukung konkurensi

print(f"\033[96m[*] Proxy Server aktif di port {PROXY_PORT}\033[0m")
while True:
    c_sock, c_addr = proxy_socket.accept()
    threading.Thread(target=tangani_koneksi, args=(c_sock, c_addr)).start()