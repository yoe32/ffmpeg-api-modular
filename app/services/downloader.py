import asyncio
from pathlib import Path
from typing import List
import httpx
from app.core.config import settings
async def download_one(client: httpx.AsyncClient, url: str, out_dir: Path) -> Path:
    base = url.split("?")[0].split("/")[-1]
    ext = ".mp4"
    if "." in base: ext = "." + base.split(".")[-1]
    name = f"in-{abs(hash(url)) % (10**8)}{ext}"
    path = out_dir / name
    async with client.stream("GET", url) as resp:
        if resp.status_code >= 400: raise RuntimeError(f"GET {resp.status_code} for {url}")
        with open(path, "wb") as f:
            async for chunk in resp.aiter_bytes(): f.write(chunk)
    return path
async def download_inputs(urls: List[str], out_dir: Path) -> List[Path]:
    limits = httpx.Limits(max_keepalive_connections=settings.MAX_PARALLEL_DOWNLOADS, max_connections=settings.MAX_PARALLEL_DOWNLOADS)
    timeout = None if settings.DOWNLOAD_TIMEOUT is None else httpx.Timeout(settings.DOWNLOAD_TIMEOUT)
    async with httpx.AsyncClient(follow_redirects=True, limits=limits, timeout=timeout) as client:
        sem = asyncio.Semaphore(settings.MAX_PARALLEL_DOWNLOADS)
        async def task(u):
            async with sem: return await download_one(client, u, out_dir)
        return await asyncio.gather(*[task(u) for u in urls])
