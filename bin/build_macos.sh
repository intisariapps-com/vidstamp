#!/bin/bash
# ==============================================================================
# build_macos.sh - Skrip Otomatisasi Bundling Aplikasi VidStamp untuk macOS
# ==============================================================================
# Skrip ini mengotomatisasi pengunduhan FFmpeg macOS, pembuatan ikon .icns,
# kompilasi PyInstaller (.app), dan pembuatan installer disk image (.dmg).
# ==============================================================================

# Hentikan eksekusi jika terjadi kesalahan
set -e

# Warna output terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Memulai Proses Bundling VidStamp untuk macOS ===${NC}"

# 1. Pastikan kita berada di direktori root proyek
cd "$(dirname "$0")/.."
echo -e "Direktori kerja: ${GREEN}$(pwd)${NC}"

# 2. Setup folder bin/mac/
mkdir -p bin/mac

# 3. Unduh FFmpeg & FFprobe macOS statis jika belum ada
echo -e "${BLUE}1. Memeriksa dependensi biner FFmpeg & FFprobe macOS...${NC}"
FFBINARIES_URL="https://ffbinaries.com/api/v1/version/latest"

if [ ! -f "bin/mac/ffmpeg" ]; then
    echo -e "${YELLOW}ffmpeg tidak ditemukan di bin/mac/. Mengunduh dari ffbinaries...${NC}"
    curl -L -o bin/mac/ffmpeg.zip https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v4.4.1/ffmpeg-4.4.1-osx-64.zip
    unzip -o bin/mac/ffmpeg.zip -d bin/mac/
    rm bin/mac/ffmpeg.zip
    chmod +x bin/mac/ffmpeg
    echo -e "${GREEN}ffmpeg macOS berhasil diunduh dan dipasang.${NC}"
else
    echo -e "${GREEN}ffmpeg macOS sudah tersedia.${NC}"
fi

if [ ! -f "bin/mac/ffprobe" ]; then
    echo -e "${YELLOW}ffprobe tidak ditemukan di bin/mac/. Mengunduh dari ffbinaries...${NC}"
    curl -L -o bin/mac/ffprobe.zip https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v4.4.1/ffprobe-4.4.1-osx-64.zip
    unzip -o bin/mac/ffprobe.zip -d bin/mac/
    rm bin/mac/ffprobe.zip
    chmod +x bin/mac/ffprobe
    echo -e "${GREEN}ffprobe macOS berhasil diunduh dan dipasang.${NC}"
else
    echo -e "${GREEN}ffprobe macOS sudah tersedia.${NC}"
fi

# 4. Membuat file icon.icns secara dinamis dari icon.png
echo -e "${BLUE}2. Membuat berkas ikon macOS (.icns) dari PNG...${NC}"
PNG_ICON="vidstamp/ui/assets/icon.png"
ICNS_ICON="vidstamp/ui/assets/icon.icns"

if [ -f "$PNG_ICON" ]; then
    # Buat direktori iconset sementara
    mkdir -p VidStamp.iconset
    
    # Render berbagai ukuran ikon untuk resolusi normal dan retina
    sips -z 16 16     "$PNG_ICON" --out VidStamp.iconset/icon_16x16.png &>/dev/null
    sips -z 32 32     "$PNG_ICON" --out VidStamp.iconset/icon_16x16@2x.png &>/dev/null
    sips -z 32 32     "$PNG_ICON" --out VidStamp.iconset/icon_32x32.png &>/dev/null
    sips -z 64 64     "$PNG_ICON" --out VidStamp.iconset/icon_32x32@2x.png &>/dev/null
    sips -z 128 128   "$PNG_ICON" --out VidStamp.iconset/icon_128x128.png &>/dev/null
    sips -z 256 256   "$PNG_ICON" --out VidStamp.iconset/icon_128x128@2x.png &>/dev/null
    sips -z 256 256   "$PNG_ICON" --out VidStamp.iconset/icon_256x256.png &>/dev/null
    sips -z 512 512   "$PNG_ICON" --out VidStamp.iconset/icon_256x256@2x.png &>/dev/null
    sips -z 512 512   "$PNG_ICON" --out VidStamp.iconset/icon_512x512.png &>/dev/null
    sips -z 1024 1024 "$PNG_ICON" --out VidStamp.iconset/icon_512x512@2x.png &>/dev/null
    
    # Kompilasi menjadi file .icns menggunakan iconutil bawaan macOS
    iconutil -c icns VidStamp.iconset
    mv VidStamp.icns "$ICNS_ICON"
    rm -rf VidStamp.iconset
    echo -e "${GREEN}Berkas ikon macOS (.icns) berhasil dibuat di $ICNS_ICON.${NC}"
else
    echo -e "${RED}Peringatan: $PNG_ICON tidak ditemukan. Ikon default akan digunakan.${NC}"
fi

# 5. Instalasi dependensi Python & PyInstaller
echo -e "${BLUE}3. Memasang dependensi Python...${NC}"
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    python3 -m venv .venv
    source .venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 6. Jalankan PyInstaller
echo -e "${BLUE}4. Menjalankan PyInstaller untuk kompilasi .app...${NC}"
pyinstaller --clean -y vidstamp.spec

if [ -d "dist/VidStamp.app" ]; then
    echo -e "${GREEN}Kompilasi VidStamp.app berhasil diselesaikan.${NC}"
else
    echo -e "${RED}Kesalahan: dist/VidStamp.app tidak berhasil terbentuk.${NC}"
    exit 1
fi

# 7. Membuat berkas Disk Image (.dmg) menggunakan create-dmg
echo -e "${BLUE}5. Membuat berkas installer Disk Image (.dmg)...${NC}"

# Pastikan create-dmg terinstal
if ! command -v create-dmg &> /dev/null; then
    echo -e "${YELLOW}create-dmg tidak ditemukan. Mencoba memasang lewat Homebrew...${NC}"
    if command -v brew &> /dev/null; then
        brew install create-dmg
    else
        echo -e "${RED}Homebrew tidak terdeteksi. Silakan instal 'create-dmg' secara manual untuk melanjutkan pembuatan .dmg.${NC}"
        echo -e "${YELLOW}Aplikasi .app mentah tersedia di dist/VidStamp.app.${NC}"
        exit 0
    fi
fi

# Hapus installer .dmg lama jika ada
rm -f dist/VidStamp_Setup.dmg

# Jalankan perintah create-dmg untuk membungkus .app menjadi .dmg
create-dmg \
  --volname "VidStamp Installer" \
  --volicon "$ICNS_ICON" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "VidStamp.app" 200 190 \
  --hide-extension "VidStamp.app" \
  --app-drop-link 600 190 \
  "dist/VidStamp_Setup.dmg" \
  "dist/VidStamp.app"

echo -e "${GREEN}=== Selesai! Berkas installer macOS berhasil dibuat di dist/VidStamp_Setup.dmg ===${NC}"
