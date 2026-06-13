import socket
import time
import statistics

# =====================================================================
# !!! SESUAIKAN IP LAPTOP A (SERVER/PROXY) DI SINI !!!
# =====================================================================
PROXY_IP = '127.0.0.1'
PROXY_PORT = 8080
SERVER_UDP_IP = '127.0.0.1'
SERVER_UDP_PORT = 9000
# =====================================================================

def mode_http():
    print("\n\033[95m--- MODE HTTP (TCP) ---\033[0m")
    file_tujuan = input("Masukkan file yang ingin dibuka (contoh: /index.html): ")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((PROXY_IP, PROXY_PORT))
        
        request = f"GET {file_tujuan} HTTP/1.1\r\nHost: {PROXY_IP}\r\n\r\n"
        sock.sendall(request.encode())
        
        respon = sock.recv(4096).decode(errors='ignore')
        print("\n[ISI RESPON]:")
        print("-" * 30)
        print(respon[:500] + "...") # Menampilkan 500 karakter pertama
        print("-" * 30)
        sock.close()
    except Exception as e:
        print(f"Gagal koneksi: {e}")

def mode_qos_ping():
    print("\n\033[95m--- MODE QoS PING (UDP) ---\033[0m")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0) # Batas timeout 1 detik sesuai ketentuan
    
    rtt_list = []
    lost = 0
    jumlah_ping = 10 # Minimal 10 paket sesuai ketentuan
    total_bytes_received = 0

    # Catat waktu awal seluruh rangkaian pengujian untuk menghitung throughput
    waktu_mulai_test = time.time()

    for i in range(1, jumlah_ping + 1):
        mulai_paket = time.time()
        pesan = f"Ping {i} {mulai_paket}".encode() # Format payload sesuai ketentuan
        
        try:
            sock.sendto(pesan, (SERVER_UDP_IP, SERVER_UDP_PORT))
            data, addr = sock.recvfrom(1024)
            selesai_paket = time.time()
            
            # Hitung ukuran data yang diterima (dalam Bytes)
            total_bytes_received += len(data)
            
            rtt = (selesai_paket - mulai_paket) * 1000
            rtt_list.append(rtt)
            print(f"Respon dari {addr}: seq={i} waktu={rtt:.2f}ms | ukuran={len(data)} bytes")
        except socket.timeout:
            lost += 1
            print(f"Request seq={i}: Timed Out")
        
        time.sleep(0.1) # Jeda antar-paket

    waktu_selesai_test = time.time()
    durasi_total_detik = waktu_selesai_test - waktu_mulai_test

    # --- HITUNG STATISTIK QOS (LENGKAP 4 PARAMETER) ---
    if rtt_list:
        packet_loss_persen = (lost / jumlah_ping) * 100
        rtt_min = min(rtt_list)
        rtt_max = max(rtt_list)
        rtt_avg = sum(rtt_list) / len(rtt_list)
        
        # Jitter: Variasi selisih delay antar-paket berturut-turut
        if len(rtt_list) > 1:
            jitter = statistics.stdev(rtt_list)
        else:
            jitter = 0.0

        # Throughput (kbps): (Total Bytes * 8) / (Total Durasi Detik * 1000)
        throughput_kbps = (total_bytes_received * 8) / (durasi_total_detik * 1000)

        print("\n\033[92m=====================================")
        print("          HASIL ANALISIS QoS         ")
        print("=====================================\033[0m")
        print(f"1. Paket       : Terkirim = {jumlah_ping}, Hilang = {lost}")
        print(f"   Packet Loss : {packet_loss_persen:.2f}%")
        print(f"2. Latency/RTT : Min = {rtt_min:.2f}ms")
        print(f"                 Max = {rtt_max:.2f}ms")
        print(f"                 Rata-rata = {rtt_avg:.2f}ms")
        print(f"3. Jitter      : {jitter:.2f}ms")
        print(f"4. Throughput  : {throughput_kbps:.4f} kbps")
        print("\033[92m=====================================\033[0m")
    else:
        print("\n\033[91m[QoS ERROR] Semua paket hilang (100% Packet Loss). Tidak dapat menghitung RTT, Jitter, dan Throughput.\033[0m")
        
    sock.close()

if __name__ == "__main__":
    while True:
        print("\nMENU CLIENT:")
        print("1. Ambil File Web (HTTP)")
        print("2. Uji Kinerja Jaringan (QoS)")
        print("3. Keluar")
        pilih = input("Pilih (1/2/3): ")
        
        if pilih == '1': mode_http()
        elif pilih == '2': mode_qos_ping()
        elif pilih == '3': break
        else: print("Pilihan salah!")