import asyncio
from pathlib import Path
from typing import List
from app.models.schemas import ProcessParams


def color_to_ffmpeg(c: str) -> str:
    if c.startswith("#") and len(c) == 7:
        return c[1:]  # FFmpeg acepta hex sin '#'
    return c


async def run_ffmpeg(args: list[str]) -> None:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {err.decode()}")


async def run_ffprobe_json(path: Path) -> dict:
    import json as _json
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-print_format", "json", str(path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe error: {err.decode()}")
    return _json.loads(out.decode())


async def concat_copy(inputs: List[Path], out_path: Path, faststart: bool = True) -> None:
    lst = out_path.with_suffix(".txt")
    lst.write_text("\n".join([f"file '{p}'" for p in inputs]))
    args = ["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy"]
    if faststart:
        args += ["-movflags", "+faststart"]
    args.append(str(out_path))
    await run_ffmpeg(args)


async def concat_transcode(inputs: List[Path], out_path: Path, params: ProcessParams) -> None:
    lst = out_path.with_suffix(".txt")
    lst.write_text("\n".join([f"file '{p}'" for p in inputs]))
    w = params.w or 1152
    h = params.h or 1760
    if params.fit == "contain":
        vf = (
            f"scale='min({w},iw)':'min({h},ih)':force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={color_to_ffmpeg(params.pad_color)}"
        )
    else:
        vf = f"scale='{w}*max(1,iw/{w})':'{h}*max(1,ih/{h})',crop={w}:{h}"
    if params.fps:
        vf += f",fps={params.fps}"
    args = [
        "ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-vf", vf, "-c:v", params.vcodec, "-preset", params.preset, "-crf", str(params.crf),
        "-pix_fmt", params.pix_fmt, "-c:a", params.acodec, "-b:a", params.abitrate
    ]
    if params.faststart:
        args += ["-movflags", "+faststart"]
    args.append(str(out_path))
    await run_ffmpeg(args)


async def single_transcode(inp: Path, out_path: Path, params: ProcessParams) -> None:
    w = params.w or 1152
    h = params.h or 1760
    if params.fit == "contain":
        vf = (
            f"scale='min({w},iw)':'min({h},ih)':force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={color_to_ffmpeg(params.pad_color)}"
        )
    else:
        vf = f"scale='{w}*max(1,iw/{w})':'{h}*max(1,ih/{h})',crop={w}:{h}"
    if params.fps:
        vf += f",fps={params.fps}"
    args = [
        "ffmpeg", "-hide_banner", "-y", "-i", str(inp),
        "-vf", vf, "-c:v", params.vcodec, "-preset", params.preset, "-crf", str(params.crf),
        "-pix_fmt", params.pix_fmt, "-c:a", params.acodec, "-b:a", params.abitrate
    ]
    if params.faststart:
        args += ["-movflags", "+faststart"]
    args.append(str(out_path))
    await run_ffmpeg(args)


# ---------- NUEVOS HELPERS PARA MERGE A/V ----------

async def normalize_video(inp: Path, out_path: Path, params: ProcessParams) -> None:
    w = params.w or 1152
    h = params.h or 1760
    if params.fit == "contain":
        vf = (
            f"scale='min({w},iw)':'min({h},ih)':force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={color_to_ffmpeg(params.pad_color)}"
        )
    else:
        vf = f"scale='{w}*max(1,iw/{w})':'{h}*max(1,ih/{h})',crop={w}:{h}"
    if params.fps:
        vf += f",fps={params.fps}"

    args = [
        "ffmpeg", "-hide_banner", "-y", "-i", str(inp),
        "-vf", vf,
        "-c:v", params.vcodec, "-preset", params.preset, "-crf", str(params.crf),
        "-pix_fmt", params.pix_fmt,
        "-c:a", params.acodec, "-b:a", params.abitrate,
        str(out_path)
    ]
    await run_ffmpeg(args)


async def normalize_many(inputs: List[Path], workdir: Path, params: ProcessParams) -> List[Path]:
    out_paths: List[Path] = []
    for i, p in enumerate(inputs):
        outp = workdir / f"normalized_{i}.mp4"
        await normalize_video(p, outp, params)
        out_paths.append(outp)
    return out_paths


async def concat_copy_from_list_file(list_file: Path, out_path: Path, faststart: bool = True) -> None:
    args = ["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy"]
    if faststart:
        args += ["-movflags", "+faststart"]
    args.append(str(out_path))
    await run_ffmpeg(args)


async def add_global_audio(video_path: Path, audio_path: Path, out_path: Path) -> None:
    # Mapea 0:v (video original) + 1:a (audio global)
    args = [
        "ffmpeg", "-hide_banner", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac",
        str(out_path)
    ]
    await run_ffmpeg(args)
