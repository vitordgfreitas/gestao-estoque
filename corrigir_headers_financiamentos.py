"""
Corrigir headers da aba Financiamentos e adicionar Valor Entrada
"""
from sheets_config import init_sheets

def corrigir_headers_financiamentos():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_financiamentos = sheets['sheet_financiamentos']
    
    # Headers corretos na ordem certa
    headers_corretos = [
        'ID',
        'Item ID',
        'Valor Total',
        'Valor Entrada',  # NOVO
        'Numero Parcelas',
        'Valor Parcela',
        'Taxa Juros',
        'Data Inicio',
        'Status',
        'Instituicao Financeira',
        'Observacoes'
    ]
    
    print(f"\n[*] Substituindo headers da linha 1...")
    print(f"    Headers corretos: {headers_corretos}")
    
    # Atualiza a linha de headers
    sheet_financiamentos.update('A1:K1', [headers_corretos])
    
    print(f"\n[OK] Headers atualizados com sucesso!")
    
    # Verifica
    headers_novos = sheet_financiamentos.row_values(1)
    print(f"\n[*] Headers atuais:")
    for i, h in enumerate(headers_novos, 1):
        print(f"  Coluna {chr(64+i)}: {h}")

if __name__ == "__main__":
    try:
        corrigir_headers_financiamentos()
        print("\n[SUCESSO] Headers corrigidos!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
