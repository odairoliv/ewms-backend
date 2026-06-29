# EWMS Backend

API REST em FastAPI (Python) para o sistema EWMS, em camadas:

```
app/
  controllers/   -> recebe requisições HTTP, valida entrada, chama o service certo
  services/      -> regras de negócio, RBAC, cálculo de horas/valor, auditoria
  repositories/  -> única camada que conversa com o banco (SQLAlchemy)
  models/        -> entidades ORM (tabelas)
  schemas/       -> DTOs Pydantic (entrada/saída da API)
  core/          -> config, conexão com banco, segurança/JWT
```

## Opção A — Docker Compose (recomendado)

Sobe a API e o Postgres juntos, sem precisar instalar Python nem Postgres na máquina.

Pré-requisito: Docker Desktop instalado e rodando.

1. Copiar `.env.example` para `.env` (os valores padrão já funcionam com o `docker-compose.yml`):
   ```
   copy .env.example .env
   ```
2. Subir os containers (primeira vez cria o banco e as tabelas automaticamente via `scripts/create_database_postgres.sql`):
   ```
   docker compose up --build
   ```
3. Em outro terminal, popular dados de teste (6 empresas, usuários, fornecedores, consultores e apontamentos de exemplo):
   ```
   docker compose exec backend python -m scripts.seed
   ```
4. Documentação interativa: http://localhost:8000/docs

Para rodar novamente depois da primeira vez: `docker compose up`.
Para resetar o banco do zero: `docker compose down -v && docker compose up --build` (o `-v` remove o volume do Postgres).

## Opção B — Python local

- Python 3.12+
- PostgreSQL rodando localmente na porta 5432

1. Criar e ativar o ambiente virtual (Windows/PowerShell):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
2. Instalar dependências:
   ```
   pip install -r requirements.txt
   ```
3. Copiar `.env.example` para `.env` e ajustar usuário/senha do Postgres:
   ```
   copy .env.example .env
   ```
4. Criar o banco e as tabelas:
   ```
   psql -U postgres -c "CREATE DATABASE ewms;"
   psql -U postgres -d ewms -f scripts/create_database_postgres.sql
   ```
5. Popular dados de teste (6 empresas, usuários, fornecedores, consultores e apontamentos de exemplo):
   ```
   python -m scripts.seed
   ```
6. Rodar o servidor:
   ```
   uvicorn app.main:app --reload --port 8000
   ```
7. Documentação interativa: http://localhost:8000/docs

Para rodar novamente depois da primeira vez, em uma nova sessão de terminal dentro de `ewms-backend`:
```
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

## Usuários de teste (após `python -m scripts.seed`)

| Email | Senha | Perfil | Empresa |
|---|---|---|---|
| super@ewms.com | super123 | SuperUsuario | EWMS Sistemas |
| admin@ewms.com | admin123 | Administrador | Cliente Demo S.A. |
| lider@ewms.com | lider123 | Liderança | Cliente Demo S.A. |
| fornecedor@ewms.com | fornecedor123 | Fornecedor | Cliente Demo S.A. |
| usuario@ewms.com | usuario123 | Usuário | Cliente Demo S.A. |

O seed também cria mais 4 empresas-cliente (Banco Horizonte S.A., Varejo Estrela LTDA, Indústria Atlas LTDA, Saúde Vitalis S.A.) com seus próprios usuários, fornecedores e consultores, usadas para validar o isolamento multi-tenant e a visão cross-tenant do SuperUsuario.

## Integração com o frontend

O frontend espera a API em `http://localhost:8000/api` (configurável via `VITE_API_BASE_URL` no `.env` do `ewms-frontend`). Todos os endpoints implementados estão sob esse prefixo `/api`. O backend precisa estar rodando **antes** de abrir o frontend, ou o login falhará.

## Resetar o banco do zero

Com Docker Compose: `docker compose down -v && docker compose up --build`, depois `docker compose exec backend python -m scripts.seed`.

Com Postgres local: recrie o banco e rode o schema de novo:
```
psql -U postgres -c "DROP DATABASE ewms;"
psql -U postgres -c "CREATE DATABASE ewms;"
psql -U postgres -d ewms -f scripts/create_database_postgres.sql
python -m scripts.seed
```
Isso apaga e recria todas as tabelas — só use em ambiente de desenvolvimento local.
