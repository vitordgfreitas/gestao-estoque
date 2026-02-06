"""
FORÇAR correção dos headers da aba Carros
"""
from sheets_config import init_sheets

def forcar_correcao_carros():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_carros = sheets['sheet_carros']
    
    print("\n[*] Limpando TODA a linha 1 (headers)...")
    sheet_carros.batch_clear(['A1:Z1'])
    
    print("\n[*] Escrevendo headers corretos...")
    headers_corretos = [
        'ID',          # A
        'Item ID',     # B
        'Placa',       # C
        'Chassi',      # D
        'Renavam',     # E
        'Marca',       # F
        'Modelo',      # G
        'Ano'          # H
    ]
    
    # Atualiza header por header para garantir
    for i, header in enumerate(headers_corretos, 1):
        col_letter = chr(64 + i)
        sheet_carros.update(f'{col_letter}1', [[header]])
        print(f"  {col_letter}1 = {header}")
    
    print("\n[OK] Headers escritos!")
    
    # Verifica
    import time
    time.sleep(2)  # Aguarda 2s para o Google Sheets processar
    
    headers_verificacao = sheet_carros.row_values(1)
    print(f"\n[*] Verificacao final ({len(headers_verificacao)} colunas):")
    for i, h in enumerate(headers_verificacao, 1):
        print(f"  Coluna {chr(64+i)}: [{h}]")
    
    # Verifica duplicatas
    from collections import Counter
    duplicados = [item for item, count in Counter(headers_verificacao).items() if count > 1 and item]
    if duplicados:
        print(f"\n[ERRO] Ainda tem duplicados: {duplicados}")
    else:
        print(f"\n[OK] Nenhum header duplicado!")

if __name__ == "__main__":
    try:
        forcar_correcao_carros()
        print("\n[SUCESSO] Headers corrigidos!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
