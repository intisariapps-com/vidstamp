"""
build.py - Skrip otomatisasi kompilasi lokal VidStamp untuk Windows.
Mengotomatiskan langkah:
1. Sinkronisasi Versi (update_version.py)
2. Pengetesan Unit (pytest)
3. Kompilasi Executable (pyinstaller)
4. Pembuatan Setup Installer (Inno Setup / ISCC.exe)
"""
import os
import sys
import shutil
import subprocess
import json

def print_step(msg):
    print("\n" + "=" * 60)
    print(f"--> {msg}")
    print("=" * 60)

def run_command(cmd, shell=False):
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
    print(f"Menjalankan: {cmd_str}")
    res = subprocess.run(cmd, shell=shell)
    if res.returncode != 0:
        print(f"\n[-] ERROR: Perintah gagal dengan exit code {res.returncode}\n")
        sys.exit(res.returncode)
    return res

def main():
    # 1. Update Versi
    print_step("1. Menyinkronkan versi dari version.json ke seluruh berkas...")
    run_command([sys.executable, "update_version.py"])

    # Ambil versi target untuk informasi di akhir
    version = "unknown"
    if os.path.exists("version.json"):
        try:
            with open("version.json", "r") as f:
                version = json.load(f).get("version", "unknown")
        except Exception as e:
            print(f"[!] Gagal membaca version.json: {e}")

    # Resolusi path binari di .venv jika ada
    venv_dir = os.path.join(".", ".venv")
    is_windows = os.name == "nt"
    
    if is_windows:
        pytest_exe = os.path.join(venv_dir, "Scripts", "pytest.exe")
        pyinstaller_exe = os.path.join(venv_dir, "Scripts", "pyinstaller.exe")
    else:
        pytest_exe = os.path.join(venv_dir, "bin", "pytest")
        pyinstaller_exe = os.path.join(venv_dir, "bin", "pyinstaller")

    # Fallback jika tidak ada di .venv
    if not os.path.exists(pytest_exe):
        pytest_exe = shutil.which("pytest") or "pytest"
    if not os.path.exists(pyinstaller_exe):
        pyinstaller_exe = shutil.which("pyinstaller") or "pyinstaller"

    # 2. Jalankan Unit Test (Fail-Fast Gatekeeper)
    print_step("2. Menjalankan Unit Test (Pytest)...")
    run_command([pytest_exe])

    # 3. Jalankan PyInstaller
    print_step("3. Mengompilasi aplikasi dengan PyInstaller...")
    run_command([pyinstaller_exe, "--clean", "-y", "vidstamp.spec"])

    # 4. Bangun Setup Installer menggunakan Inno Setup
    if is_windows:
        print_step("4. Membangun Setup Installer dengan Inno Setup...")
        iscc_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            "ISCC.exe"
        ]
        
        iscc_found = None
        for path in iscc_paths:
            if os.path.exists(path):
                iscc_found = path
                break
        
        if not iscc_found:
            # Cari di PATH
            iscc_found = shutil.which("ISCC.exe") or shutil.which("ISCC")

        if not iscc_found:
            print("\n[-] WARNING: Inno Setup Compiler (ISCC.exe) tidak ditemukan.")
            print("Silakan unduh & instal Inno Setup 6 di folder default, atau tambahkan jalurnya ke PATH sistem.")
            print("[!] Hasil kompilasi PyInstaller sukses di folder 'dist/VidStamp/', namun Installer Setup tidak dibuat.\n")
            sys.exit(1)

        print(f"Inno Setup Compiler ditemukan: {iscc_found}")
        run_command([iscc_found, "installer_windows.iss"])

        # 5. Selesai & Laporan
        print_step("BUILD SELESAI DENGAN SUKSES!")
        setup_file = f"VidStamp_Setup_v{version}.exe"
        if os.path.exists(setup_file):
            size_mb = os.path.getsize(setup_file) / (1024 * 1024)
            print(f"[+] Installer siap digunakan: {setup_file} ({size_mb:.2f} MB)")
        else:
            print("[+] Proses kompilasi installer selesai (silakan periksa folder utama).")
    else:
        print_step("BUILD SELESAI (Bukan Windows)!")
        print("[*] Kompilasi executable sukses. Lewati langkah pembuatan setup installer Windows karena Anda tidak berada di Windows.")

if __name__ == "__main__":
    main()
