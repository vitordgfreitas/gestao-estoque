"""
Script de migração para:
1. Criar tabela pecas_carros
2. Adicionar categoria "Peças de Carro"
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
        # 1. Verifica se a tabela pecas_carros já existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pecas_carros'")
        if cursor.fetchone():
            print("ℹ️  Tabela 'pecas_carros' já existe.")
        else:
            print("🔄 Criando tabela 'pecas_carros'...")
            cursor.execute("""
                CREATE TABLE pecas_carros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    peca_id INTEGER NOT NULL,
                    carro_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL DEFAULT 1,
                    data_instalacao DATE,
                    observacoes VARCHAR(500),
                    FOREIGN KEY (peca_id) REFERENCES itens (id),
                    FOREIGN KEY (carro_id) REFERENCES itens (id)
                )
            """)
            print("✅ Tabela 'pecas_carros' criada com sucesso!")
        
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        print()
        print("Próximos passos:")
        print("1. A categoria 'Peças de Carro' será adicionada automaticamente ao sistema")
        print("2. Você pode começar a cadastrar peças usando esta categoria")
        print("3. Use a nova página 'Peças em Carros' para associar peças a carros")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro durante migração: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("MIGRAÇÃO: Criar tabela pecas_carros e adicionar categoria")
    print("="*60)
    print()
    
    success = migrate()
    
    print()
    if success:
        print("✅ Migração executada com sucesso!")
    else:
        print("❌ Falha na migração. Verifique os erros acima.")
    print("="*60)
