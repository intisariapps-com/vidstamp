"""
vidstamp/core/player.py - Mesin pemutar video & audio (OpenCV + ffpyplayer)
"""
import cv2
from ffpyplayer.player import MediaPlayer

class VideoPlayerEngine:
    def __init__(self):
        self.cap = None
        self.audio_player = None
        self.fps = 30.0
        self.total_frames = 0
        self.width = 0
        self.height = 0
        self.video_path = ""
        
        # State
        self.playing = False
        self.cur_idx = 0
        self.speed = 1.0
        self._seek_target = None

    def load(self, path):
        """Memuat berkas video dan mempersiapkan audio player MediaPlayer."""
        self.release()
        
        self.video_path = path
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            return False
            
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Inisialisasi audio player (vn=True mematikan video rendering di ffpyplayer)
        try:
            self.audio_player = MediaPlayer(path, ff_opts={'vn': True})
            self.audio_player.set_pause(True)
        except Exception:
            self.audio_player = None
            
        self.cur_idx = 0
        self.playing = False
        self._seek_target = None
        return True

    def set_playing(self, state: bool):
        """Play / Pause pemutaran video dan audio secara sinkron."""
        if not self.cap:
            return
        self.playing = state
        if self.audio_player:
            self.audio_player.set_pause(not state)

    def set_speed(self, val: float):
        """Mengubah kecepatan video."""
        self.speed = val

    def seek_to(self, frame_idx: int):
        """Lompat (seek) ke frame tertentu secara instan."""
        if not self.cap:
            return
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        self.cur_idx = frame_idx
        
        # Cari detik tujuan seek
        sec = frame_idx / self.fps
        if self.audio_player:
            self.audio_player.seek(sec, relative=False)
            
        if self.playing:
            self._seek_target = frame_idx
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

    def get_next_frame(self):
        """
        Mengambil frame berikutnya dari OpenCV dan menyinkronkan posisinya
        berdasarkan waktu (PTS) audio dari MediaPlayer.
        """
        if not self.cap:
            return False, None

        # Jika ada antrean seek target
        if self._seek_target is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self._seek_target)
            self._seek_target = None

        # Jika sedang memutar, sinkronkan video ke audio PTS
        if self.playing and self.audio_player:
            pts = self.audio_player.get_pts()
            if pts > 0:
                target_frame = int(pts * self.fps)
                # Hanya lakukan seek (set frame) jika desync lebih dari 6 frame (~200ms)
                if abs(self.cur_idx - target_frame) >= 6:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    self.cur_idx = target_frame

        ret, frame = self.cap.read()
        if ret:
            self.cur_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            
        return ret, frame

    def read_single_frame(self, frame_idx: int):
        """Membaca satu frame spesifik tanpa mengubah posisi playback."""
        if not self.cap:
            return None
        prev_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, prev_pos)
        if ret:
            return frame
        return None

    def release(self):
        """Menutup stream video & audio player."""
        self.playing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.audio_player:
            self.audio_player.close_player()
            self.audio_player = None
        self.cur_idx = 0
        self._seek_target = None
