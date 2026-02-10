"""
Teste para verificar como o gspread está lendo os valores do Google Sheets
"""
from sheets_database import get_sheets

def testar_leitura_valores():
    print("=" * 60)
    print("TESTE: Como gspread lê os valores do Google Sheets")
    print("=" * 60)
    
    sheets = get_sheets()
    sheet_financiamentos = sheets['sheet_financiamentos']
    
    # Lê todos os registros
    records = sheet_financiamentos.get_all_records()
    
    print(f"\nTotal de financiamentos: {len(records)}")
    print("\n" + "-" * 60)
    
    for i, record in enumerate(records, 1):
        if record and record.get('ID'):
            print(f"\nFinanciamento {i}:")
            print(f"  ID: {record.get('ID')} (type: {type(record.get('ID')).__name__})")
            print(f"  Item ID: {record.get('Item ID')} (type: {type(record.get('Item ID')).__name__})")
            
            valor_total = record.get('Valor Total')
            print(f"  Valor Total RAW: '{valor_total}' (type: {type(valor_total).__name__})")
            
            valor_entrada = record.get('Valor Entrada')
            print(f"  Valor Entrada RAW: '{valor_entrada}' (type: {type(valor_entrada).__name__})")
            
            valor_parcela = record.get('Valor Parcela')
            print(f"  Valor Parcela RAW: '{valor_parcela}' (type: {type(valor_parcela).__name__})")
            
            taxa_juros = record.get('Taxa Juros')
            print(f"  Taxa Juros RAW: '{taxa_juros}' (type: {type(taxa_juros).__name__})")
            
            # Testa parse_value
            def parse_value(val):
                if val is None:
                    return 0.0
                
                if isinstance(val, (int, float)):
                    return round(float(val), 2)
                
                if isinstance(val, str):
                    val_clean = val.replace(' ', '').strip()
                    
                    if ',' in val_clean and '.' in val_clean:
                        val_clean = val_clean.replace('.', '').replace(',', '.')
                    elif ',' in val_clean:
                        val_clean = val_clean.replace(',', '.')
                    
                    try:
                        return round(float(val_clean), 2)
                    except (ValueError, TypeError):
                        return 0.0
                
                return 0.0
            
            valor_total_parsed = parse_value(valor_total)
            valor_entrada_parsed = parse_value(valor_entrada)
            valor_parcela_parsed = parse_value(valor_parcela)
            
            print(f"  Valor Total PARSED: {valor_total_parsed}")
            print(f"  Valor Entrada PARSED: {valor_entrada_parsed}")
            print(f"  Valor Parcela PARSED: {valor_parcela_parsed}")
            
            print("-" * 60)

if __name__ == "__main__":
    testar_leitura_valores()
