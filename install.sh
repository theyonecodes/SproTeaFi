#!/bin/bash

# SproTeaFi Installer for Linux/macOS/Termux
set -e

echo "SproTeaFi Installer"
echo "This will install dependencies and set up the environment."
echo "For personal, non-commercial use only. Downloading copyrighted material may be illegal."
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Check for Termux
if [[ -n "$TERMUX_VERSION" ]]; then
    pkg_install="pkg install -y"
    termux-setup-storage
else
    pkg_install="sudo apt-get install -y"
fi

# Install system dependencies
command -v python3 >/dev/null 2>&1 || { echo "Installing python3..."; $pkg_install python3; }
command -v pip3 >/dev/null 2>&1 || { echo "Installing pip3..."; $pkg_install python3-pip; }
command -v ffmpeg >/dev/null 2>&1 || { echo "Installing ffmpeg..."; $pkg_install ffmpeg; }
command -v yt-dlp >/dev/null 2>&1 || { echo "Installing yt-dlp..."; pip3 install yt-dlp; }

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p ~/sproteafi_logs

echo "Installation complete! Run './sproteafi --help' to start."