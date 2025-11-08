import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from app.models.schemas import ProcessRequest, AdvancedProcessRequest
from app.deps.auth import require_api_key
from app.services.downloader import download_inputs
from app.services.ffmpeg import concat_copy, concat_transcode, single_transcode, advanced_process
router = APIRouter(prefix="/process", tags=["process"])
@router.post("", dependencies=[Depends(require_api_key)], responses={200:{"content":{"video/mp4":{"schema":{"type":"string","format":"binary"}}},"description":"Archivo MP4 resultante"}}, summary="Procesa y devuelve un MP4 (concat/transcode)")
async def process(req: ProcessRequest):
    if not req.inputs: raise HTTPException(status_code=400, detail="inputs[] requerido")
    work = Path(tempfile.mkdtemp(prefix="proc-"))
    try:
        paths = await download_inputs(req.inputs, work); out_path = work / "out.mp4"
        if len(paths) == 1:
            if req.copy: out_path.write_bytes(Path(paths[0]).read_bytes())
            else: await single_transcode(paths[0], out_path, req.params)
        else:
            if req.copy: await concat_copy(paths, out_path, faststart=req.params.faststart)
            else: await concat_transcode(paths, out_path, req.params)
        return FileResponse(out_path, media_type="video/mp4", filename=req.filename or "output.mp4")
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
@router.post("/advanced", dependencies=[Depends(require_api_key)], responses={200:{"content":{"video/mp4":{"schema":{"type":"string","format":"binary"}}},"description":"Archivo MP4 resultante (modo avanzado)"}}, summary="Modo avanzado con filtergraph y flags controladas")
async def process_advanced(req: AdvancedProcessRequest):
    if not req.inputs: raise HTTPException(status_code=400, detail="inputs[] requerido")
    work = Path(tempfile.mkdtemp(prefix="adv-"))
    try:
        paths = await download_inputs(req.inputs, work); out_path = work / "out.mp4"
        await advanced_process(paths, out_path, req.filtergraph, req.vcodec, req.acodec, req.crf, req.preset, req.extra_args)
        return FileResponse(out_path, media_type="video/mp4", filename=req.filename or "output.mp4")
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
