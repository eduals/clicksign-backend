# Migrations

Para configurar as migrations do Alembic:

1. Inicializar migrations (apenas na primeira vez):
```bash
flask db init
```

2. Criar migration:
```bash
flask db migrate -m "Initial migration - create accounts table"
```

3. Aplicar migration:
```bash
flask db upgrade
```

4. Reverter migration (se necessário):
```bash
flask db downgrade
```

## Nota

As migrations serão criadas automaticamente quando você executar os comandos acima pela primeira vez. O diretório `migrations/` será criado automaticamente.

