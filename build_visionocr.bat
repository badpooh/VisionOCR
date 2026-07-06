@echo off
REM ============================================================
REM VisionOCR - Windows exe build script
REM ------------------------------------------------------------
REM Produces dist\VisionOCR\VisionOCR.exe using python_env.
REM ============================================================

setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0python_env\python.exe"
if not exist "%PYTHON%" (
    echo [ERROR] Python not found: %PYTHON%
    pause
    exit /b 1
)

echo Using Python: %PYTHON%
"%PYTHON%" --version

echo.
echo [1/4] Ensuring PyInstaller ...
"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    "%PYTHON%" -m pip install pyinstaller
    if errorlevel 1 goto :fail_dep
)

echo.
echo [2/4] Cleaning previous build ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/4] Running PyInstaller ...
"%PYTHON%" -m PyInstaller VisionOCR.spec --noconfirm
if errorlevel 1 goto :fail_build

echo.
echo [4/4] Done.
echo Output: %cd%\dist\VisionOCR\VisionOCR.exe
echo.
pause
exit /b 0

:fail_dep
echo.
echo [ERROR] dependency install failed.
pause
exit /b 1

:fail_build
echo.
echo [ERROR] PyInstaller build failed.
pause
exit /b 1
