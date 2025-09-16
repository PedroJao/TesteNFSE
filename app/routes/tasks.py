from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from ..schemas import TaskCreateResponse, TaskResponse
from ..services import tasks as task_service
from ..database import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/upload-nfse", response_model=TaskCreateResponse)
async def upload_nfse(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # validações básicas
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ter extensão .pdf")
    return task_service.create_task(background_tasks, file)

@router.get("/status/{task_id}", response_model=TaskResponse)
def get_status(task_id: int):
    status = task_service.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    # devolve campos similares ao schema
    return {
        "id": status["task_id"],
        "status": status["status"],
        "data_criacao": status["data_criacao"],
        "data_conclusao": status["data_conclusao"],
        "arquivo_pdf": None,
        "erro_mensagem": None
    }

@router.get("/result/{task_id}")
def get_result(task_id: int):
    result = task_service.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resultado não disponível")
    return result
