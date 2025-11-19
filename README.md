# Backend Flask - HubSpot Clicksign Integration

Backend API para gerenciar contas e armazenar API keys do Clicksign.

Para instruções detalhadas de setup, consulte [SETUP.md](./SETUP.md)

## Configuração Rápida

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Configurar variáveis de ambiente:
```bash
cp env.example .env
# Editar .env com suas configurações
```

3. Configurar banco de dados PostgreSQL e executar migrations:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. Rodar o servidor:
```bash
python run.py
```

## Endpoints

### GET /api/account/{portal_id}
Recupera informações da conta e API key do Clicksign.

**Headers:**
- `Authorization: Bearer {BACKEND_API_TOKEN}`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "...",
    "portal_id": "123456",
    "clicksign_api_key": "...",
    "created_at": "...",
    "trial_expires_at": "...",
    "plan_expires_at": null,
    "is_active": true
  }
}
```

### POST /api/account/{portal_id}
Cria nova conta.

**Headers:**
- `Authorization: Bearer {BACKEND_API_TOKEN}`

**Body:**
```json
{
  "clicksign_api_key": "optional"
}
```

### POST /api/account/{portal_id}/clicksign-key
Salva/atualiza API key do Clicksign.

**Headers:**
- `Authorization: Bearer {BACKEND_API_TOKEN}`

**Body:**
```json
{
  "clicksign_api_key": "token-do-clicksign"
}
```

### GET /api/account/{portal_id}/status
Retorna status da conta.

**Headers:**
- `Authorization: Bearer {BACKEND_API_TOKEN}`

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "trial|expired|active",
    "trial_expires_at": "...",
    "plan_expires_at": null,
    "is_active": true
  }
}
```

## Autenticação

Todas as rotas requerem autenticação Bearer token:
```
Authorization: Bearer {BACKEND_API_TOKEN}
```

O token é configurado via variável de ambiente `BACKEND_API_TOKEN`.

