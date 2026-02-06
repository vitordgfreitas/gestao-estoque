"""
Corrigir headers duplicados na aba Carros
"""
from sheets_config import init_sheets

def corrigir_headers_carros():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_carros = sheets['sheet_carros']
    
    print("\n[*] Headers atuais:")
    headers = sheet_carros.row_values(1)
    for i, h in enumerate(headers, 1):
        print(f"  Coluna {chr(64+i)}: {h}")
    
    # Headers corretos (sem duplicatas)
    headers_corretos = [
        'ID',
        'Item ID',
        'Placa',
        'Marca',
        'Modelo',
        'Ano'
    ]
    
    print(f"\n[*] Substituindo headers...")
    sheet_carros.update('A1:F1', [headers_corretos])
    
    # Limpa colunas extras se tiver
    if len(headers) > 6:
        print(f"[*] Limpando {len(headers) - 6} colunas extras...")
        sheet_carros.batch_clear([f'G1:{chr(64+len(headers))}1'])
    
    print(f"\n[OK] Headers corrigidos!")
    
    # Verifica
    headers_novos = sheet_carros.row_values(1)
    print(f"\n[*] Headers finais:")
    for i, h in enumerate(headers_novos, 1):
        print(f"  Coluna {chr(64+i)}: {h}")

if __name__ == "__main__":
    try:
        corrigir_headers_carros()
        print("\n[SUCESSO] Headers da aba Carros corrigidos!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
