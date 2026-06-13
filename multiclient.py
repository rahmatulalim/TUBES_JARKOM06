import subprocess
import time

def jalankan_multi_client():
    processes = []
    jumlah_client = 5
    
    print(f"[*] Memulai pengujian konkuren dengan {jumlah_client} client...")
    
    # 1. Spawning/membuat 5 proses client.py secara bersamaan
    for i in range(jumlah_client):
        p = subprocess.Popen(
            ['python', 'client.py'], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(p)
        print(f" -> Client {i+1} berhasil dibuat (PID: {p.pid})")

    # Jeda mikro agar semua proses siap
    time.sleep(0.5)

    print("\n[*] Mengirimkan perintah otomatis ke seluruh client...")
    # 2. Memberikan input otomatis ke menu client.py
    # Mengirim '1' (Menu HTTP), lalu '/index.html' (Nama file), lalu '3' (Keluar dari loop)
    input_otomatis = "1\n/index.html\n3\n"
    
    for idx, p in enumerate(processes):
        try:
            # communicate() akan mengirim input dan langsung membaca output secara paralel
            stdout, stderr = p.communicate(input=input_otomatis, timeout=5)
            print(f"\n================ OUTPUT CLIENT {idx+1} ================")
            # Menampilkan 200 karakter pertama dari output client untuk verifikasi
            print(stdout[:250] + "\n...[Output Dipotong]...")
        except subprocess.TimeoutExpired:
            print(f"[!] Client {idx+1} mengalami Timeout!")
            p.kill()

if __name__ == "__main__":
    jalankan_multi_client()