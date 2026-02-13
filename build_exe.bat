@echo off
echo Building ImageOrganizer Windows Executable...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install packages
echo Installing dependencies...
pip install --upgrade pip
pip install pillow pyinstaller

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "ImageOrganizer.spec" del "ImageOrganizer.spec"

REM Build executable
echo Building executable...
pyinstaller --onefile ^
            --name "ImageOrganizer" ^
            --icon "NONE" ^
            --add-data "requirements.txt;." ^
            --hidden-import "PIL" ^
            --hidden-import "PIL._imaging" ^
            --hidden-import "PIL._imagingtk" ^
            --hidden-import "PIL._webp" ^
            --console ^
            src/main.py

REM Deactivate venv
deactivate

REM Report result
if exist "dist\ImageOrganizer.exe" (
    echo.
    echo ✅ SUCCESS: Executable built!
    echo 📍 Location: %CD%\dist\ImageOrganizer.exe
    echo.
    echo 📋 To use:
    echo   1. Copy ImageOrganizer.exe anywhere
    echo   2. Run from Command Prompt or double-click
    echo   3. First run creates ImageOrganizer folder in your Documents
    echo.
    
    REM Ask to copy to desktop
    set /p copyToDesktop="📂 Copy to Desktop? (y/N): "
    if /i "%copyToDesktop%"=="y" (
        copy "dist\ImageOrganizer.exe" "%USERPROFILE%\Desktop\ImageOrganizer.exe"
        echo ✅ Copied to Desktop!
    )
) else (
    echo.
    echo ❌ ERROR: Build failed!
)

echo.
pause