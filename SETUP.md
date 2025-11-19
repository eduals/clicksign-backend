# Setup do Backend Flask

## Pré-requisitos

- Python 3.8+
- PostgreSQL 12+
- pip (gerenciador de pacotes Python)

## Instalação

1. **Instalar dependências:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configurar banco de dados PostgreSQL:**
   - Criar banco de dados:
   ```sql
   CREATE DATABASE clicksign_db;
   ```
   - Ou usar um banco existente

3. **Configurar variáveis de ambiente:**
```bash
cp env.example .env
```

Editar o arquivo `.env` com suas configurações:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/clicksign_db
SECRET_KEY=sua-chave-secreta-aqui
BACKEND_API_TOKEN=seu-token-de-autenticacao-aqui
FLASK_ENV=development
```

4. **Inicializar migrations:**
```bash
flask db init
flask db migrate -m "Initial migration - create accounts table"
flask db upgrade
```

5. **Rodar o servidor:**
```bash
python run.py
```

O servidor estará rodando em `http://localhost:5000`

## Configuração no Frontend HubSpot

Após configurar o backend, atualize a URL e o token no frontend:

1. **Editar `hubspot/src/app/cards/backendApi.ts`:**
   - Alterar `BACKEND_URL` para a URL do seu backend
   - Alterar `BACKEND_API_TOKEN` para o mesmo token configurado no `.env`

2. **Editar `hubspot/src/app/settings/backendApi.ts`:**
   - Fazer as mesmas alterações acima

3. **Atualizar `hubspot/src/app/app-hsmeta.json`:**
   - Adicionar a URL do backend em `permittedUrls.fetch` (já está configurado com localhost e placeholder)

## Testando a API

### Criar uma conta:
```bash
curl -X POST http://localhost:5000/api/account/123456 \
  -H "Authorization: Bearer seu-token-aqui" \
  -H "Content-Type: application/json" \
  -d '{"clicksign_api_key": "token-do-clicksign"}'
```

### Buscar conta:
```bash
curl -X GET http://localhost:5000/api/account/123456 \
  -H "Authorization: Bearer seu-token-aqui"
```

### Salvar API key:
```bash
curl -X POST http://localhost:5000/api/account/123456/clicksign-key \
  -H "Authorization: Bearer seu-token-aqui" \
  -H "Content-Type: application/json" \
  -d '{"clicksign_api_key": "novo-token"}'
```

### Verificar status:
```bash
curl -X GET http://localhost:5000/api/account/123456/status \
  -H "Authorization: Bearer seu-token-aqui"
```

## Estrutura do Banco de Dados

A tabela `accounts` será criada automaticamente com as migrations. Estrutura:

- `id` (UUID, PK)
- `portal_id` (VARCHAR, UNIQUE) - ID do portal HubSpot
- `clicksign_api_key` (TEXT) - API key do Clicksign
- `created_at` (TIMESTAMP) - Data de criação
- `trial_expires_at` (TIMESTAMP) - Expiração do trial (20 dias)
- `plan_expires_at` (TIMESTAMP, NULLABLE) - Expiração do plano
- `is_active` (BOOLEAN) - Status ativo/inativo
- `updated_at` (TIMESTAMP) - Última atualização

## Produção

Para produção:

1. Use variáveis de ambiente seguras
2. Configure HTTPS
3. Use um servidor WSGI (ex: Gunicorn)
4. Configure CORS adequadamente
5. Use um banco de dados gerenciado (ex: AWS RDS, Heroku Postgres)
6. Configure logs e monitoramento

