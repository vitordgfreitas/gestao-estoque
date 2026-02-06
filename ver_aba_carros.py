"""
Ver como os dados estao no Google Sheets - aba Carros
"""
from sheets_config import init_sheets

def ver_aba_carros():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_carros = sheets['sheet_Carros']
    
    print("\n[*] Headers da aba Carros:")
    headers = sheet_carros.row_values(1)
    for i, h in enumerate(headers, 1):
        print(f"  Coluna {chr(64+i)}: {h}")
    
    print("\n[*] Primeiras 10 linhas de dados:")
    all_values = sheet_carros.get_all_values()
    for i, row in enumerate(all_values[:11], 1):  # Header + 10 linhas
        if i == 1:
            print(f"  Linha {i} (HEADER): {row}")
        else:
            print(f"  Linha {i}: {row}")

if __name__ == "__main__":
    try:
        ver_aba_carros()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
