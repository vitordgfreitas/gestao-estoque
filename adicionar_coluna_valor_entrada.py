"""
Script para adicionar a coluna "Valor Entrada" na aba Financiamentos do Google Sheets
"""
from sheets_config import init_sheets
import gspread

def adicionar_coluna_valor_entrada():
    print("[*] Adicionando coluna 'Valor Entrada' na aba Financiamentos...")
    
    # Inicializa as planilhas
    sheets = init_sheets(spreadsheet_id='1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE')
    sheet_financiamentos = sheets['sheet_financiamentos']
    
    # Pega os headers atuais
    headers = sheet_financiamentos.row_values(1)
    print(f"Headers atuais: {headers}")
    
    # Verifica se a coluna já existe
    if 'Valor Entrada' in headers:
        print("[OK] Coluna 'Valor Entrada' ja existe!")
        return
    
    # Encontra a posição correta (depois de "Valor Total")
    if 'Valor Total' in headers:
        pos = headers.index('Valor Total') + 2  # +2 porque é 1-indexed e queremos DEPOIS
        print(f"[*] Inserindo coluna 'Valor Entrada' na posicao {pos} (coluna {chr(64+pos)})")
        
        # Insere uma nova coluna
        sheet_financiamentos.insert_cols([[]], col=pos)
        
        # Adiciona o header
        col_letter = chr(64 + pos)  # Converte número para letra (1=A, 2=B, etc)
        sheet_financiamentos.update(f'{col_letter}1', 'Valor Entrada')
        
        # Preenche com 0.0 para os registros existentes
        num_rows = len(sheet_financiamentos.get_all_values())
        if num_rows > 1:
            valores_default = [[0.0] for _ in range(num_rows - 1)]
            sheet_financiamentos.update(f'{col_letter}2:{col_letter}{num_rows}', valores_default)
        
        print(f"[OK] Coluna 'Valor Entrada' adicionada com sucesso na coluna {col_letter}!")
        print(f"[OK] {num_rows - 1} registros existentes preenchidos com 0.0")
    else:
        print("[ERRO] Coluna 'Valor Total' nao encontrada nos headers!")
        return
    
    # Verifica o resultado
    headers_novos = sheet_financiamentos.row_values(1)
    print(f"\n[OK] Headers atualizados: {headers_novos}")

if __name__ == "__main__":
    try:
        adicionar_coluna_valor_entrada()
        print("\n[SUCESSO] A coluna foi adicionada.")
    except FileNotFoundError:
        print("\n[ERRO] Arquivo credentials.json nao encontrado!")
        print("   Certifique-se de que o arquivo esta na raiz do projeto.")
    except gspread.exceptions.APIError as e:
        print(f"\n[ERRO] Erro na API do Google Sheets: {e}")
        print("   Verifique se a planilha esta compartilhada com a conta de servico.")
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
