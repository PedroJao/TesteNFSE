from fastapi import APIRouter, HTTPException
from typing import List
from ..schemas import WebhookCreate, WebhookResponse
from ..database import SessionLocal
from .. import models

router = APIRouter()

@router.post("/webhook", response_model=WebhookResponse)
def create_webhook(payload: WebhookCreate):
    db = SessionLocal()
    try:
        wh = models.Webhook(url=payload.url, actions=payload.actions)
        db.add(wh)
        db.commit()
        db.refresh(wh)
        return wh
    finally:
        db.close()

@router.get("/webhook", response_model=List[WebhookResponse])
def list_webhooks():
    db = SessionLocal()
    try:
        hooks = db.query(models.Webhook).order_by(models.Webhook.id.desc()).limit(1000).all()
        return hooks
    finally:
        db.close()
