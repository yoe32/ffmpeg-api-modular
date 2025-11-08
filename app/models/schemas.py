from pydantic import BaseModel, Field
from typing import List, Optional, Literal
class ProbeRequest(BaseModel):
    input: str = Field(..., description="URL pública")
class ProcessParams(BaseModel):
    w: int | None = 1152
    h: int | None = 1760
    fps: int | None = 30
    vcodec: str = "libx264"
    crf: int = 18
    preset: str = "veryfast"
    acodec: str = "aac"
    abitrate: str = "192k"
    pix_fmt: str = "yuv420p"
    faststart: bool = True
    pad_color: str = "black"
    fit: Literal["contain", "cover"] = "contain"
class ProcessRequest(BaseModel):
    inputs: List[str] = Field(..., min_length=1)
    concat: bool = True
    copy: bool = False
    filename: Optional[str] = "output.mp4"
    params: ProcessParams = ProcessParams()
class AdvancedProcessRequest(BaseModel):
    inputs: List[str] = Field(..., min_length=1)
    filtergraph: str
    map: Optional[list[str]] = None
    vcodec: str = "libx264"
    acodec: str = "aac"
    crf: int = 18
    preset: str = "veryfast"
    extra_args: list[str] = []
    filename: Optional[str] = "output.mp4"
