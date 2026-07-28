"""
vidstamp/core/mpc_client.py - Modul Klien Web API MPC-HC (HTTP Interface) menggunakan urllib bawaan
"""
import urllib.request
import urllib.parse
import re

class MPCClient:
    def __init__(self, host="localhost", port=13579):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def get_variables(self):
        """
        Mengambil status variabel player aktif dari MPC-HC via GET /variables.html.
        Mengembalikan dictionary berisi state pemutaran.
        """
        url = f"{self.base_url}/variables.html"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'VidStamp-Companion'})
            # Gunakan timeout rendah agar tidak memblokir event loop GUI utama
            with urllib.request.urlopen(req, timeout=0.2) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                def extract(tag):
                    m = re.search(fr'<p id="{tag}">(.*?)</p>', html, re.DOTALL)
                    return m.group(1).strip() if m else ""
                
                state = extract("state")
                position_ms = extract("position")
                duration_ms = extract("duration")
                filepath = extract("filepath")
                filepath_short = extract("filepathshort")
                
                # State MPC-HC: 0=Stopped, 1=Paused, 2=Playing, -1=Closed
                return {
                    "active": True,
                    "state": int(state) if state.isdigit() or (state.startswith('-') and state[1:].isdigit()) else -1,
                    "position_sec": float(position_ms) / 1000.0 if position_ms.isdigit() else 0.0,
                    "duration_sec": float(duration_ms) / 1000.0 if duration_ms.isdigit() else 0.0,
                    "filepath": filepath,
                    "filename": filepath_short
                }
        except Exception as err:
            return {
                "active": False,
                "error": str(err),
                "state": -1,
                "position_sec": 0.0,
                "duration_sec": 0.0,
                "filepath": "",
                "filename": ""
            }

    def send_command(self, wm_command, position_str=None):
        """
        Mengirimkan perintah ke MPC-HC via POST /command.html.
        """
        url = f"{self.base_url}/command.html"
        data = {"wm_command": str(wm_command)}
        if position_str is not None:
            data["position"] = str(position_str)
            
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=encoded_data, headers={'User-Agent': 'VidStamp-Companion'})
            with urllib.request.urlopen(req, timeout=0.2) as response:
                # Perintah sukses dikirim
                return True
        except Exception:
            return False

    def toggle_play(self):
        # Play/Pause toggle
        return self.send_command(889)

    def play(self):
        return self.send_command(887)

    def pause(self):
        return self.send_command(888)

    def seek_to_seconds(self, seconds):
        """
        Melakukan seek ke posisi detik tertentu.
        MPC-HC menerima parameter position dalam format milidetik jika integer, atau format HH:MM:SS.
        """
        # Gunakan format milidetik integer langsung
        ms = int(seconds * 1000)
        return self.send_command(-1, position_str=str(ms))

    def step_forward(self):
        # Maju 1 frame
        return self.send_command(904)

    def step_backward(self):
        # Mundur 1 frame
        return self.send_command(903)

    def jump_forward(self, seconds=5):
        if seconds == 10:
            return self.send_command(900) # Maju 10 detik
        return self.send_command(902) # Maju 5 detik (default)

    def jump_backward(self, seconds=5):
        if seconds == 10:
            return self.send_command(899) # Mundur 10 detik
        return self.send_command(901) # Mundur 5 detik (default)
