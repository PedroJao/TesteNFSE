from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from .database import Base

class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pendente", nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_conclusao = Column(DateTime, nullable=True)
    arquivo_pdf = Column(String, nullable=True)
    json_resultado = Column(Text, nullable=True)
    erro_mensagem = Column(Text, nullable=True)

class Webhook(Base):
    __tablename__ = "webhook"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    actions = Column(String, nullable=False)  # ex: "upload,conclusao"
