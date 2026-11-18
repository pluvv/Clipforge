from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import subprocess, uuid, re, os

ROOT=Path(__file__).resolve().parents[1]
UPLOAD=ROOT/'uploads'; OUTPUT=ROOT/'output'; UPLOAD.mkdir(exist_ok=True); OUTPUT.mkdir(exist_ok=True)
app=FastAPI(title='ClipForge')
app.mount('/static',StaticFiles(directory=ROOT/'app'/'static'),name='static')

def exe(name):
    local=ROOT/'tools'/'ffmpeg'/'bin'/f'{name}.exe'
    return str(local if local.exists() else name)

@app.get('/',response_class=HTMLResponse)
def home(): return (ROOT/'app'/'static'/'index.html').read_text(encoding='utf-8')

@app.post('/api/generate')
async def generate(url: str=Form(''), prompt: str=Form(''), video: UploadFile|None=File(None)):
    job=uuid.uuid4().hex[:8]; source=None
    if url.strip():
        try:
            import yt_dlp
        except ImportError: raise HTTPException(500,'yt-dlp is missing. Run start.bat again.')
        out=str(UPLOAD/f'{job}.%(ext)s')
        opts={'format':'bestvideo[height<=1080]+bestaudio/best[height<=1080]','merge_output_format':'mp4','outtmpl':out,'quiet':True,'no_warnings':True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url.strip()])
            files=list(UPLOAD.glob(job+'.*')); source=files[0] if files else None
        except Exception as e: raise HTTPException(400,'Could not download that video. Check the link and try again. '+str(e)[:200])
    elif video and video.filename:
        ext=Path(video.filename).suffix.lower()
        if ext not in ['.mp4','.mov','.mkv','.webm','.avi']: raise HTTPException(400,'Unsupported video format')
        source=UPLOAD/f'{job}{ext}'; source.write_bytes(await video.read())
    else: raise HTTPException(400,'Paste a YouTube link or upload a video.')
    if not source or not source.exists(): raise HTTPException(400,'Video download/file could not be found.')
    ffprobe=exe('ffprobe'); ffmpeg=exe('ffmpeg')
    try:
        duration=float(subprocess.check_output([ffprobe,'-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(source)],text=True).strip())
    except Exception: raise HTTPException(500,'FFmpeg/ffprobe could not read the video. Restart using start.bat.')
    try:
        from faster_whisper import WhisperModel
        model=WhisperModel(os.getenv('CLIPFORGE_MODEL', 'small'),device='cpu',compute_type='int8')
        trans,_=model.transcribe(str(source),vad_filter=True)
        segments=[(seg.start,seg.end,seg.text.strip()) for seg in trans]
        key=[w.lower() for w in re.findall(r'\w+',prompt) if len(w)>3]
        candidates=[]
        for st,en,txt in segments:
            start=max(0,st-8); end=min(duration,en+18)
            if end-start<12: end=min(duration,start+25)
            score=1+sum(2 for k in key if k in txt.lower())+sum(1 for k in ['wow','laugh','crazy','insane','amazing','but','however','finally','secret'] if k in txt.lower())
            candidates.append((score,start,end,txt))
        candidates.sort(reverse=True); chosen=[]
        for _,st,en,txt in candidates:
            if en-st>60: en=st+60
            if all(en<=a or st>=b for a,b in chosen):
                chosen.append((st,en))
                if len(chosen)>=5: break
    except Exception as e: raise HTTPException(500,'Transcription failed. '+str(e)[:220])
    if not chosen: chosen=[(0,min(duration,45))]
    results=[]
    for i,(st,en) in enumerate(chosen,1):
        name=f'{job}_clip{i}.mp4'; dest=OUTPUT/name
        cmd=[ffmpeg,'-y','-ss',str(st),'-i',str(source),'-t',str(en-st),'-vf','scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920','-c:v','libx264','-preset','fast','-crf','23','-c:a','aac','-b:a','128k','-movflags','+faststart',str(dest)]
        try: subprocess.run(cmd,check=True,capture_output=True)
        except Exception as e: raise HTTPException(500,'Rendering failed: '+str(e)[:180])
        results.append({'name':name,'url':f'/api/download/{name}','start':round(st),'end':round(en)})
    return {'clips':results}

@app.get('/api/download/{filename}')
def download(filename:str):
    p=OUTPUT/filename
    if not p.exists() or p.parent!=OUTPUT: raise HTTPException(404)
    return FileResponse(p,media_type='video/mp4',filename=filename)