import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import httpx
from app.models.schemas import ProbeRequest
from app.deps.auth import require_api_key
from app.services.ffmpeg import run_ffprobe_json
router = APIRouter(prefix="/probe", tags=["probe"])
@router.post("", dependencies=[Depends(require_api_key)])
async def probe(req: ProbeRequest):
    tmp = Path(tempfile.mkdtemp(prefix="probe-")); path = tmp / "input.mp4"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
            r = await client.get(req.input)
            if r.status_code >= 400: raise HTTPException(status_code=400, detail=f"cannot fetch input: {r.status_code}")
            path.write_bytes(r.content)
        meta = await run_ffprobe_json(path); return JSONResponse(meta)
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if path.exists(): path.unlink(); tmp.rmdir()
        except Exception: pass
