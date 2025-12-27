@echo off
setlocal enabledelayedexpansion
REM Build script for Windows: creates MyBrowser.exe
REM Requirements:
REM  - pyinstaller installed in the venv
REM  - assets\logo.ico (icon)

set APP_NAME=MyBrowser
set ASSETS_DIR=assets
set CONFIG_DIR=config
set ICON_ICO=%ASSETS_DIR%\logo.ico

if not exist "%ICON_ICO%" (
  echo ERROR: %ICON_ICO% not found. Provide an .ico file for the app icon.
  exit /b 1
)

echo [1/3] Running PyInstaller...
pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name %APP_NAME% ^
  --icon %ICON_ICO% ^
  --add-data "%ASSETS_DIR%;assets" ^
  --add-data "%CONFIG_DIR%;config" ^
  --collect-submodules PyQt5.QtWebEngine ^
  --collect-data PyQt5.QtWebEngine ^
  main.py

if errorlevel 1 (
  echo PyInstaller failed.
  exit /b 1
)

echo [2/3] Build completed. Output folder: dist\%APP_NAME%

echo [3/3] You can zip the folder or use an installer maker if desired.
endlocal
