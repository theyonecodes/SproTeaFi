import unittest
from unittest.mock import patch
from io import StringIO
from sproteafi_cli import main

class TestSproTeaFiCLI(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    @patch("sproteafi_core.SproTeaFi")
    def test_cli_help(self, mock_core, mock_stdout):
        with self.assertRaises(SystemExit):
            sys.argv = ["sproteafi_cli.py", "--help"]
            main()
        self.assertIn("Spotify Playlist Downloader", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sproteafi_core.SproTeaFi")
    @patch("rich.prompt.Prompt.ask")
    def test_interactive_url(self, mock_prompt, mock_core, mock_stdout):
        mock_prompt.return_value = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYQM9s"
        sys.argv = ["sproteafi_cli.py"]
        main()
        self.assertIn("Processing playlist", mock_stdout.getvalue())

if __name__ == "__main__":
    unittest.main()