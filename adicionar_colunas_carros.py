"""
Adicionar colunas Chassi e Renavam na aba Carros
"""
from sheets_config import init_sheets

def adicionar_colunas_carros():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_carros = sheets['sheet_carros']
    
    print("\n[*] Headers atuais:")
    headers = sheet_carros.row_values(1)
    print(f"  {headers}")
    
    # Headers corretos COM Chassi e Renavam
    headers_corretos = [
        'ID',          # A
        'Item ID',     # B
        'Placa',       # C
        'Chassi',      # D <- NOVO
        'Renavam',     # E <- NOVO
        'Marca',       # F (era D antes)
        'Modelo',      # G (era E antes)
        'Ano'          # H (era F antes)
    ]
    
    print(f"\n[*] Estrutura correta (8 colunas):")
    for i, h in enumerate(headers_corretos, 1):
        print(f"  Coluna {chr(64+i)}: {h}")
    
    print(f"\n[*] Atualizando headers...")
    sheet_carros.update('A1:H1', [headers_corretos])
    
    print(f"\n[OK] Headers atualizados!")
    
    # Mostra como ficou
    print(f"\n[*] Primeira linha de dados (exemplo):")
    linha2 = sheet_carros.row_values(2)
    for i, (header, valor) in enumerate(zip(headers_corretos, linha2), 1):
        print(f"  {chr(64+i)} - {header}: {valor}")

if __name__ == "__main__":
    try:
        adicionar_colunas_carros()
        print("\n[SUCESSO] Estrutura da aba Carros corrigida!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
