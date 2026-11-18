# Deploy ClipForge online

This repo is prepared for a Render web-service deployment using the included render.yaml.

1. Sign in to Render (https://render.com) and connect your GitHub account.
2. Choose **New > Blueprint** and select this repository.
3. Confirm the service settings from render.yaml and deploy.
4. Once deployment completes, use the Render-provided public URL.

Notes:
- This is a server-side app; GitHub Pages alone cannot run video processing.
- Free hosting may sleep when idle and has limited RAM, CPU, storage, and request duration. Large videos or Whisper model downloads may fail or time out.
- Uploaded/downloaded videos and generated clips are stored on ephemeral service storage and may disappear after redeploy/restart.
- Use videos you have permission to process and comply with YouTube terms and copyright.
