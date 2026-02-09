"""
Script para corrigir os headers da aba Financiamentos no Google Sheets
"""
from sheets_config import get_sheets_client
import os

def corrigir_headers_financiamentos():
    """Corrige os headers da aba Financiamentos"""
    try:
        # Conecta ao Google Sheets
        client = get_sheets_client()
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        if not sheet_id:
            print("❌ GOOGLE_SHEET_ID não configurado!")
            return
        
        print(f"📊 Conectando ao Google Sheets: {sheet_id}")
        spreadsheet = client.open_by_key(sheet_id)
        
        # Obtém a aba Financiamentos
        try:
            sheet_financiamentos = spreadsheet.worksheet("Financiamentos")
            print("✅ Aba 'Financiamentos' encontrada")
        except:
            print("❌ Aba 'Financiamentos' não encontrada!")
            return
        
        # Headers corretos
        headers_corretos = [
            "ID",
            "Item ID",
            "Valor Total",
            "Numero Parcelas",
            "Valor Parcela",
            "Taxa Juros",
            "Data Inicio",
            "Status",
            "Instituicao Financeira",
            "Observacoes"
        ]
        
        # Atualiza os headers na primeira linha
        print("🔧 Corrigindo headers...")
        sheet_financiamentos.update('A1:J1', [headers_corretos])
        
        print("✅ Headers corrigidos com sucesso!")
        print("\nHeaders atualizados:")
        for i, header in enumerate(headers_corretos, 1):
            print(f"  Coluna {chr(64+i)}: {header}")
        
        # Mostra dados atuais
        print("\n📋 Primeiras linhas da planilha:")
        rows = sheet_financiamentos.get_all_values()[:3]  # Primeiras 3 linhas
        for row in rows:
            print("  " + " | ".join(str(cell) for cell in row))
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("CORRIGIR HEADERS DA ABA FINANCIAMENTOS")
    print("=" * 60)
    print()
    corrigir_headers_financiamentos()
    print()
    print("=" * 60)
