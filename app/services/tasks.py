import json
import traceback
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from .. import models, schemas
from ..database import SessionLocal
from ..services import storage, webhooks as webhook_service
from ..extractor.fortaleza import FortalezaNFSeExtractor
from datetime import datetime

extractor = FortalezaNFSeExtractor()

def create_task(background_tasks: BackgroundTasks, upload_file) -> dict:
    """Cria a task no banco, salva arquivo e agenda processamento em background."""
    db: Session = SessionLocal()
    file_path = None
    try:
        file_path = storage.save_upload_file(upload_file)
        task = models.Task(status="pendente", arquivo_pdf=file_path, data_criacao=datetime.utcnow())
        db.add(task)
        db.commit()
        db.refresh(task)
        # agenda background
        background_tasks.add_task(process_task, task.id)
        # notificar upload (async)
        background_tasks.add_task(webhook_service.notify_webhooks_for_action, db, "upload", task.id)
        return {"task_id": task.id}
    except Exception as e:
        if file_path:
            storage.remove_file(file_path)
        raise
    finally:
        db.close()

def process_task(task_id: int):
    """Função executada em background: lê task do DB, roda extrator e atualiza DB."""
    db: Session = SessionLocal()
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            return
        task.status = "em andamento"
        db.commit()
        try:
            extracted = extractor.extract(task.arquivo_pdf)
            task.json_resultado = json.dumps(extracted, ensure_ascii=False)
            task.status = "concluída"
            task.data_conclusao = datetime.utcnow()
        except Exception as exc:
            task.status = "falha"
            task.erro_mensagem = f"{str(exc)}\n{traceback.format_exc()}"
        db.commit()
        # notify
        webhook_service.notify_webhooks_for_action(db, "conclusao", task_id)
    finally:
        # cleanup
        if task and task.arquivo_pdf:
            storage.remove_file(task.arquivo_pdf)
        db.close()

def get_status(task_id: int) -> dict:
    db: Session = SessionLocal()
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            return None
        return {
            "task_id": task.id,
            "status": task.status,
            "data_criacao": task.data_criacao,
            "data_conclusao": task.data_conclusao
        }
    finally:
        db.close()

def get_result(task_id: int):
    db: Session = SessionLocal()
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            return None
        if not task.json_resultado:
            return None
        return json.loads(task.json_resultado)
    finally:
        db.close()
