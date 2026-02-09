"""
INSTRUÇÕES PARA CORRIGIR OS HEADERS DA PLANILHA FINANCIAMENTOS

O problema é que as colunas da planilha "Financiamentos" estão bagunçadas.

## SOLUÇÃO MANUAL (MAIS RÁPIDA)

1. Abra o Google Sheets da aplicação
2. Vá na aba "Financiamentos"
3. **DELETE a linha 1 inteira** (clique no número 1 à esquerda e delete)
4. Na célula A1, copie e cole esta linha (separada por TABs):

ID	Item ID	Valor Total	Numero Parcelas	Valor Parcela	Taxa Juros	Data Inicio	Status	Instituicao Financeira	Observacoes

OU copie célula por célula:
- A1: ID
- B1: Item ID
- C1: Valor Total
- D1: Numero Parcelas
- E1: Valor Parcela
- F1: Taxa Juros
- G1: Data Inicio
- H1: Status
- I1: Instituicao Financeira
- J1: Observacoes

5. Verifique se os dados nas linhas abaixo estão nas colunas corretas
6. Se necessário, reorganize os dados manualmente

## ORDEM CORRETA DAS COLUNAS

1. **ID** - Identificador único do financiamento
2. **Item ID** - ID do item financiado
3. **Valor Total** - Valor total financiado
4. **Numero Parcelas** - Quantidade de parcelas
5. **Valor Parcela** - Valor de cada parcela
6. **Taxa Juros** - Taxa de juros (decimal, ex: 0.0275 = 2,75%)
7. **Data Inicio** - Data de início do financiamento
8. **Status** - Status (Ativo, Quitado, Cancelado)
9. **Instituicao Financeira** - Nome da instituição
10. **Observacoes** - Observações adicionais

## NOTA IMPORTANTE

O financiamento salvo tem estes dados:
- ID: 1
- Item ID: 9
- Valor Total: 136072,88
- Numero Parcelas: 36
- Valor Parcela: 3512,11
- Taxa Juros: 0,015539
- Data Inicio: 2026-02-21
- Status: Ativo
- Instituicao Financeira: Volkswagen Financial Services
- Observacoes: (vazio)

Certifique-se de que cada dado está na coluna correta após corrigir os headers.

## SE TIVER MAIS DE UM FINANCIAMENTO

Reorganize cada linha para corresponder aos headers corretos.

## APÓS CORRIGIR

1. Salve a planilha
2. Teste criar um novo financiamento no app
3. Verifique se os dados aparecem nas colunas corretas
