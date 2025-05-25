@echo off
ECHO SproTeaFi Installer for Windows
ECHO This will install dependencies and set up the environment.
ECHO For personal, non-commercial use only. Downloading copyrighted material may be illegal.
set /p REPLY=Continue? (y/N) 
IF /I NOT "%REPLY%"=="y" EXIT /B 1

:: Install system dependencies
where python >nul 2>&1 || (ECHO Installing Python... & winget install Python.Python.3)
where ffmpeg >nul 2>&1 || (ECHO Installing ffmpeg... & winget install ffmpeg)
where yt-dlp >nul 2>&1 || (ECHO Installing yt-dlp... & pip install yt-dlp)

:: Create virtual environment
python -m venv venv
call venv\Scripts\activate

:: Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

:: Create logs directory
mkdir %USERPROFILE%\sproteafi_logs

ECHO Installation complete! Run "sproteafi --help" to start.