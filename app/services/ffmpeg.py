import asyncio
from pathlib import Path
from typing import List
from app.models.schemas import ProcessParams
def color_to_ffmpeg(c: str) -> str:
    if c.startswith("#") and len(c) == 7: return c[1:]
    return c
async def run_ffmpeg(args: list[str]) -> None:
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode != 0: raise RuntimeError(f"ffmpeg error: {err.decode()}")
async def run_ffprobe_json(path: Path) -> dict:
    import json as _json
    proc = await asyncio.create_subprocess_exec("ffprobe","-v","error","-show_format","-show_streams","-print_format","json", str(path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode != 0: raise RuntimeError(f"ffprobe error: {err.decode()}")
    return _json.loads(out.decode())
async def concat_copy(inputs: List[Path], out_path: Path, faststart: bool = True) -> None:
    lst = out_path.with_suffix(".txt"); lst.write_text("\n".join([f"file '{p}'" for p in inputs]))
    args = ["ffmpeg","-hide_banner","-y","-f","concat","-safe","0","-i",str(lst),"-c","copy"]
    if faststart: args += ["-movflags","+faststart"]
    args.append(str(out_path))
    await run_ffmpeg(args)
async def concat_transcode(inputs: List[Path], out_path: Path, params: ProcessParams) -> None:
    lst = out_path.with_suffix(".txt"); lst.write_text("\n".join([f"file '{p}'" for p in inputs]))
    w = params.w or 1152; h = params.h or 1760
    if params.fit == "contain":
        vf = f"scale='min({w},iw)':'min({h},ih)':force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={color_to_ffmpeg(params.pad_color)}"
    else:
        vf = f"scale='{w}*max(1,iw/{w})':'{h}*max(1,ih/{h})',crop={w}:{h}"
    if params.fps: vf += f",fps={params.fps}"
    args = ["ffmpeg","-hide_banner","-y","-f","concat","-safe","0","-i",str(lst),
            "-vf", vf, "-c:v", params.vcodec, "-preset", params.preset, "-crf", str(params.crf),
            "-pix_fmt", params.pix_fmt, "-c:a", params.acodec, "-b:a", params.abitrate]
    if params.faststart: args += ["-movflags","+faststart"]
    args.append(str(out_path))
    await run_ffmpeg(args)
async def single_transcode(inp: Path, out_path: Path, params: ProcessParams) -> None:
    w = params.w or 1152; h = params.h or 1760
    if params.fit == "contain":
        vf = f"scale='min({w},iw)':'min({h},ih)':force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={color_to_ffmpeg(params.pad_color)}"
    else:
        vf = f"scale='{w}*max(1,iw/{w})':'{h}*max(1,ih/{h})',crop={w}:{h}"
    if params.fps: vf += f",fps={params.fps}"
    args = ["ffmpeg","-hide_banner","-y","-i",str(inp),
            "-vf", vf, "-c:v", params.vcodec, "-preset", params.preset, "-crf", str(params.crf),
            "-pix_fmt", params.pix_fmt, "-c:a", params.acodec, "-b:a", params.abitrate]
    if params.faststart: args += ["-movflags","+faststart"]
    args.append(str(out_path))
    await run_ffmpeg(args)
SAFE_EXTRA_ARGS = {"-shortest","-t","-to","-ss"}
async def advanced_process(inputs, out_path: Path, filtergraph: str, vcodec: str, acodec: str, crf: int, preset: str, extra_args: list[str]) -> None:
    lst = out_path.with_suffix(".txt"); lst.write_text("\n".join([f"file '{p}'" for p in inputs]))
    args = ["ffmpeg","-hide_banner","-y","-f","concat","-safe","0","-i",str(lst),
            "-filter_complex", filtergraph, "-c:v", vcodec, "-preset", preset, "-crf", str(crf), "-c:a", acodec]
    filtered = []; it = iter(extra_args or [])
    for token in it:
        if token in SAFE_EXTRA_ARGS:
            filtered.append(token)
            if token in {"-t","-to","-ss"}:
                try: filtered.append(next(it))
                except StopIteration: pass
    args += filtered; args.append(str(out_path))
    await run_ffmpeg(args)
