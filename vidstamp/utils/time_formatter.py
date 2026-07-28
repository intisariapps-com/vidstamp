"""
vidstamp/utils/time_formatter.py - Helper formatting waktu
"""

def format_time(sec, ms=False):
    """
    Mengubah durasi detik float ke string format HH:MM:SS (waktu berjalan).
    Parameter 'ms' diabaikan namun tetap ada untuk kompatibilitas pemanggilan lama.
    """
    if sec is None:
        return "--:--:--"
    sec = max(0, float(sec))
    total_sec = int(sec)
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_remaining(current_sec, total_sec):
    """
    Mengubah sisa waktu ke string format -HH:MM:SS (hitung mundur).
    """
    if current_sec is None or total_sec is None or total_sec <= 0:
        return "-00:00:00"
    remaining = max(0, float(total_sec) - float(current_sec))
    total = int(remaining)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"-{h:02d}:{m:02d}:{s:02d}"
