import json
import re
import os

def update_versions():
    # 1. Baca version.json
    with open('version.json', 'r') as f:
        config = json.load(f)
    version = config['version']
    print(f"Versi target terdeteksi: {version}")

    # 2. Update vidstamp/__init__.py
    init_path = 'vidstamp/__init__.py'
    if os.path.exists(init_path):
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(f'# vidstamp package\n__version__ = "{version}"\n')
        print(f"Updated {init_path}")

    # 3. Update vidstamp/ui/launcher.py
    launcher_path = 'vidstamp/ui/launcher.py'
    if os.path.exists(launcher_path):
        with open(launcher_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ganti text="v1.3.0" atau versi lain
        new_content = re.sub(
            r'text="v[0-9\.]+"',
            f'text="v{version}"',
            content
        )
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {launcher_path}")

    # 4. Update vidstamp/ui/main_window.py
    main_window_path = 'vidstamp/ui/main_window.py'
    if os.path.exists(main_window_path):
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ganti title
        new_content = re.sub(
            r'self\.root\.title\("VidStamp( v[0-9\.]+)? - Video Timestamp & Scene Marker"\)',
            f'self.root.title("VidStamp v{version} - Video Timestamp & Scene Marker")',
            content
        )
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {main_window_path}")

    # 5. Update installer_windows.iss
    iss_path = 'installer_windows.iss'
    if os.path.exists(iss_path):
        with open(iss_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ganti AppVersion
        content = re.sub(
            r'AppVersion=[^\r\n]+',
            f'AppVersion={version}',
            content
        )
        # Ganti OutputBaseFilename
        content = re.sub(
            r'OutputBaseFilename=[^\r\n]+',
            f'OutputBaseFilename=VidStamp_Setup_v{version}',
            content
        )
        
        with open(iss_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {iss_path}")

if __name__ == '__main__':
    update_versions()
