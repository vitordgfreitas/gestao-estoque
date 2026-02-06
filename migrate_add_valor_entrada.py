"""
Script de migração para adicionar campo valor_entrada na tabela financiamentos
Execute este script uma única vez para atualizar o banco de dados existente.
"""
import sqlite3
import os

def migrate():
    # Caminho para o banco de dados
    db_paths = [
        'data/estoque.db',
        'backend/data/estoque.db',
        os.path.join(os.path.dirname(__file__), 'data', 'estoque.db'),
        os.path.join(os.path.dirname(__file__), 'backend', 'data', 'estoque.db')
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Banco de dados não encontrado!")
        print("Tentei os seguintes caminhos:")
        for path in db_paths:
            print(f"  - {path}")
        return False
    
    print(f"✅ Banco de dados encontrado em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(financiamentos)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'valor_entrada' in columns:
            print("ℹ️  Coluna 'valor_entrada' já existe. Nenhuma migração necessária.")
            return True
        
        # Adiciona a coluna valor_entrada
        print("🔄 Adicionando coluna 'valor_entrada'...")
        cursor.execute("""
            ALTER TABLE financiamentos 
            ADD COLUMN valor_entrada REAL NOT NULL DEFAULT 0.0
        """)
        
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        print("   - Coluna 'valor_entrada' adicionada à tabela 'financiamentos'")
        print("   - Valor padrão: 0.0 para registros existentes")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro durante migração: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("MIGRAÇÃO: Adicionar campo valor_entrada em financiamentos")
    print("="*60)
    print()
    
    success = migrate()
    
    print()
    if success:
        print("✅ Migração executada com sucesso!")
    else:
        print("❌ Falha na migração. Verifique os erros acima.")
    print("="*60)
