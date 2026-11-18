# ClipForge

ClipForge turns videos into short vertical clips. Paste a YouTube URL or upload a video, describe the moments you want, and generate clips.

## Windows quick start
1. Download or clone this repository.
2. Double-click `start.bat`. It installs portable FFmpeg and Python dependencies on first launch.
3. Open http://127.0.0.1:7860 in your browser.
4. Paste a YouTube URL or upload a video and press Generate.

## Requirements
- Windows 10/11
- Python 3.10+ (Python launcher `py`)
- Internet connection for setup, downloads, and model download on first run

## Notes
- FFmpeg is downloaded into the project tools folder.
- Whisper transcription currently runs on CPU.
- Clip selection is a basic transcript heuristic; results may need review.
- Portrait framing is center-cropped.
- Only process videos you have permission to download or edit, and follow YouTube's terms and applicable copyright law.
- Keep the terminal window running while using the app.

## Deploy online (cloud)
This repository includes a Render Blueprint (`render.yaml`). GitHub Pages cannot run the video processing backend. To deploy as a public web app, connect this repository to Render and create a Blueprint deployment. See [DEPLOY.md](DEPLOY.md). The free tier is resource-limited and may struggle with longer videos.
