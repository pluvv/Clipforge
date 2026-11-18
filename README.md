# ClipForge AI
Local-first prototype that transcribes a video and ranks candidate moments from the transcript, then renders vertical MP4 clips.

## Requirements
- Windows 10/11
- Python 3.10–3.12
- FFmpeg and ffprobe installed and available on PATH

## Start
1. Install FFmpeg (ensure `ffmpeg` and `ffprobe` work in Command Prompt).
2. Double-click `start.bat`. First launch installs Python dependencies.
3. Open http://127.0.0.1:7860
4. Upload a video and enter a clipping prompt.

## Prototype limitations
- Transcript heuristics, not yet semantic LLM ranking; prompt keyword matching is rudimentary.
- CPU transcription by default; CUDA can be enabled with `USE_CUDA=1` after installing compatible CUDA libraries.
- Clips use center-crop portrait framing. No burned-in subtitles yet.
- YouTube URL ingestion is not implemented. Use videos you own or are authorized to process; respect platform terms and rights.
- Long videos can take a while. This prototype renders candidate clips sequentially.
