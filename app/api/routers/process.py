import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from app.models.schemas import (
    ProcessRequest,
    AdvancedProcessRequest,
    MergeAVRequest,
)
from app.deps.auth import require_api_key
from app.services.downloader import download_inputs
from app.services.ffmpeg import (
    concat_copy,
    concat_transcode,
    single_transcode,
    advanced_process,
    normalize_many,
    concat_copy_from_list_file,
    add_global_audio,
)

router = APIRouter(prefix="/process", tags=["process"])


@router.post(
    "",
    dependencies=[Depends(require_api_key)],
    responses={
        200: {
            "content": {"video/mp4": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Archivo MP4 resultante"
        }
    },
    summary="Procesa y devuelve un MP4 (concat/transcode)"
)
async def process(req: ProcessRequest):
    if not req.inputs:
        raise HTTPException(status_code=400, detail="inputs[] requerido")
    work = Path(tempfile.mkdtemp(prefix="proc-"))
    try:
        paths = await download_inputs(req.inputs, work)
        out_path = work / "out.mp4"
        if len(paths) == 1:
            if req.copy:
                out_path.write_bytes(Path(paths[0]).read_bytes())
            else:
                await single_transcode(paths[0], out_path, req.params)
        else:
            if req.copy:
                await concat_copy(paths, out_path, faststart=req.params.faststart)
            else:
                await concat_transcode(paths, out_path, req.params)
        return FileResponse(out_path, media_type="video/mp4", filename=req.filename or "output.mp4")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/advanced",
    dependencies=[Depends(require_api_key)],
    responses={
        200: {
            "content": {"video/mp4": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Archivo MP4 resultante (modo avanzado)"
        }
    },
    summary="Modo avanzado con filtergraph y flags controladas"
)
async def process_advanced(req: AdvancedProcessRequest):
    if not req.inputs:
        raise HTTPException(status_code=400, detail="inputs[] requerido")
    work = Path(tempfile.mkdtemp(prefix="adv-"))
    try:
        paths = await download_inputs(req.inputs, work)
        out_path = work / "out.mp4"
        await advanced_process(
            paths, out_path,
            req.filtergraph, req.vcodec, req.acodec, req.crf, req.preset, req.extra_args
        )
        return FileResponse(out_path, media_type="video/mp4", filename=req.filename or "output.mp4")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/merge-av",
    dependencies=[Depends(require_api_key)],
    responses={
        200: {
            "content": {"video/mp4": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Video final (concatenación de videos normalizados + audio global)"
        }
    },
    summary="Concatena varios videos (normalizados) y agrega un audio global; devuelve MP4"
)
async def merge_av(req: MergeAVRequest):
    if not req.videos:
        raise HTTPException(status_code=400, detail="videos[] requerido")
    if not req.audio:
        raise HTTPException(status_code=400, detail="audio requerido")

    work = Path(tempfile.mkdtemp(prefix="mergeav-"))
    try:
        # 1) Descargar videos y audio
        video_paths = await download_inputs(req.videos, work)
        audio_path = (await download_inputs([req.audio], work))[0]

        # 2) Normalizar todos los videos a la misma resolución/fps/códecs
        normalized = await normalize_many(video_paths, work, req.params)

        # 3) Concat (copy) con lista
        list_file = work / "concat.txt"
        list_file.write_text("\n".join([f"file '{p}'" for p in normalized]))
        merged_video = work / "merged_video.mp4"
        await concat_copy_from_list_file(list_file, merged_video, faststart=req.params.faststart)

        # 4) Agregar audio global (map 0:v + 1:a), dejar video en copy
        final_out = work / "final.mp4"
        await add_global_audio(merged_video, audio_path, final_out)

        return FileResponse(final_out, media_type="video/mp4", filename=req.filename or "output.mp4")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
