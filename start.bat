@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo === ClipForge Setup ===
set "FFBIN=%CD%\tools\ffmpeg\bin"
if not exist "%FFBIN%\ffmpeg.exe" (
 echo Installing FFmpeg automatically...
 powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $root=(Get-Location).Path; $tools=Join-Path $root 'tools'; New-Item -ItemType Directory -Force $tools | Out-Null; $zip=Join-Path $tools 'ffmpeg.zip'; $tmp=Join-Path $tools 'ffmpeg_tmp'; if(Test-Path $tmp){Remove-Item $tmp -Recurse -Force}; Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $zip; Expand-Archive $zip $tmp -Force; $found=Get-ChildItem $tmp -Filter ffmpeg.exe -File -Recurse | Select-Object -First 1; if(!$found){throw 'Archive downloaded but ffmpeg.exe not found'}; $bin=$found.Directory.FullName; $dest=Join-Path $tools 'ffmpeg\bin'; New-Item -ItemType Directory -Force $dest | Out-Null; Get-ChildItem $bin -File | ForEach-Object {Copy-Item $_.FullName $dest -Force}; if(!(Test-Path (Join-Path $dest 'ffmpeg.exe'))){throw 'Copy failed'}; Remove-Item $zip -Force -ErrorAction SilentlyContinue; Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue; Write-Host 'FFmpeg ready.'"
 if errorlevel 1 goto fail
)
set "PATH=%FFBIN%;%PATH%"
if not exist .venv\Scripts\python.exe (
 echo Creating Python environment...
 py -3 -m venv .venv
 if errorlevel 1 goto fail
)
echo Installing Python packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Launching ClipForge at http://127.0.0.1:7860
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 7860
goto end
:fail
echo Setup failed. Please send a screenshot of this window.
pause
:end
endlocal