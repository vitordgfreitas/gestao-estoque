"""
Script para verificar a configuração do Google Sheets
"""
import os
import sys

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

print("=" * 60)
print("  VERIFICAÇÃO DE CONFIGURAÇÃO - GOOGLE SHEETS")
print("=" * 60)
print()

# 1. Verificar arquivo credentials.json
print("1. Verificando arquivo credentials.json...")
credentials_path = os.path.join(root_dir, 'credentials.json')
if os.path.exists(credentials_path):
    print(f"   [OK] credentials.json encontrado em: {credentials_path}")
else:
    print(f"   [ERRO] credentials.json NAO encontrado em: {credentials_path}")
    print("   Verifique se o arquivo está na raiz do projeto")
print()

# 2. Verificar variável de ambiente
print("2. Verificando variável de ambiente USE_GOOGLE_SHEETS...")
use_google_sheets = os.getenv('USE_GOOGLE_SHEETS', 'true').lower() == 'true'
print(f"   USE_GOOGLE_SHEETS = {use_google_sheets}")
print()

# 3. Tentar importar e conectar ao Google Sheets
if use_google_sheets:
    print("3. Tentando conectar ao Google Sheets...")
    try:
        import sheets_config
        import sheets_database
        
        # Tentar obter cliente
        client = sheets_config.get_sheets_client()
        print("   [OK] Cliente Google Sheets criado com sucesso")
        
        # Tentar obter informações da planilha
        try:
            sheets_info = sheets_database.get_sheets()
            spreadsheet_url = sheets_info.get('spreadsheet_url', 'N/A')
            spreadsheet_id = sheets_info.get('spreadsheet_id', 'N/A')
            print(f"   [OK] Planilha conectada: {spreadsheet_url}")
            print(f"   [OK] ID da Planilha: {spreadsheet_id}")
            
            # Tentar listar itens
            print()
            print("4. Testando leitura de dados...")
            try:
                itens = sheets_database.listar_itens()
                print(f"   [OK] {len(itens)} itens encontrados no Google Sheets")
                
                if len(itens) > 0:
                    print()
                    print("   Primeiros 3 itens:")
                    for i, item in enumerate(itens[:3], 1):
                        print(f"   {i}. {item.nome} (ID: {item.id})")
                else:
                    print("   [AVISO] Nenhum item encontrado na planilha")
                    
            except Exception as e:
                print(f"   [ERRO] Erro ao listar itens: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Tentar listar compromissos
            try:
                compromissos = sheets_database.listar_compromissos()
                print(f"   [OK] {len(compromissos)} compromissos encontrados no Google Sheets")
            except Exception as e:
                print(f"   [ERRO] Erro ao listar compromissos: {str(e)}")
                
        except Exception as e:
            print(f"   [ERRO] Erro ao conectar a planilha: {str(e)}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"   [ERRO] Erro ao importar modulos: {str(e)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"   [ERRO] Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print("3. Google Sheets desabilitado (USE_GOOGLE_SHEETS=false)")
    print("   O sistema usará SQLite local")

print()
print("=" * 60)
print("  VERIFICAÇÃO CONCLUÍDA")
print("=" * 60)
