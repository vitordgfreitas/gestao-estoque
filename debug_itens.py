"""
Debug: Ver como os itens estao chegando da API
"""
import sys
sys.path.insert(0, '.')

from sheets_database import listar_itens

def debug_itens():
    print("[*] Buscando todos os itens...")
    try:
        itens = listar_itens()
        carros = [i for i in itens if i.categoria == 'Carros']
        print(f"\n[OK] Encontrados {len(carros)} carros\n")
        
        for item in carros:
            print(f"=== Item ID: {item.id} ===")
            print(f"  Nome: {item.nome}")
            print(f"  Categoria: {item.categoria}")
            print(f"  dados_categoria type: {type(item.dados_categoria)}")
            print(f"  dados_categoria: {item.dados_categoria}")
            
            # Verifica se tem placa
            if item.dados_categoria:
                print(f"  Placa (key 'Placa'): {item.dados_categoria.get('Placa', 'NAO TEM')}")
                print(f"  Placa (key 'placa'): {item.dados_categoria.get('placa', 'NAO TEM')}")
                print(f"  Marca: {item.dados_categoria.get('Marca', 'NAO TEM')}")
                print(f"  Modelo: {item.dados_categoria.get('Modelo', 'NAO TEM')}")
            
            # Tenta acessar carro
            if hasattr(item, 'carro'):
                print(f"  carro: {item.carro}")
            
            print()
            
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_itens()
