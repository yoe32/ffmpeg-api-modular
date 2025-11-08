import tempfile
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, AnyHttpUrl, Field
import httpx
import asyncio
import os
from fastapi.security.api_key import APIKeyHeader


app = FastAPI(title="FFmpeg Merge (Multi A/V)")

API_KEY = os.getenv("API_KEY", "")
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)
async def require_api_key(key: str = Depends(api_key_header)):
    if not API_KEY:
        return True
    if key == API_KEY:
        return True
    raise HTTPException(status_code=401, detail="Invalid API key")


class MergeRequest(BaseModel):
    videos: List[AnyHttpUrl] = Field(..., min_length=1, description="URLs públicas de video, en orden")
    audios: List[AnyHttpUrl] = Field(default_factory=list, description="URLs públicas de audio, en orden (se concatenan)")
    # Normalización de video simple
    width: int = 1152
    height: int = 1760
    fps: int = 30
    crf: int = 18
    preset: str = "veryfast"
    filename: str = "merged.mp4"


async def _download(url: str, dest: Path):
    async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
        async with client.stream("GET", url) as resp:
            if resp.status_code >= 400:
                raise HTTPException(status_code=400, detail=f"GET {resp.status_code} for {url}")
            with open(dest, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    f.write(chunk)


async def _run_ff(args: list[str]):
    p = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await p.communicate()
    if p.returncode != 0:
        raise HTTPException(status_code=500, detail=f"ffmpeg/ffprobe error: {err.decode()}")


@app.get("/health")
async def health():
    return {"ok": True}


@app.post(
    "/merge",
    dependencies=[Depends(require_api_key)],
    responses={200: {"content": {"video/mp4": {"schema": {"type": "string", "format": "binary"}}},
                     "description": "Archivo MP4 resultante"}},
    summary="Concatena varios videos (normalizados) y varios audios (concatenados) en un MP4"
)
async def merge(req: MergeRequest):
    work = Path(tempfile.mkdtemp(prefix="merge-"))
    try:
        # 1) Descargar insumos
        v_raw_paths: List[Path] = [work / f"vraw_{i}" for i, _ in enumerate(req.videos)]
        a_raw_paths: List[Path] = [work / f"araw_{i}" for i, _ in enumerate(req.audios)]
        tasks = [ _download(str(u), p) for u, p in zip(req.videos, v_raw_paths) ]
        tasks += [ _download(str(u), p) for u, p in zip(req.audios, a_raw_paths) ]
        await asyncio.gather(*tasks)

        # 2) Normalizar cada video a misma resolución/fps/códec (H.264 + yuv420p)
        v_norm_paths: List[Path] = []
        for i, p in enumerate(v_raw_paths):
            outp = work / f"vnorm_{i}.mp4"
            vf = (
                f"scale='min({req.width},iw)':'min({req.height},ih)':"
                f"force_original_aspect_ratio=decrease,"
                f"pad={req.width}:{req.height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                f"fps={req.fps}"
            )
            args = [
                "ffmpeg","-hide_banner","-y","-i",str(p),
                "-vf", vf,
                "-c:v","libx264","-preset",req.preset,"-crf",str(req.crf),
                "-pix_fmt","yuv420p",
                "-c:a","aac","-b:a","192k",
                str(outp)
            ]
            await _run_ff(args)
            v_norm_paths.append(outp)

        # 3) Concat de videos con copy
        v_list = work / "vlist.txt"
        v_list.write_text("\n".join([f"file '{p}'" for p in v_norm_paths]))
        v_merged = work / "merged_video.mp4"
        await _run_ff([
            "ffmpeg","-hide_banner","-y",
            "-f","concat","-safe","0","-i",str(v_list),
            "-c","copy",
            "-movflags","+faststart",
            str(v_merged)
        ])

        # 4) Procesar audios (opcional): transcodificar a AAC y concatenar
        if a_raw_paths:
            a_norm_paths: List[Path] = []
            for i, p in enumerate(a_raw_paths):
                outa = work / f"anorm_{i}.m4a"
                await _run_ff([
                    "ffmpeg","-hide_banner","-y","-i",str(p),
                    "-c:a","aac","-b:a","192k",
                    "-vn",
                    str(outa)
                ])
                a_norm_paths.append(outa)

            a_list = work / "alist.txt"
            a_list.write_text("\n".join([f"file '{p}'" for p in a_norm_paths]))
            a_merged = work / "merged_audio.m4a"
            await _run_ff([
                "ffmpeg","-hide_banner","-y",
                "-f","concat","-safe","0","-i",str(a_list),
                "-c","copy",
                str(a_merged)
            ])

            # 5) Merge final: video concatenado + audio concatenado
            out_path = work / "out.mp4"
            await _run_ff([
                "ffmpeg","-hide_banner","-y",
                "-i", str(v_merged),
                "-i", str(a_merged),
                "-map","0:v","-map","1:a",
                "-c:v","copy","-c:a","aac",
                "-movflags","+faststart",
                str(out_path)
            ])
        else:
            # si no hay audios, devolvemos solo el video concatenado
            out_path = v_merged

        return FileResponse(out_path, media_type="video/mp4", filename=req.filename)
    finally:
        # Limpieza best-effort (no removemos inmediatamente; FileResponse gestiona el handle)
        pass
