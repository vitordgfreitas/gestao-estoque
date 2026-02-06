"""
FORÇAR correção dos headers da aba Financiamentos
"""
from sheets_config import init_sheets

def forcar_correcao_financiamentos():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_fin = sheets['sheet_financiamentos']
    
    print("\n[*] Limpando TODA a linha 1...")
    sheet_fin.batch_clear(['A1:Z1'])
    
    print("\n[*] Escrevendo headers corretos...")
    headers_corretos = [
        'ID',                        # A
        'Item ID',                   # B
        'Valor Total',               # C
        'Valor Entrada',             # D <- IMPORTANTE
        'Numero Parcelas',           # E
        'Valor Parcela',             # F
        'Taxa Juros',                # G
        'Data Inicio',               # H
        'Status',                    # I
        'Instituicao Financeira',    # J
        'Observacoes'                # K (UMA SÓ)
    ]
    
    # Escreve header por header
    for i, header in enumerate(headers_corretos, 1):
        col_letter = chr(64 + i)
        sheet_fin.update(f'{col_letter}1', [[header]])
        print(f"  {col_letter}1 = {header}")
    
    print("\n[OK] Headers escritos!")
    
    # Aguarda e verifica
    import time
    time.sleep(2)
    
    headers_verificacao = sheet_fin.row_values(1)
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
        forcar_correcao_financiamentos()
        print("\n[SUCESSO] Aba Financiamentos corrigida!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
