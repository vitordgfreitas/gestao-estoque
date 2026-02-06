"""
Verificar o estado da aba Financiamentos no Google Sheets
"""
from sheets_config import init_sheets

def verificar_financiamentos():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_financiamentos = sheets['sheet_financiamentos']
    
    print("\n[*] Headers:")
    headers = sheet_financiamentos.row_values(1)
    for i, h in enumerate(headers, 1):
        print(f"  Coluna {chr(64+i)}: {h}")
    
    print("\n[*] Dados:")
    all_values = sheet_financiamentos.get_all_values()
    print(f"  Total de linhas: {len(all_values)}")
    
    if len(all_values) > 1:
        print("\n[*] Primeiras 5 linhas de dados:")
        for i, row in enumerate(all_values[1:6], 2):  # Pula header
            print(f"  Linha {i}: {row}")
    else:
        print("  [OK] Nenhum financiamento cadastrado ainda.")
    
    # Verifica se 'Valor Entrada' existe
    if 'Valor Entrada' in headers:
        col_idx = headers.index('Valor Entrada')
        print(f"\n[OK] Coluna 'Valor Entrada' encontrada na posicao {col_idx+1} (coluna {chr(65+col_idx)})")
    else:
        print("\n[ERRO] Coluna 'Valor Entrada' NAO encontrada!")

if __name__ == "__main__":
    try:
        verificar_financiamentos()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
