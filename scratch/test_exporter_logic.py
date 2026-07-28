import os
import sys
import unittest

# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidstamp.core.exporter import (
    srt_time_to_seconds,
    seconds_to_srt_time,
    merge_duplicate_ocr_subtitles,
    cut_and_shift_srt,
    clean_srt_text
)

class TestExporterSubtitles(unittest.TestCase):
    def test_time_conversions(self):
        # Test srt_time_to_seconds
        self.assertAlmostEqual(srt_time_to_seconds("00:00:01,500"), 1.5)
        self.assertAlmostEqual(srt_time_to_seconds("01:02:03,004"), 3723.004)
        
        # Test seconds_to_srt_time
        self.assertEqual(seconds_to_srt_time(1.5), "00:00:01,500")
        self.assertEqual(seconds_to_srt_time(3723.004), "01:02:03,004")

    def test_clean_srt_text(self):
        self.assertEqual(clean_srt_text("<i>Halo</i>"), "Halo")
        self.assertEqual(clean_srt_text("{\\an8}Teks ASS"), "Teks ASS")
        self.assertEqual(clean_srt_text("  Baris 1 \n  Baris 2  "), "Baris 1\nBaris 2")

    def test_merge_duplicate_ocr_subtitles(self):
        subs = [
            {'start': 1.0, 'end': 2.0, 'text': 'Halo dunia'},
            {'start': 2.1, 'end': 3.5, 'text': 'Halo dunia'}, # Duplikat, gap 0.1s
            {'start': 4.0, 'end': 5.0, 'text': 'Teks lain'},
            {'start': 5.5, 'end': 6.0, 'text': 'Halo dunia'}, # Teks sama tapi gap 0.5s
            {'start': 9.0, 'end': 10.0, 'text': 'Halo dunia'}, # Teks sama tapi gap 3.0s (> 2.5s)
        ]
        merged = merge_duplicate_ocr_subtitles(subs)
        
        # Harus digabungkan menjadi:
        # 1. Halo dunia (1.0 -> 3.5)
        # 2. Teks lain (4.0 -> 5.0)
        # 3. Halo dunia (5.5 -> 6.0)
        # 4. Halo dunia (9.0 -> 10.0)
        self.assertEqual(len(merged), 4)
        self.assertEqual(merged[0]['start'], 1.0)
        self.assertEqual(merged[0]['end'], 3.5)
        self.assertEqual(merged[1]['text'], 'Teks lain')
        self.assertEqual(merged[2]['start'], 5.5)
        self.assertEqual(merged[2]['end'], 6.0)
        self.assertEqual(merged[3]['start'], 9.0)
        self.assertEqual(merged[3]['end'], 10.0)

    def test_cut_and_shift_srt(self):
        # Buat srt tiruan
        input_srt = "temp_test_input.srt"
        output_srt = "temp_test_output.srt"
        
        srt_content = """1
00:00:01,000 --> 00:00:03,000
<i>Halo Dunia</i>

2
00:00:04,500 --> 00:00:06,000
Lagu Pembuka Anime

3
00:00:07,000 --> 00:00:09,000
{\\an8}Cerita berlanjut

4
00:00:09,200 --> 00:00:10,500
Cerita berlanjut
"""
        with open(input_srt, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        # Kita skip OP dari detik 4.0 hingga 7.0.
        # keep_ranges: [(0.0, 4.0), (7.0, 15.0)]
        keep_ranges = [(0.0, 4.0), (7.0, 15.0)]
        
        success = cut_and_shift_srt(input_srt, keep_ranges, output_srt)
        self.assertTrue(success)
        
        # Baca output srt
        with open(output_srt, 'r', encoding='utf-8') as f:
            out_content = f.read()
            
        # Bersihkan file temp
        if os.path.exists(input_srt): os.remove(input_srt)
        if os.path.exists(output_srt): os.remove(output_srt)
        
        self.assertIn("00:00:01,000 --> 00:00:03,000", out_content)
        self.assertIn("Halo Dunia", out_content)
        self.assertIn("00:00:04,000 --> 00:00:07,500", out_content)
        self.assertIn("Cerita berlanjut", out_content)
        self.assertNotIn("Lagu Pembuka Anime", out_content)

if __name__ == '__main__':
    unittest.main()
