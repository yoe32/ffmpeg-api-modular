from pydantic import BaseModel, Field
from typing import List, Optional, Literal
class ProbeRequest(BaseModel):
    input: str = Field(..., description="URL pública del video a inspeccionar")
class ProcessParams(BaseModel):
    w: int | None = Field(default=1152)
    h: int | None = Field(default=1760)
    fps: int | None = Field(default=30)
    vcodec: str = Field(default="libx264")
    crf: int = Field(default=18, ge=0, le=51)
    preset: str = Field(default="veryfast")
    acodec: str = Field(default="aac")
    abitrate: str = Field(default="192k")
    pix_fmt: str = Field(default="yuv420p")
    faststart: bool = Field(default=True)
    pad_color: str = Field(default="black")
    fit: Literal["contain", "cover"] = Field(default="contain")
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
