from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ProbeRequest(BaseModel):
    input: str = Field(..., description="URL pública del video a inspeccionar")


class ProcessParams(BaseModel):
    w: int | None = Field(default=1152, description="Ancho de salida")
    h: int | None = Field(default=1760, description="Alto de salida")
    fps: int | None = Field(default=30, description="FPS de salida")
    vcodec: str = Field(default="libx264")
    crf: int = Field(default=18, ge=0, le=51)
    preset: str = Field(default="veryfast")
    acodec: str = Field(default="aac")
    abitrate: str = Field(default="192k")
    pix_fmt: str = Field(default="yuv420p")
    faststart: bool = Field(default=True, description="Añade -movflags +faststart")
    pad_color: str = Field(default="black", description="Nombre CSS o #RRGGBB")
    fit: Literal["contain", "cover"] = Field(default="contain")


class ProcessRequest(BaseModel):
    inputs: List[str] = Field(..., min_length=1, description="URLs públicas GET")
    concat: bool = True
    copy: bool = False  # aviso: Pydantic puede mostrar warning por 'copy' en BaseModel, es inofensivo
    filename: Optional[str] = Field(default="output.mp4")
    params: ProcessParams = Field(default_factory=ProcessParams)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "inputs": [
                    "https://<project>.supabase.co/storage/v1/object/public/raw/clip1.mp4",
                    "https://<project>.supabase.co/storage/v1/object/public/raw/clip2.mp4"
                ],
                "concat": True,
                "copy": False,
                "filename": "merged.mp4",
                "params": {
                    "w": 1152, "h": 1760, "fps": 30, "crf": 18, "preset": "veryfast",
                    "pix_fmt": "yuv420p", "faststart": True
                }
            }]
        }
    }


class AdvancedProcessRequest(BaseModel):
    inputs: List[str] = Field(..., min_length=1)
    filtergraph: str = Field(..., description="Filtergraph FFmpeg")
    map: Optional[list[str]] = Field(default=None, description="Mapeo de streams, ej: ['0:v:0','0:a:0']")
    vcodec: str = "libx264"
    acodec: str = "aac"
    crf: int = 18
    preset: str = "veryfast"
    extra_args: list[str] = Field(default_factory=list, description="Flags adicionales (lista blanca interna)")
    filename: Optional[str] = "output.mp4"


class MergeAVRequest(BaseModel):
    videos: List[str] = Field(..., min_length=1, description="URLs públicas de video a concatenar")
    audio: str = Field(..., description="URL pública del audio global (mp3/wav/m4a...)")
    filename: Optional[str] = "merged_with_audio.mp4"
    params: ProcessParams = Field(default_factory=ProcessParams)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "videos": [
                    "https://<project>.supabase.co/storage/v1/object/public/raw/v1.mp4",
                    "https://<project>.supabase.co/storage/v1/object/public/raw/v2.mp4"
                ],
                "audio": "https://<project>.supabase.co/storage/v1/object/public/raw/global.mp3",
                "filename": "final.mp4",
                "params": { "w": 1152, "h": 1760, "fps": 30, "crf": 18, "preset": "veryfast" }
            }]
        }
    }
