"""
Testar a função listar_financiamentos localmente
"""
import sys
sys.path.insert(0, '.')

from sheets_database import listar_financiamentos

def teste_listar_financiamentos():
    print("[*] Testando listar_financiamentos()...")
    try:
        financiamentos = listar_financiamentos()
        print(f"[OK] Sucesso! Encontrados {len(financiamentos)} financiamentos")
        
        for fin in financiamentos:
            print(f"\n  Financiamento ID: {fin.id}")
            print(f"    Item ID: {fin.item_id}")
            print(f"    Valor Total: {fin.valor_total}")
            print(f"    Valor Entrada: {getattr(fin, 'valor_entrada', 'ATRIBUTO NAO EXISTE')}")
            print(f"    Numero Parcelas: {fin.numero_parcelas}")
            
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    teste_listar_financiamentos()
