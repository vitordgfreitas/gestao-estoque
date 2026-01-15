# Guia de Solução de Problemas

## Erro: ERR_CONNECTION_REFUSED

Se você está vendo "ERR_CONNECTION_REFUSED" ao tentar acessar `http://localhost:8501`, siga estes passos:

### 1. Verificar se a aplicação está rodando

Abra um terminal e verifique se há um processo Streamlit rodando:
```bash
# Windows PowerShell
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*streamlit*"}
```

### 2. Verificar se a porta 8501 está em uso

```bash
# Windows PowerShell
netstat -ano | findstr :8501
```

Se a porta estiver em uso, você pode:
- Parar o processo que está usando a porta
- Ou usar outra porta: `streamlit run app.py --server.port=8502`

### 3. Verificar se o ambiente virtual está configurado

Execute o script de teste:
```bash
check.bat
```

Ou manualmente:
```bash
env\Scripts\python test_app.py
```

### 4. Verificar se as dependências estão instaladas

```bash
env\Scripts\pip list
```

Você deve ver:
- streamlit
- sqlalchemy

Se não estiverem instaladas:
```bash
env\Scripts\pip install -r requirements.txt
```

### 5. Tentar iniciar manualmente

```bash
# Ativar ambiente virtual
env\Scripts\activate

# Rodar aplicação
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

### 6. Verificar logs de erro

Quando executar `make api` ou `run.bat`, observe se há mensagens de erro no terminal. Erros comuns:

- **"ModuleNotFoundError"**: Dependências não instaladas → Execute `make install`
- **"Port already in use"**: Porta ocupada → Use outra porta ou pare o processo
- **"Permission denied"**: Problema de permissões → Execute como administrador

### 7. Verificar firewall

O Windows Firewall pode estar bloqueando a conexão. Tente desabilitar temporariamente para testar.

### 8. Tentar com IP específico

Em vez de `localhost`, tente:
- `http://127.0.0.1:8501`
- `http://0.0.0.0:8501`

### 9. Reinstalar ambiente virtual

Se nada funcionar, tente recriar o ambiente:

```bash
# Remover ambiente antigo
rmdir /s /q env

# Recriar
make setup

# Rodar
make run
```

### 10. Verificar versão do Python

O sistema requer Python 3.8 ou superior:

```bash
python --version
```

Se a versão for inferior, instale uma versão mais recente do Python.

## Mensagens de Sucesso

Quando a aplicação iniciar corretamente, você verá algo como:

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Se você ver essa mensagem mas ainda não conseguir acessar, o problema pode ser:
- Firewall bloqueando
- Antivírus interferindo
- Proxy configurado no navegador
