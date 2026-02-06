"""
Corrigir estrutura da aba Financiamentos com Valor Entrada
"""
from sheets_config import init_sheets

def corrigir_financiamentos():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_fin = sheets['sheet_financiamentos']
    
    print("\n[*] Headers atuais:")
    headers = sheet_fin.row_values(1)
    for i, h in enumerate(headers, 1):
        print(f"  Coluna {chr(64+i)}: [{h}]")
    
    print("\n[*] Dados da linha 2 (antes):")
    linha2_antes = sheet_fin.row_values(2)
    print(f"  {linha2_antes}")
    
    # Verifica se já tem Valor Entrada
    if 'Valor Entrada' in headers:
        print("\n[OK] Coluna 'Valor Entrada' ja existe!")
        return
    
    print("\n[*] Inserindo coluna D para 'Valor Entrada'...")
    # Insere uma coluna vazia na posição D (depois de C)
    sheet_fin.insert_cols([[]], col=4)
    
    print("[*] Atualizando header D1...")
    sheet_fin.update('D1', [['Valor Entrada']])
    
    # Preenche com 0.0 para todos os registros existentes
    num_rows = len(sheet_fin.get_all_values())
    if num_rows > 1:
        print(f"[*] Preenchendo {num_rows-1} linhas com 0.0...")
        valores_default = [[0.0] for _ in range(num_rows - 1)]
        sheet_fin.update(f'D2:D{num_rows}', valores_default)
    
    print("\n[OK] Coluna inserida!")
    
    # Verifica
    import time
    time.sleep(2)
    
    headers_novos = sheet_fin.row_values(1)
    print(f"\n[*] Headers finais:")
    for i, h in enumerate(headers_novos, 1):
        print(f"  Coluna {chr(64+i)}: [{h}]")
    
    print("\n[*] Dados da linha 2 (depois):")
    linha2_depois = sheet_fin.row_values(2)
    print(f"  {linha2_depois}")

if __name__ == "__main__":
    try:
        corrigir_financiamentos()
        print("\n[SUCESSO] Estrutura corrigida!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
