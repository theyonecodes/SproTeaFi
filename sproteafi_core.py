import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import ffmpeg
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import os
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
LOG_DIR = os.path.expanduser("~/sproteafi_logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "sproteafi.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = Console()

# Cache directory
CACHE_DIR = os.path.expanduser("~/.sproteafi_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class SproTeaFi:
    def __init__(self, client_id=None, client_secret=None, verbose=False):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=client_id or os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        ))
        self.verbose = verbose
        self.cache_file = os.path.join(CACHE_DIR, "search_cache.json")
        self.search_cache = self.load_cache()

    # Rest of the file remains unchanged (as provided previously)
    def load_cache(self):
        """Load YouTube search cache."""
        try:
            with open(self.cache_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self):
        """Save YouTube search cache."""
        with open(self.cache_file, "w") as f:
            json.dump(self.search_cache, f)

    def get_playlist_tracks(self, playlist_url):
        """Fetch tracks from Spotify playlist URL."""
        try:
            playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
            results = self.sp.playlist_items(playlist_id)
            tracks = []
            for item in results["items"]:
                track = item["track"]
                tracks.append({
                    "title": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                })
            logging.info(f"Fetched {len(tracks)} tracks from playlist {playlist_id}")
            return tracks
        except Exception as e:
            logging.error(f"Failed to fetch playlist: {e}")
            raise ValueError(f"Invalid playlist URL or API error: {e}")

    def search_youtube(self, track):
        """Search YouTube for best audio match."""
        query = f"{track['artist']} {track['title']} audio"
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.search_cache:
            logging.info(f"Cache hit for {query}")
            return self.search_cache[cache_key]

        ydl_opts = {
            "quiet": not self.verbose,
            "format": "bestaudio/best",
            "noplaylist": True,
            "extract_flat": True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch:{query}", download=False)
                url = result["entries"][0]["url"]
                self.search_cache[cache_key] = url
                self.save_cache()
                logging.info(f"Found YouTube URL for {query}: {url}")
                return url
        except Exception as e:
            logging.error(f"YouTube search failed for {query}: {e}")
            return None

    def download_track(self, url, output_path):
        """Download audio from YouTube URL."""
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path + ".%(ext)s",
            "quiet": not self.verbose,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logging.info(f"Downloaded track to {output_path}.mp3")
            return f"{output_path}.mp3"
        except Exception as e:
            logging.error(f"Download failed for {url}: {e}")
            return None

    def normalize_audio(self, input_file, output_file, format="mp3"):
        """Normalize audio to -14 LUFS."""
        try:
            stream = ffmpeg.input(input_file)
            stream = ffmpeg.filter(stream, "loudnorm", I=-14, TP=-1.5, LRA=11)
            stream = ffmpeg.output(stream, output_file, format=format, **{"ar": 44100, "ac": 2})
            ffmpeg.run(stream, overwrite_output=True, quiet=not self.verbose)
            logging.info(f"Normalized audio to {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"Normalization failed for {input_file}: {e}")
            return None

    def tag_audio(self, file_path, metadata, format="mp3"):
        """Tag audio file with metadata."""
        try:
            if format == "mp3":
                audio = MP3(file_path, ID3=mutagen.id3.ID3)
                audio.add_tags()
                audio.tags.add(mutagen.id3.TIT2(encoding=3, text=metadata["title"]))
                audio.tags.add(mutagen.id3.TPE1(encoding=3, text=metadata["artist"]))
                audio.tags.add(mutagen.id3.TALB(encoding=3, text=metadata["album"]))
                audio.save()
            elif format == "flac":
                audio = FLAC(file_path)
                audio["title"] = metadata["title"]
                audio["artist"] = metadata["artist"]
                audio["album"] = metadata["album"]
                audio.save()
            logging.info(f"Tagged {file_path}")
        except Exception as e:
            logging.error(f"Tagging failed for {file_path}: {e}")

    def organize_files(self, file_path, metadata, sort_by="artist"):
        """Organize files into folders by artist or genre."""
        try:
            base_dir = os.path.expanduser("~/Music/SproTeaFi")
            if sort_by == "genre":
                genre = self.sp.artist(metadata["artist"])["genres"][0] if self.sp.artist(metadata["artist"])["genres"] else "Unknown"
                dest_dir = os.path.join(base_dir, genre)
            else:
                dest_dir = os.path.join(base_dir, metadata["artist"])
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(file_path))
            shutil.move(file_path, dest_path)
            logging.info(f"Organized {file_path} to {dest_path}")
            return dest_path
        except Exception as e:
            logging.error(f"Organization failed for {file_path}: {e}")
            return file_path

    def process_playlist(self, playlist_url, format="mp3", sort_by="artist", output_dir="~/Music/SproTeaFi"):
        """Process entire playlist."""
        output_dir = os.path.expanduser(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        tracks = self.get_playlist_tracks(playlist_url)

        with Progress() as progress:
            task = progress.add_task("[green]Processing tracks...", total=len(tracks))
            with ThreadPoolExecutor() as executor:
                futures = []
                for track in tracks:
                    futures.append(executor.submit(self.process_track, track, output_dir, format, sort_by))
                for future in futures:
                    future.result()
                    progress.advance(task)

    def process_track(self, track, output_dir, format, sort_by):
        """Process a single track."""
        safe_title = "".join(c for c in track["title"] if c.isalnum() or c in " -_")
        output_path = os.path.join(output_dir, f"{track['artist']} - {safe_title}")
        
        # Check if file already exists
        final_path = f"{output_path}.{format}"
        if os.path.exists(final_path):
            console.print(f"[yellow]Skipping {track['title']} (already exists)")
            logging.info(f"Skipped {final_path} (already exists)")
            return

        console.print(f"[cyan]Processing {track['title']} by {track['artist']}")
        url = self.search_youtube(track)
        if not url:
            console.print(f"[red]Failed to find {track['title']}")
            return

        temp_file = self.download_track(url, output_path)
        if not temp_file:
            console.print(f"[red]Failed to download {track['title']}")
            return

        norm_file = self.normalize_audio(temp_file, final_path, format)
        if not norm_file:
            console.print(f"[red]Failed to normalize {track['title']}")
            os.remove(temp_file)
            return

        self.tag_audio(norm_file, track, format)
        self.organize_files(norm_file, track, sort_by)
        if norm_file != temp_file:
            os.remove(temp_file)
        console.print(f"[green]Completed {track['title']}")