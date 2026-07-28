# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import ffpyplayer
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Dapatkan lokasi absolut library ffpyplayer untuk menyalin DLL pendukungnya secara manual
ffpyplayer_path = os.path.dirname(ffpyplayer.__file__)

# Tentukan file biner FFmpeg & FFprobe yang akan disertakan berdasarkan platform target
binaries = []
if sys.platform.startswith('win'):
    if os.path.exists('bin/win/ffmpeg.exe'):
        binaries.append(('bin/win/ffmpeg.exe', 'bin'))
    if os.path.exists('bin/win/ffprobe.exe'):
        binaries.append(('bin/win/ffprobe.exe', 'bin'))
elif sys.platform.startswith('darwin'):
    if os.path.exists('bin/mac/ffmpeg'):
        binaries.append(('bin/mac/ffmpeg', 'bin'))
    if os.path.exists('bin/mac/ffprobe'):
        binaries.append(('bin/mac/ffprobe', 'bin'))

# Tambahkan seluruh direktori ffpyplayer sebagai data tambahan agar DLL SDL2/FFmpeg termuat dengan benar
datas = [
    (ffpyplayer_path, 'ffpyplayer'),
]

a = Analysis(
    ['vidstamp/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=collect_submodules('ffpyplayer') + ['cv2', 'PIL', 'PIL.ImageTk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VidStamp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set to False untuk UI desktop produksi, set True jika butuh debugging console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='vidstamp/ui/assets/icon.ico' if os.path.exists('vidstamp/ui/assets/icon.ico') else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VidStamp',
)

if sys.platform.startswith('darwin'):
    app = BUNDLE(
        coll,
        name='VidStamp.app',
        icon='vidstamp/ui/assets/icon.icns' if os.path.exists('vidstamp/ui/assets/icon.icns') else None,
        bundle_identifier='com.intisariapps.vidstamp',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Video File',
                    'CFBundleTypeRole': 'Viewer',
                    'LSHandlerRank': 'Alternate',
                    'LSItemContentTypes': [
                        'public.movie',
                        'public.video',
                        'com.apple.quicktime-movie',
                        'public.avi',
                        'public.mpeg-4'
                    ]
                }
            ]
        }
    )
