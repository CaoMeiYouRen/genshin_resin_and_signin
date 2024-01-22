chcp 65001
@echo off
set VM_PATH="D:\Program Files\MuMu\emulator\MuMuPlayer-12.0\shell"
start /d %VM_PATH% MuMuPlayer.exe

timeout /t 90 /nobreak

python -V
python auto_miyoushe_signin.py

timeout /t 5 /nobreak

taskkill /F /IM MuMuPlayer.exe
taskkill /F /IM MuMuVMMHeadless.exe
taskkill /F /IM MuMuVMMSVC.exe

exit