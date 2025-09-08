# mini-royale-backend

API FastAPI do jogo Mini Royale Aventura.

## Como rodar localmente

1. Instale as dependências:

2. Configure o arquivo `.env` com sua string MongoDB (MONGO_URL) e nome do banco (DB_NAME).

3. Execute o servidor:

4. Acesse a documentação automática:

## Endpoints principais

- `GET /api/v1/perfil/{player_id}` – Consulta perfil do jogador
- `POST /api/v1/match/start` – Inicia uma partida
- `PATCH /api/v1/perfil/{player_id}` – Atualiza vida/gems

## Estrutura de arquivos

- `.env` – Configurações secretas
- `backend_full.py` – Código principal da API
- `requirements.txt` – Pacotes necessários

## Observações

- Recomenda-se usar Python 3.9+.
- Para deploy, consulte documentação do Render, Heroku etc.

