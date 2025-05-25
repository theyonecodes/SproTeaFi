import unittest
from sproteafi_core import SproTeaFi
import os

class TestSproTeaFi(unittest.TestCase):
    def setUp(self):
        self.sproteafi = SproTeaFi(verbose=True)
        self.test_dir = os.path.expanduser("~/Music/SproTeaFi/test")
        os.makedirs(self.test_dir, exist_ok=True)

    def test_get_playlist_tracks(self):
        playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYQM9s"
        tracks = self.sproteafi.get_playlist_tracks(playlist_url)
        self.assertGreater(len(tracks), 0)
        self.assertIn("title", tracks[0])

    def test_process_track(self):
        track = {"title": "Test Song", "artist": "Test Artist", "album": "Test Album", "image": None}
        self.sproteafi.process_track(track, self.test_dir, "mp3", "artist")
        # Mock YouTube search and download for proper testing

if __name__ == "__main__":
    unittest.main()