"""
Remover coluna duplicada "Observacoes" da aba Financiamentos
"""
from sheets_config import init_sheets

def remover_colunas_duplicadas():
    print("[*] Conectando ao Google Sheets...")
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_financiamentos = sheets['sheet_financiamentos']
    
    print("[*] Verificando headers...")
    headers = sheet_financiamentos.row_values(1)
    print(f"    Headers atuais: {headers}")
    print(f"    Total de colunas: {len(headers)}")
    
    # Conta duplicados
    from collections import Counter
    duplicados = [item for item, count in Counter(headers).items() if count > 1]
    
    if duplicados:
        print(f"\n[!] Encontrados headers duplicados: {duplicados}")
        
        # Pega apenas as primeiras 11 colunas (sem as duplicatas)
        headers_corretos = [
            'ID',
            'Item ID',
            'Valor Total',
            'Valor Entrada',
            'Numero Parcelas',
            'Valor Parcela',
            'Taxa Juros',
            'Data Inicio',
            'Status',
            'Instituicao Financeira',
            'Observacoes'
        ]
        
        print(f"\n[*] Limpando colunas extras...")
        
        # Limpa as colunas L e M (colunas 12 e 13)
        sheet_financiamentos.batch_clear(['L1:M1'])
        
        # Atualiza só as 11 colunas corretas
        sheet_financiamentos.update('A1:K1', [headers_corretos])
        
        print(f"\n[OK] Colunas duplicadas removidas!")
        
        # Verifica novamente
        headers_novos = sheet_financiamentos.row_values(1)
        print(f"\n[*] Headers finais:")
        for i, h in enumerate(headers_novos, 1):
            print(f"  Coluna {chr(64+i)}: {h}")
        
        print(f"\n[OK] Total de colunas agora: {len(headers_novos)}")
    else:
        print("[OK] Nenhum header duplicado encontrado!")

if __name__ == "__main__":
    try:
        remover_colunas_duplicadas()
        print("\n[SUCESSO] Operacao concluida!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
