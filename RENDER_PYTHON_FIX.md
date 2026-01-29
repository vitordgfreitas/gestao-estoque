# Correção: Erro SQLAlchemy com Python 3.13

## Problema
```
AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly but has additional attributes
```

Este erro acontece porque **SQLAlchemy 2.0.23 não é compatível com Python 3.13**.

## Solução Rápida

### Opção 1: Forçar Python 3.11 no Render (RECOMENDADO)

1. **No painel do Render:**
   - Vá em **Settings** do serviço `crm-backend`
   - Encontre **"Python Version"** ou **"Environment"**
   - Selecione **Python 3.11** (não 3.13!)
   - Salve

2. **Ou use o arquivo `runtime.txt`:**
   - O arquivo `backend/runtime.txt` já foi criado com `python-3.11.0`
   - Faça commit e push:
     ```bash
     git add backend/runtime.txt
     git commit -m "Force Python 3.11"
     git push origin main
     ```

### Opção 2: Atualizar SQLAlchemy (já feito)

O `requirements.txt` foi atualizado para SQLAlchemy 2.0.36 que tem melhor compatibilidade.

## Verificação

Após configurar Python 3.11:
- ✅ Build deve completar sem erros
- ✅ Serviço deve iniciar corretamente
- ✅ Não deve mais aparecer o erro de AssertionError

## Por que Python 3.11?

- Python 3.13 é muito novo (lançado em outubro de 2024)
- Muitas bibliotecas ainda não têm suporte completo
- SQLAlchemy 2.0.23 tem problemas conhecidos com Python 3.13
- Python 3.11 é estável e tem excelente suporte

## Próximos Passos

1. Configure Python 3.11 no Render (Settings → Python Version)
2. Ou faça commit do `runtime.txt` e push
3. Aguarde o deploy automático
4. Verifique se está funcionando
