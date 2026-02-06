# 🧪 Guia de Testes - Implementação Completa

## Pré-requisitos

1. ✅ Migrações executadas (`executar_migracoes.bat`)
2. ✅ Backend rodando (`uvicorn main:app --reload`)
3. ✅ Frontend rodando (`npm run dev`)

---

## Teste 1: Valor de Entrada em Financiamentos

### Objetivo
Verificar se o valor de entrada é corretamente deduzido do valor total.

### Passos

1. Acesse **Financiamentos**
2. Clique em "**Novo Financiamento**"
3. Selecione um item (ex: Carro)
4. Preencha:
   - **Valor Total**: 100000
   - **Valor de Entrada**: 20000
   - **Número de Parcelas**: 24
   - **Taxa de Juros**: 0.02 (2%)
   - **Data de Início**: Hoje
   - **Instituição**: Banco XYZ
5. Clique em "**Criar Financiamento**"

### Resultado Esperado

- ✅ Financiamento criado com sucesso
- ✅ Card exibe:
  - **Valor Total**: R$ 100.000,00
  - **Valor de Entrada**: R$ 20.000,00
  - **Valor Financiado**: R$ 80.000,00 (não R$ 100.000,00!)
- ✅ Valor da parcela calculado sobre R$ 80.000,00
- ✅ Valores com 2 casas decimais corretas

---

## Teste 2: Filtro de Categoria em Financiamentos

### Objetivo
Verificar se o filtro de categoria funciona corretamente.

### Passos

1. Acesse **Financiamentos**
2. Clique em "**Novo Financiamento**"
3. No dropdown **Categoria**, selecione "**Carros**"
4. Observe o dropdown **Item**

### Resultado Esperado

- ✅ Dropdown de Item mostra APENAS itens da categoria "Carros"
- ✅ Carros exibidos no formato: "**Marca Modelo - Placa**"
  - Exemplo: "Toyota Corolla - ABC1234"
- ✅ Ao trocar para "**Estrutura de Evento**", mostra apenas itens dessa categoria
- ✅ Ao trocar categoria, campo "Item" é limpo

---

## Teste 3: Associar Peça a Carro (Tipo Compromisso)

### Objetivo
Verificar a funcionalidade de associar peças de carro.

### Passos

1. Acesse **Registrar Compromisso**
2. No dropdown **Tipo de Compromisso**, selecione "**Peças de Carro**"
3. Observe que a interface muda completamente
4. Preencha:
   - **Carro**: Selecione um carro (ex: "Toyota Corolla - ABC1234")
   - **Peça**: Selecione uma peça (ex: "Filtro de Óleo")
   - **Quantidade**: 2
   - **Data de Instalação**: Hoje
   - **Observações**: "Instalado na revisão"
5. Clique em "**Associar Peça ao Carro**"

### Resultado Esperado

- ✅ Toast de sucesso: "Peça associada ao carro com sucesso!"
- ✅ Formulário limpo (mantém tipo "Peças de Carro")
- ✅ Não aparece campos de localização (cidade, UF, endereço)
- ✅ Botão muda texto conforme tipo selecionado

### Validações

- ❌ Não permite selecionar item que não seja carro
- ❌ Não permite selecionar item que não seja peça de carro

---

## Teste 4: Compromisso Normal (Itens Alugados)

### Objetivo
Garantir que a funcionalidade original não foi quebrada.

### Passos

1. Acesse **Registrar Compromisso**
2. No dropdown **Tipo de Compromisso**, selecione "**Itens Alugados**"
3. Preencha normalmente:
   - Categoria
   - Item
   - Quantidade
   - Datas (início e fim)
   - Localização (cidade, UF, endereço)
   - Contratante
4. Clique em "**Registrar Compromisso**"

### Resultado Esperado

- ✅ Interface original aparece
- ✅ Todos os campos antigos funcionam
- ✅ Verificação de disponibilidade funciona
- ✅ Toast de sucesso: "Compromisso registrado com sucesso!"

---

## Teste 5: Precisão Decimal

### Objetivo
Verificar se os valores monetários têm exatamente 2 casas decimais.

### Cenário A: Financiamento

1. Crie financiamento:
   - Valor Total: 200000
   - Número de Parcelas: 24
   - Taxa: 0.02

### Resultado Esperado

- ✅ Valor da parcela exibido: R$ 10.574,22 (não R$ 10,57!)
- ✅ Valor Presente exibido com 2 casas decimais
- ✅ No Google Sheets (se integrado), valores salvos como float com 2 decimais

### Cenário B: Parcelas

1. Acesse detalhes do financiamento
2. Verifique as parcelas

### Resultado Esperado

- ✅ Cada parcela com valor preciso: R$ 10.574,22
- ✅ Ao pagar parcela, valor registrado com 2 casas decimais

---

## Teste 6: Navegação e Menu

### Objetivo
Verificar que a página "Peças em Carros" foi removida.

### Passos

1. Abra o menu lateral
2. Procure por "Peças em Carros" ou "Peças de Carro"
3. Tente acessar manualmente: `http://localhost:5173/pecas-carros`

### Resultado Esperado

- ✅ Menu NÃO contém item "Peças em Carros"
- ✅ URL `/pecas-carros` retorna 404 ou redireciona
- ✅ Funcionalidade integrada em "Registrar Compromisso"

---

## Teste 7: Exibição de Carros em Dropdowns

### Objetivo
Verificar formatação melhorada de carros.

### Onde Testar

1. **Financiamentos** > Novo > Categoria: Carros > Item
2. **Compromissos** > Tipo: Peças de Carro > Carro

### Resultado Esperado

**Formato correto**:
- ✅ "Toyota Corolla - ABC1234"
- ✅ "Ford Ka - XYZ9876"
- ✅ "Honda Civic - DEF4567"

**Formato antigo (INCORRETO)**:
- ❌ "Carro 1"
- ❌ "Meu Carro"
- ❌ Apenas nome genérico

### Fallback

Se carro não tem marca/modelo/placa:
- ✅ Exibe o campo `nome` do item
- ✅ Não gera erro no console

---

## 🐛 Checklist de Debugging

Se algo não funcionar:

### Backend

- [ ] Migrações foram executadas?
- [ ] Coluna `valor_entrada` existe em `financiamentos`?
  ```bash
  sqlite3 data/estoque.db ".schema financiamentos"
  ```
- [ ] Tabela `pecas_carros` foi criada?
  ```bash
  sqlite3 data/estoque.db ".tables"
  ```
- [ ] Console do backend não mostra erros?
- [ ] Endpoints retornam status 200?

### Frontend

- [ ] Console do navegador não mostra erros?
- [ ] Componentes carregam corretamente?
- [ ] API está acessível (verificar CORS)?
- [ ] Token de autenticação válido?

### Dados

- [ ] Existe pelo menos 1 item categoria "Carros"?
- [ ] Existe pelo menos 1 item categoria "Peças de Carro"?
- [ ] Carros têm campos `Marca`, `Modelo`, `Placa` em `dados_categoria`?

---

## 📊 Matriz de Testes

| Teste | Status | Observações |
|-------|--------|-------------|
| Valor de Entrada | ⬜ | |
| Filtro Categoria | ⬜ | |
| Associar Peça | ⬜ | |
| Compromisso Normal | ⬜ | |
| Precisão Decimal | ⬜ | |
| Navegação/Menu | ⬜ | |
| Exibição Carros | ⬜ | |

**Legenda**: ⬜ Pendente | ✅ Passou | ❌ Falhou

---

## 🎯 Critérios de Aceitação

Para considerar a implementação completa:

- ✅ Todos os 7 testes devem **PASSAR**
- ✅ Nenhum erro no console (backend ou frontend)
- ✅ Valores com **exatamente 2 casas decimais**
- ✅ UX intuitiva (tipo de compromisso claro)
- ✅ Validações funcionando

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique o **Checklist de Debugging** acima
2. Consulte `IMPLEMENTACAO_COMPLETA.md` para detalhes técnicos
3. Revise os logs do backend e console do navegador

---

*Guia criado em: 2026-02-06*
