"""
Ver todas as abas disponiveis
"""
from sheets_config import init_sheets

def listar_abas():
    print("[*] Conectando ao Google Sheets...")
    sheets_dict = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    
    print("\n[*] Abas disponiveis:")
    for key in sheets_dict.keys():
        print(f"  - {key}")

if __name__ == "__main__":
    try:
        listar_abas()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
