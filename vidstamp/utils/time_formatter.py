"""
vidstamp/utils/time_formatter.py - Helper formatting waktu
"""

def format_time(sec, ms=True):
    """
    Mengubah durasi detik float ke string format MM:SS.mmm atau MM:SS
    """
    if sec is None:
        return "--:--"
    s = int(sec)
    mi = s // 60
    s = s % 60
    if ms:
        msec = int(round((sec - int(sec)) * 1000))
        # Jika round membulatkan ke 1000, sesuaikan detik
        if msec == 1000:
            msec = 0
            s += 1
            if s == 60:
                s = 0
                mi += 1
        return f"{mi:02d}:{s:02d}.{msec:03d}"
    return f"{mi:02d}:{s:02d}"
