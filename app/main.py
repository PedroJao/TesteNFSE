from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from .database import Base, engine
from .routes import tasks, webhooks, health
from .config import DATABASE_URL

import re
import psycopg2

def init_db():
    """Cria o banco e as tabelas se não existirem, e concede permissões necessárias."""
    try:
        # Tenta criar as tabelas diretamente
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        # Se o banco não existir, cria
        match = re.match(r"postgresql:\/\/(.+):(.+)@(.+)\/(.+)", DATABASE_URL)
        if not match:
            raise ValueError("DATABASE_URL inválido")
        user, password, host, dbname = match.groups()
        
        # Conecta ao banco padrão 'postgres' para criar o novo banco
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Verifica se o banco já existe
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{dbname}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f'CREATE DATABASE "{dbname}"')
        
        # Fecha a conexão inicial
        cur.close()
        conn.close()

        # Conecta ao novo banco para garantir permissões
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Garante permissões completas no schema public
        cur.execute(f"GRANT ALL ON SCHEMA public TO {user};")
        cur.execute(f"ALTER SCHEMA public OWNER TO {user};")
        
        cur.close()
        conn.close()

        # Tenta criar as tabelas novamente
        Base.metadata.create_all(bind=engine)

# Inicializa banco ao subir API
init_db()

# Instância FastAPI
app = FastAPI(title="Leitor de NFSe API")

# Inclui rotas
app.include_router(tasks.router)
app.include_router(webhooks.router)
app.include_router(health.router)

@app.get("/")
def root():
    return {"message": "Leitor de NFSe API rodando com PostgreSQL!"}