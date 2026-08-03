from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Niche = Literal["interior", "exterior", "product_model"]


class GenerateImagesRequest(BaseModel):
    niche: str
    style: str
    images: list[str] = Field(default_factory=list)
    user_prompt: Optional[str] = Field(default=None, max_length=200)
    n_variants: int = 3


class Variant(BaseModel):
    label: str
    url: str


class GenerateImagesResponse(BaseModel):
    niche: Niche
    style: str
    variants: list[Variant]


Provider3D = Literal["byteplus_hyper3d", "tencent_hunyuan3d", "tencent_hunyuan3d_pro"]


class Generate3DRequest(BaseModel):
    images: list[str] = Field(default_factory=list, max_length=4)
    user_prompt: Optional[str] = Field(default=None, max_length=200)
    provider: Provider3D = "byteplus_hyper3d"


class Generate3DResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    task_id: str
    status: str
    model_url: Optional[str] = None
    preview_url: Optional[str] = None
    model_type: Optional[str] = None


class AnimateRequest(BaseModel):
    model_url: str
    motion_type: int = Field(ge=1, le=48)


class StylesResponse(BaseModel):
    interior: list[str]
    exterior: list[str]
    product_model: list[str]


class HealthResponse(BaseModel):
    status: str
    app: str
    port: int
