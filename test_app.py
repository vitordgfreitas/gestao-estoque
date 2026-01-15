"""Script de teste para verificar se tudo está funcionando"""
import sys
import os

print("=== Teste de Configuração ===")
print(f"Python: {sys.version}")
print(f"Diretório atual: {os.getcwd()}")

# Testar imports
print("\n=== Testando Imports ===")
try:
    import streamlit
    print(f"✅ Streamlit: {streamlit.__version__}")
except ImportError as e:
    print(f"❌ Erro ao importar Streamlit: {e}")
    sys.exit(1)

try:
    import sqlalchemy
    print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ Erro ao importar SQLAlchemy: {e}")
    sys.exit(1)

# Testar modelos
print("\n=== Testando Modelos ===")
try:
    from models import init_db
    init_db()
    print("✅ Banco de dados inicializado com sucesso")
except Exception as e:
    print(f"❌ Erro ao inicializar banco de dados: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Testar database
print("\n=== Testando Database ===")
try:
    import database as db
    itens = db.listar_itens()
    print(f"✅ Database funcionando. Itens cadastrados: {len(itens)}")
except Exception as e:
    print(f"❌ Erro ao acessar database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Todos os testes passaram! A aplicação deve funcionar.")
print("\nPara iniciar, execute: streamlit run app.py")
