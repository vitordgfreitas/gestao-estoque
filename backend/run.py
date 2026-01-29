"""
Script para rodar o servidor FastAPI
"""
import uvicorn
import os
import sys

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Carrega variáveis de ambiente do arquivo .env se existir
try:
    from dotenv import load_dotenv
    env_path = os.path.join(root_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    # Também tenta carregar .env do backend
    backend_env = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
except ImportError:
    pass  # python-dotenv não instalado, continua sem ele

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 Iniciando servidor FastAPI na porta {port}")
    print(f"📁 Diretório raiz: {root_dir}")
    print(f"🌐 Acesse: http://localhost:{port}")
    print(f"📚 Docs: http://localhost:{port}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
