import requests
from sqlalchemy.orm import Session
from .. import models
from typing import List
from datetime import datetime

def notify_webhooks_for_action(db: Session, action: str, task_id: int):
    """Pega webhooks que contem a action e notifica (background)."""
    try:
        hooks: List[models.Webhook] = db.query(models.Webhook).filter(models.Webhook.actions.contains(action)).all()
        payload = {"action": action, "task_id": task_id, "timestamp": datetime.utcnow().isoformat()}
        for wh in hooks:
            try:
                requests.post(wh.url, json=payload, timeout=5)
            except Exception:
                # falha não interrompe o loop; possíveis logs aqui
                continue
    except Exception:
        pass
