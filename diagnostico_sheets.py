"""
Script de diagnóstico para verificar integridade das sheets
"""
from sheets_database import get_sheets

def diagnostico_sheets():
    print("=" * 60)
    print("DIAGNÓSTICO DE INTEGRIDADE DAS SHEETS")
    print("=" * 60)
    
    sheets = get_sheets()
    
    # Verifica nomes das abas
    print("\n1. ABAS DISPONÍVEIS:")
    print("-" * 60)
    for key, value in sheets.items():
        if key.startswith('sheet_'):
            sheet_name = value.title if hasattr(value, 'title') else str(value)
            print(f"  {key}: {sheet_name}")
    
    # Verifica sheet de itens
    print("\n2. SHEET DE ITENS:")
    print("-" * 60)
    sheet_itens = sheets['sheet_itens']
    print(f"  Nome da aba: {sheet_itens.title}")
    print(f"  ID da aba: {sheet_itens.id}")
    
    try:
        itens_records = sheet_itens.get_all_records()
        print(f"  Total de itens: {len(itens_records)}")
        
        # Verifica categorias únicas
        categorias = set()
        itens_com_problema = []
        
        for record in itens_records:
            categoria = record.get('Categoria', '')
            categorias.add(categoria)
            
            # Detecta itens com categoria estranha
            if categoria and categoria.lower() in ['financiamentos', 'financiamento']:
                itens_com_problema.append({
                    'id': record.get('ID'),
                    'nome': record.get('Nome'),
                    'categoria': categoria
                })
        
        print(f"  Categorias encontradas: {sorted(categorias)}")
        
        if itens_com_problema:
            print(f"\n  ⚠️  PROBLEMA DETECTADO! {len(itens_com_problema)} item(ns) com categoria 'Financiamentos':")
            for item in itens_com_problema:
                print(f"    - ID {item['id']}: {item['nome']} (Categoria: {item['categoria']})")
        else:
            print(f"\n  ✓ Nenhum item com categoria 'Financiamentos' detectado")
    except Exception as e:
        print(f"  ✗ Erro ao ler itens: {e}")
    
    # Verifica sheet de financiamentos
    print("\n3. SHEET DE FINANCIAMENTOS:")
    print("-" * 60)
    sheet_financiamentos = sheets['sheet_financiamentos']
    print(f"  Nome da aba: {sheet_financiamentos.title}")
    print(f"  ID da aba: {sheet_financiamentos.id}")
    
    try:
        fin_records = sheet_financiamentos.get_all_records()
        print(f"  Total de financiamentos: {len(fin_records)}")
        
        # Verifica se financiamentos têm IDs válidos
        fins_invalidos = []
        for record in fin_records:
            item_id = record.get('Item ID')
            if not item_id:
                fins_invalidos.append(record.get('ID'))
        
        if fins_invalidos:
            print(f"\n  ⚠️  {len(fins_invalidos)} financiamento(s) sem Item ID válido: {fins_invalidos}")
        else:
            print(f"\n  ✓ Todos os financiamentos têm Item ID válido")
    except Exception as e:
        print(f"  ✗ Erro ao ler financiamentos: {e}")
    
    # Verifica se há confusão entre abas
    print("\n4. VERIFICAÇÃO DE CONFUSÃO ENTRE ABAS:")
    print("-" * 60)
    if sheet_itens.id == sheet_financiamentos.id:
        print(f"  ✗ ERRO CRÍTICO! As duas sheets têm o MESMO ID!")
        print(f"    sheet_itens ID: {sheet_itens.id}")
        print(f"    sheet_financiamentos ID: {sheet_financiamentos.id}")
    else:
        print(f"  ✓ Sheets têm IDs diferentes (correto)")
        print(f"    sheet_itens ID: {sheet_itens.id}")
        print(f"    sheet_financiamentos ID: {sheet_financiamentos.id}")
    
    # Verifica cache
    print("\n5. VERIFICAÇÃO DE CACHE:")
    print("-" * 60)
    from sheets_database import _sheets_cache
    if _sheets_cache:
        print(f"  Cache ativo: Sim")
        print(f"  Spreadsheet ID: {_sheets_cache.get('spreadsheet_id')}")
    else:
        print(f"  Cache ativo: Não")
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 60)

if __name__ == "__main__":
    diagnostico_sheets()
