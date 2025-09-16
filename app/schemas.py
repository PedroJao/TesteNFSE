from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class WebhookCreate(BaseModel):
    url: HttpUrl
    actions: str

class WebhookResponse(BaseModel):
    id: int
    url: HttpUrl
    data_criacao: datetime
    actions: str

    model_config = {"from_attributes": True}

class TaskCreateResponse(BaseModel):
    task_id: int

class TaskResponse(BaseModel):
    id: int
    status: str
    data_criacao: datetime
    data_conclusao: Optional[datetime] = None
    arquivo_pdf: Optional[str] = None
    erro_mensagem: Optional[str] = None

    model_config = {"from_attributes": True}