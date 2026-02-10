"""
Script de teste para validar a consistência de valores decimais
Testa os cenários identificados no plano de correção
"""
# -*- coding: utf-8 -*-
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_parse_value():
    """Testa a função parse_value com diferentes formatos"""
    
    def parse_value(val):
        """
        Parse value from Google Sheets.
        gspread already converts commas to dots correctly, so we just need to handle strings.
        """
        if val is None:
            return 0.0
        
        if isinstance(val, (int, float)):
            # gspread already converts commas to dots correctly (136072,88 → 136072.88)
            # Just round, don't try to "correct" the value
            return round(float(val), 2)
        
        if isinstance(val, str):
            # Clean Brazilian formatting (ex: "80.000,50" → 80000.50)
            val_clean = val.replace(' ', '').strip()
            
            if ',' in val_clean and '.' in val_clean:
                # Format: "80.000,50" → remove dots (thousands), comma becomes dot (decimal)
                val_clean = val_clean.replace('.', '').replace(',', '.')
            elif ',' in val_clean:
                # Format: "80000,50" → comma becomes dot
                val_clean = val_clean.replace(',', '.')
            
            try:
                return round(float(val_clean), 2)
            except (ValueError, TypeError):
                return 0.0
        
        return 0.0
    
    print("=" * 60)
    print("TESTE 1: parse_value() - Valores Monetários")
    print("=" * 60)
    
    test_cases = [
        # (input, expected, description)
        (136072.88, 136072.88, "Float com decimais (gspread já converteu)"),
        (80000, 80000.00, "Integer (sem decimais)"),
        (80000.0, 80000.00, "Float sem decimais"),
        ("136.072,88", 136072.88, "String formato brasileiro com pontos de milhar"),
        ("80000,50", 80000.50, "String formato brasileiro sem pontos de milhar"),
        ("80000", 80000.00, "String sem formatação"),
        (1968.52, 1968.52, "Valor de parcela típico"),
        (0, 0.0, "Zero"),
        (None, 0.0, "None"),
    ]
    
    all_passed = True
    for input_val, expected, description in test_cases:
        result = parse_value(input_val)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} {description}")
        print(f"  Input: {input_val} ({type(input_val).__name__})")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        if not passed:
            print(f"  ERRO: Diferença de {result - expected}")
        print()
    
    return all_passed


def test_normalize_taxa():
    """Testa a normalização de taxa de juros"""
    
    def normalize_taxa(taxa_juros):
        """Normaliza taxa de juros para formato decimal (< 1)"""
        taxa_str = str(taxa_juros).replace(',', '.')
        taxa_float = float(taxa_str)
        
        # NORMALIZAÇÃO: Garante que taxa está em formato decimal (< 1)
        if taxa_float >= 100:  # Ex: 1550 → 0.0155 (1.55%)
            taxa_float = taxa_float / 10000
        elif taxa_float >= 1:  # Ex: 1.55 → 0.0155 (1.55%)
            taxa_float = taxa_float / 100
        # Se < 1, já está correto (0.0155)
        
        return round(taxa_float, 6)
    
    print("=" * 60)
    print("TESTE 2: normalize_taxa() - Taxa de Juros")
    print("=" * 60)
    
    test_cases = [
        # (input, expected_decimal, expected_percent_display, description)
        (0.0155, 0.0155, "1.55%", "Formato decimal correto (0.0155)"),
        ("0,0155", 0.0155, "1.55%", "String com vírgula (0,0155)"),
        (1.55, 0.0155, "1.55%", "Formato percentual (1.55)"),
        ("1,55", 0.0155, "1.55%", "String percentual com vírgula (1,55)"),
        (155, 0.0155, "1.55%", "Formato inteiro (155)"),
        (1550, 0.155, "15.50%", "Formato inteiro grande (1550 = 15.50%)"),
        (0.0275, 0.0275, "2.75%", "Taxa 2.75% em decimal"),
        (2.75, 0.0275, "2.75%", "Taxa 2.75% em percentual"),
        (275, 0.0275, "2.75%", "Taxa 2.75% em inteiro"),
    ]
    
    all_passed = True
    for input_val, expected_decimal, expected_display, description in test_cases:
        result = normalize_taxa(input_val)
        display = f"{(result * 100):.2f}%"
        passed = abs(result - expected_decimal) < 0.000001 and display == expected_display
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} {description}")
        print(f"  Input: {input_val}")
        print(f"  Expected: {expected_decimal} → {expected_display}")
        print(f"  Got: {result} → {display}")
        if not passed:
            print(f"  ERRO!")
        print()
    
    return all_passed


def test_integration_scenarios():
    """Testa cenários completos de integração"""
    
    print("=" * 60)
    print("TESTE 3: Cenários de Integração Completos")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Financiamento 1 - Volkswagen Polo",
            "sheet_data": {
                "Valor Total": 80000,
                "Valor Entrada": 26000,
                "Valor Parcela": 1968.52,
                "Taxa Juros": "0,0155000"
            },
            "expected_display": {
                "valor_total": "R$ 80.000,00",
                "valor_entrada": "R$ 26.000,00",
                "valor_parcela": "R$ 1.968,52",
                "taxa_juros": "1.55%"
            }
        },
        {
            "name": "Financiamento 2 - Fiat Mobi",
            "sheet_data": {
                "Valor Total": 136072.88,
                "Valor Entrada": 39729.42,
                "Valor Parcela": 3512.06,
                "Taxa Juros": "0,0154990"
            },
            "expected_display": {
                "valor_total": "R$ 136.072,88",
                "valor_entrada": "R$ 39.729,42",
                "valor_parcela": "R$ 3.512,06",
                "taxa_juros": "1.55%"
            }
        }
    ]
    
    # Simula o fluxo completo
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
    
    def normalize_taxa(taxa_juros):
        taxa_str = str(taxa_juros).replace(',', '.')
        taxa_float = float(taxa_str)
        if taxa_float >= 100:
            taxa_float = taxa_float / 10000
        elif taxa_float >= 1:
            taxa_float = taxa_float / 100
        return round(taxa_float, 6)
    
    def format_currency(value):
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    all_passed = True
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 60)
        
        # Simula leitura do Google Sheets
        valor_total = parse_value(scenario['sheet_data']['Valor Total'])
        valor_entrada = parse_value(scenario['sheet_data']['Valor Entrada'])
        valor_parcela = parse_value(scenario['sheet_data']['Valor Parcela'])
        taxa_juros = normalize_taxa(scenario['sheet_data']['Taxa Juros'])
        
        # Formata para display
        display_valor_total = format_currency(valor_total)
        display_valor_entrada = format_currency(valor_entrada)
        display_valor_parcela = format_currency(valor_parcela)
        display_taxa_juros = f"{(taxa_juros * 100):.2f}%"
        
        # Verifica resultados
        checks = [
            ("Valor Total", display_valor_total, scenario['expected_display']['valor_total']),
            ("Valor Entrada", display_valor_entrada, scenario['expected_display']['valor_entrada']),
            ("Valor Parcela", display_valor_parcela, scenario['expected_display']['valor_parcela']),
            ("Taxa Juros", display_taxa_juros, scenario['expected_display']['taxa_juros'])
        ]
        
        for field, got, expected in checks:
            passed = got == expected
            all_passed = all_passed and passed
            status = "✓" if passed else "✗"
            print(f"  {status} {field}: {got} {'==' if passed else '!='} {expected}")
        
        print()
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE DE CONSISTÊNCIA DE VALORES DECIMAIS")
    print("=" * 60 + "\n")
    
    test1_passed = test_parse_value()
    print()
    
    test2_passed = test_normalize_taxa()
    print()
    
    test3_passed = test_integration_scenarios()
    
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    print(f"Teste 1 (parse_value): {'✓ PASSOU' if test1_passed else '✗ FALHOU'}")
    print(f"Teste 2 (normalize_taxa): {'✓ PASSOU' if test2_passed else '✗ FALHOU'}")
    print(f"Teste 3 (integração): {'✓ PASSOU' if test3_passed else '✗ FALHOU'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n✓✓✓ TODOS OS TESTES PASSARAM! ✓✓✓")
        exit(0)
    else:
        print("\n✗✗✗ ALGUNS TESTES FALHARAM ✗✗✗")
        exit(1)
