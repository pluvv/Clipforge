import os, re, uuid, subprocess, json, shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

ROOT=Path(__file__).resolve().parent.parent
UPLOADS=ROOT/'uploads'; OUTPUT=ROOT/'output'
UPLOADS.mkdir(exist_ok=True); OUTPUT.mkdir(exist_ok=True)
app=FastAPI(title='ClipForge AI')
app.mount('/static',StaticFiles(directory=Path(__file__).parent/'static'),name='static')

@app.get('/',response_class=HTMLResponse)
def home(): return (Path(__file__).parent/'static'/'index.html').read_text(encoding='utf8')

def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode: raise RuntimeError((p.stderr or p.stdout)[-2500:])
    return p.stdout

def transcribe(path):
    try:
        from faster_whisper import WhisperModel
        model=WhisperModel(os.getenv('WHISPER_MODEL','small'), device='cuda' if os.getenv('USE_CUDA','0')=='1' else 'cpu', compute_type='float16' if os.getenv('USE_CUDA','0')=='1' else 'int8')
        segs,info=model.transcribe(str(path),vad_filter=True,word_timestamps=False)
        return [{'start':s.start,'end':s.end,'text':s.text.strip()} for s in segs]
    except Exception as e: raise RuntimeError(f'Transcription failed: {e}')

def rank_segments(segments,prompt,duration):
    terms=set(re.findall(r'[a-z0-9]+',prompt.lower()))
    signals=['laugh','lol','haha','wow','oh','damn','shit','fuck','scream','crazy','what','no way','bro','fail','kill','death','unexpected','insane']
    candidates=[]
    for i,s in enumerate(segments):
        start=max(0,s['start']-12); end=min(duration,s['end']+30)
        if end-start<20: end=min(duration,start+45)
        text=s['text'].lower(); score=sum(2 for w in signals if w in text)+sum(1 for w in terms if w in text)
        context=' '.join(x['text'] for x in segments[max(0,i-2):min(len(segments),i+5)])
        score+=sum(1 for w in signals if w in context.lower())
        candidates.append({'start':start,'end':min(end,start+90),'score':score,'reason':context[:260]})
    candidates.sort(key=lambda x:x['score'],reverse=True)
    out=[]
    for c in candidates:
        if all(abs(c['start']-x['start'])>35 for x in out):out.append(c)
        if len(out)>=8:break
    return out

def render_clip(src,dst,start,end):
    duration=end-start
    vf="scale=-2:1920,crop=1080:1920:(iw-1080)/2:0,setsar=1"
    run(['ffmpeg','-y','-ss',str(start),'-i',str(src),'-t',str(duration),'-vf',vf,'-c:v','libx264','-preset','fast','-crf','23','-c:a','aac','-b:a','128k','-movflags','+faststart',str(dst)])

@app.post('/api/process')
async def process(video:UploadFile=File(...),prompt:str=Form('Find the most engaging moments')):
    if not video.filename: raise HTTPException(400,'Missing filename')
    ext=Path(video.filename).suffix.lower()
    if ext not in ['.mp4','.mov','.mkv','.webm','.avi']: raise HTTPException(400,'Unsupported video format')
    job=uuid.uuid4().hex[:10]; path=UPLOADS/f'{job}{ext}'
    with path.open('wb') as f: shutil.copyfileobj(video.file,f)
    try:
        info=json.loads(run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)])); duration=float(info['format']['duration'])
        segments=transcribe(path); moments=rank_segments(segments,prompt,duration)
        clips=[]
        for i,m in enumerate(moments):
            target=OUTPUT/f'{job}_clip_{i+1}.mp4'
            try:
                render_clip(path,target,m['start'],m['end']); clips.append({'id':target.name,'start':round(m['start'],1),'end':round(m['end'],1),'score':m['score'],'context':m['reason'],'url':f'/api/download/{target.name}'})
            except Exception as e: clips.append({'error':str(e),'start':m['start']})
        return {'duration':duration,'clips':clips,'transcript_segments':len(segments)}
    except Exception as e: raise HTTPException(500,str(e))

@app.get('/api/download/{filename}')
def download(filename:str):
    p=OUTPUT/filename
    if not p.exists() or p.parent!=OUTPUT: raise HTTPException(404,'Clip not found')
    return FileResponse(p,media_type='video/mp4',filename=filename)
