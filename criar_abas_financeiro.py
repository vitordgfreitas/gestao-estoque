"""
Script para criar as abas de Contas a Receber e Contas a Pagar no Google Sheets
Execute este script para garantir que as abas sejam criadas
"""
import os
import sys

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

try:
    from sheets_config import init_sheets
    
    print("=" * 60)
    print("Criando abas de Contas a Receber e Contas a Pagar")
    print("=" * 60)
    
    # Obtém o ID da planilha
    spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
    if not spreadsheet_id:
        spreadsheet_id = "1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE"
        print(f"[AVISO] GOOGLE_SHEET_ID nao configurado. Usando ID padrao: {spreadsheet_id}")
    
    print(f"\nInicializando planilhas...")
    print(f"   ID da Planilha: {spreadsheet_id}")
    
    # Inicializa as planilhas (isso cria as abas se não existirem)
    sheets = init_sheets(spreadsheet_id, "Gestao de Estoque")
    
    print(f"\n[OK] Abas criadas/verificadas com sucesso!")
    print(f"   URL da Planilha: {sheets.get('spreadsheet_url', 'N/A')}")
    print(f"\nAbas disponiveis:")
    
    spreadsheet = sheets.get('spreadsheet')
    if spreadsheet:
        for ws in spreadsheet.worksheets():
            print(f"   - {ws.title}")
    
    print("\n" + "=" * 60)
    print("[OK] Processo concluido!")
    print("=" * 60)
    
except FileNotFoundError as e:
    print(f"\n[ERRO] Arquivo credentials.json nao encontrado!")
    print(f"   Por favor, coloque o arquivo credentials.json na raiz do projeto.")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERRO] Erro ao criar abas: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
