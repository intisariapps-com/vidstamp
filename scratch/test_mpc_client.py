"""
scratch/test_mpc_client.py - Unit Test Mocking untuk MPC-HC Client
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidstamp.core.mpc_client import MPCClient

class TestMPCClient(unittest.TestCase):
    def setUp(self):
        self.client = MPCClient("localhost", 13579)

    @patch("urllib.request.urlopen")
    def test_get_variables_playing(self, mock_urlopen):
        # Mocking respon HTML variables.html dari MPC-HC
        html_response = """
        <html>
        <p id="state">2</p>
        <p id="position">45000</p>
        <p id="duration">1200000</p>
        <p id="filepath">E:\\ANIME\\Sword Art Online\\SAO_03.mkv</p>
        <p id="filepathshort">SAO_03.mkv</p>
        </html>
        """
        mock_res = MagicMock()
        mock_res.read.return_value = html_response.encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_res
        
        status = self.client.get_variables()
        
        self.assertTrue(status["active"])
        self.assertEqual(status["state"], 2) # Playing
        self.assertEqual(status["position_sec"], 45.0)
        self.assertEqual(status["duration_sec"], 1200.0)
        self.assertEqual(status["filename"], "SAO_03.mkv")

    @patch("urllib.request.urlopen")
    def test_send_command(self, mock_urlopen):
        mock_res = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_res
        
        success = self.client.toggle_play()
        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()
