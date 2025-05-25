#!/usr/bin/env python3

import argparse
import os
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
from sproteafi_core import SproTeaFi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

def setup_environment():
    """Check and set up environment variables for Spotify API."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        console.print("[yellow]Spotify API credentials not found.")
        client_id = Prompt.ask("[cyan]Enter Spotify Client ID")
        client_secret = Prompt.ask("[cyan]Enter Spotify Client Secret")
        os.environ["SPOTIFY_CLIENT_ID"] = client_id
        os.environ["SPOTIFY_CLIENT_SECRET"] = client_secret
    return client_id, client_secret

def main():
    parser = argparse.ArgumentParser(description="SproTeaFi: Spotify Playlist Downloader (CLI)")
    parser.add_argument("playlist_url", nargs="?", help="Spotify playlist URL")
    parser.add_argument("--format", choices=["mp3", "flac"], default="mp3", help="Output format (default: mp3)")
    parser.add_argument("--sort-by", choices=["artist", "genre"], default="artist", help="Sort by artist or genre (default: artist)")
    parser.add_argument("--output-dir", default="~/Music/SproTeaFi", help="Output directory (default: ~/Music/SproTeaFi)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()

    console.print("[bold green]☕ SproTeaFi: Spotify Playlist Downloader")
    console.print("[yellow]For personal, non-commercial use only. Downloading copyrighted material may be illegal.")

    # Interactive prompts if arguments are missing
    if not args.playlist_url:
        args.playlist_url = Prompt.ask("[cyan]Enter Spotify playlist URL")
    
    if not args.playlist_url.startswith("https://open.spotify.com/playlist/"):
        console.print("[red]Invalid Spotify playlist URL")
        sys.exit(1)

    # Setup environment
    client_id, client_secret = setup_environment()

    # Initialize core
    try:
        sproteafi = SproTeaFi(client_id=client_id, client_secret=client_secret, verbose=args.verbose)
    except Exception as e:
        console.print(f"[red]Failed to initialize: {e}")
        sys.exit(1)

    # Process playlist
    try:
        console.print(f"[cyan]Processing playlist in {args.format.upper()} format, sorted by {args.sort_by}")
        sproteafi.process_playlist(
            playlist_url=args.playlist_url,
            format=args.format,
            sort_by=args.sort_by,
            output_dir=args.output_dir
        )
        console.print("[green]Playlist processing complete! Files saved to", args.output_dir)
    except Exception as e:
        console.print(f"[red]Error processing playlist: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()