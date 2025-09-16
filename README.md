Leitor de NFSe API
API para extração de dados de Notas Fiscais de Serviço (NFSe) de Fortaleza, utilizando FastAPI, SQLAlchemy, PostgreSQL e OCR com Tesseract. Este projeto processa PDFs de NFSe, extrai informações relevantes (como emitente, tomador, valores e serviços) e armazena os resultados em um banco de dados PostgreSQL. Suporta webhooks para notificações assíncronas.
Estrutura do Projeto
NFSE_Leitor/
├── app/
│   ├── __init__.py
│   ├── main.py              # Ponto de entrada da API FastAPI
│   ├── database.py          # Configuração do banco de dados (SQLAlchemy)
│   ├── config.py            # Configurações (ex: DATABASE_URL, TESSERACT_CMD)
│   ├── models.py            # Modelos SQLAlchemy (Task, Webhook)
│   ├── schemas.py           # Schemas Pydantic para validação
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tasks.py         # Lógica para criação e processamento de tarefas
│   │   ├── webhooks.py      # Lógica para notificação via webhooks
│   │   ├── storage.py       # Gerenciamento de arquivos (upload e remoção)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── tasks.py         # Rotas para upload, status e resultados
│   │   ├── webhooks.py      # Rotas para criação e listagem de webhooks
│   │   ├── health.py        # Rota de health check
│   ├── extractor/
│   │   ├── __init__.py
│   │   ├── base.py          # Classe abstrata para extratores
│   │   ├── fortaleza.py     # Extrator específico para NFSe de Fortaleza
├── .env                     # Variáveis de ambiente (ex: DATABASE_URL)
├── requirements.txt         # Dependências do projeto
├── README.md                # Este arquivo

Requisitos

Sistema Operacional: WSL Ubuntu (ou outro Linux compatível)
Python: 3.13
Gerenciador de Pacotes: UV
PostgreSQL: Versão 15 ou superior
Tesseract: Para OCR de PDFs
Dependências:fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic
opencv-python
numpy
pytesseract
PyMuPDF
pdfplumber
requests
python-dotenv



Configuração do Ambiente
1. Instalar Dependências do Sistema
Instale o PostgreSQL e o Tesseract no WSL Ubuntu:
sudo apt update
sudo apt install -y postgresql postgresql-contrib tesseract-ocr tesseract-ocr-por

2. Configurar o PostgreSQL

Acessar o PostgreSQL como superusuário:
sudo -u postgres psql


Definir a senha do usuário postgres (exemplo: 1324):\password postgres


Digite 1324 quando solicitado.




Criar o usuário nfse_user:
CREATE ROLE nfse_user WITH LOGIN PASSWORD 'senha123' CREATEDB;
\q


Criar o banco nfse_db:
psql -U postgres -h localhost -d postgres


Senha: 1324
Execute:DROP DATABASE IF EXISTS nfse_db;
CREATE DATABASE nfse_db OWNER nfse_user;
\c nfse_db
GRANT ALL ON SCHEMA public TO nfse_user;
ALTER SCHEMA public OWNER TO nfse_user;
\q



Nota: Se houver erro database "nfse_db" is being accessed by other users, encerre conexões ativas:
psql -U postgres -h localhost -d postgres

SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'nfse_db' AND pid <> pg_backend_pid();



3. Configurar o Projeto

Clonar o repositório (se aplicável):
git clone <URL_DO_REPOSITORIO>
cd NFSE_Leitor


Configurar o ambiente virtual com UV:
uv venv
source .venv/bin/activate
uv sync


Configurar o arquivo .env:Crie um arquivo .env na raiz do projeto com:
DATABASE_URL=postgresql://nfse_user:senha123@localhost/nfse_db
TESSERACT_CMD=/usr/bin/tesseract
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
TEMP_DIR=/tmp/nfse_leitor
DATA_DIR=/tmp/nfse_leitor/data


Formatar o código (opcional, para consistência):
uv run black .



4. Iniciar a API
uvicorn app.main:app --reload


A API estará disponível em http://127.0.0.1:8000.

Solução de Problemas
Erro: permission denied for schema public

Causa: O usuário nfse_user não tem permissões suficientes no schema public do banco nfse_db.
Solução:
Conecte-se ao nfse_db:psql -U postgres -h localhost -d nfse_db


Senha: 1324


Conceda permissões:GRANT ALL ON SCHEMA public TO nfse_user;
ALTER SCHEMA public OWNER TO nfse_user;


Reinicie a API:uvicorn app.main:app --reload





Erro: invalid integer value "ON" for connection option "port"

Causa: Problema no cliente psql, possivelmente devido a variáveis de ambiente (PGPORT) ou arquivo .psqlrc.
Solução:
Limpe variáveis de ambiente:unset PGPORT


Remova o arquivo .psqlrc (se existir):rm ~/.psqlrc


Conecte diretamente ao banco:psql -U postgres -h localhost -d nfse_db





Erro: database "nfse_db" is being accessed by other users

Solução:
Encerre conexões ativas:psql -U postgres -h localhost -d postgres

SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'nfse_db' AND pid <> pg_backend_pid();


Drope o banco:DROP DATABASE IF EXISTS nfse_db;


Recrie o banco (veja seção "Configurar o PostgreSQL").



Testar a API

Verificar se a API está rodando:
curl http://127.0.0.1:8000/


Esperado: {"message": "Leitor de NFSe API rodando com PostgreSQL!"}


Testar health check:
curl http://127.0.0.1:8000/health


Esperado: {"status": "healthy"}


Testar upload de NFSe:
curl -X POST -F "file=@caminho/para/seu_arquivo.pdf" http://127.0.0.1:8000/upload-nfse


Substitua caminho/para/seu_arquivo.pdf pelo caminho de um PDF válido.



Estrutura do Banco de Dados
As tabelas são criadas automaticamente pela função init_db() em main.py:

Tabela task:

id: SERIAL PRIMARY KEY
status: VARCHAR (pendente, em andamento, concluída, falha)
data_criacao: TIMESTAMP
data_conclusao: TIMESTAMP
arquivo_pdf: VARCHAR (caminho do arquivo)
json_resultado: TEXT (resultado da extração)
erro_mensagem: TEXT


Tabela webhook:

id: SERIAL PRIMARY KEY
url: VARCHAR (URL do webhook)
actions: VARCHAR (ações que disparam o webhook)



Notas sobre Clean Code

O projeto segue a estrutura modular, separando rotas, serviços e modelos.
Use o Black para formatação consistente:uv run black .


Adicione logs em services/webhooks.py e services/tasks.py para melhorar a depuração (atualmente, exceções são ignoradas com pass).

Contribuições

Para reportar bugs ou sugerir melhorias, crie uma issue no repositório.
Para testes, forneça um PDF de NFSe de Fortaleza para validar a extração.
