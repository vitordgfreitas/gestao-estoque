# 📋 Guia de Instalação do Script de Automação do Google Sheets

Este script automatiza ações quando você edita diretamente no Google Sheets:

## ✨ O que o script faz:

1. **Criação automática de categorias**: Quando você adiciona um item na aba "Itens" com uma categoria nova, o script cria automaticamente uma nova aba com o nome dessa categoria.

2. **Sincronização bidirecional completa**: 
   - **Itens → Categorias**: Quando você cria um item na aba "Itens" de qualquer categoria, ele automaticamente cria/atualiza o registro na aba da categoria correspondente
   - **Categorias → Itens**: Quando você cria um registro em QUALQUER aba de categoria (Carros, Roupas, Estruturas, etc.), ele automaticamente cria/atualiza o item correspondente na aba "Itens"

3. **Preenchimento automático inteligente**:
   - Para **Carros**: Extrai automaticamente marca, modelo e ano do nome do item
   - Para **outras categorias**: Mapeia campos comuns (nome, descrição, quantidade, cidade, UF, endereço) automaticamente
   - Preenche dados sempre que possível, mantendo valores existentes quando já preenchidos

## 🚀 Como instalar:

### Passo 1: Abrir o Apps Script

1. Abra sua planilha do Google Sheets
2. Clique em **Extensões** (ou **Ferramentas** em versões antigas)
3. Clique em **Apps Script**

### Passo 2: Colar o código

1. Você verá uma tela com um editor de código
2. Delete todo o código que estiver lá (se houver)
3. Abra o arquivo `GOOGLE_SHEETS_SCRIPT.js` deste projeto
4. Copie **TODO** o conteúdo do arquivo
5. Cole no editor do Apps Script

### Passo 3: Salvar o projeto

1. Clique em **Salvar** (ícone de disquete) ou pressione `Ctrl+S` (Windows) / `Cmd+S` (Mac)
2. Dê um nome ao projeto (ex: "Automação Gestão de Estoque")
3. Clique em **OK**

### Passo 4: Configurar o Trigger (Gatilho)

1. No menu lateral esquerdo, clique em **Triggers** (Gatilhos) - ícone de relógio ⏰
2. Clique no botão **+ Adicionar Trigger** (no canto inferior direito)
3. Configure:
   - **Função a executar**: `onEdit`
   - **Tipo de evento**: `Ao editar`
   - **Fonte do evento**: `Na planilha`
   - Deixe os outros campos como estão
4. Clique em **Salvar**

### Passo 5: Autorizar o script

1. Na primeira vez que o script rodar, o Google pedirá permissão
2. Clique em **Revisar permissões**
3. Escolha sua conta do Google
4. Clique em **Avançado** → **Ir para [nome do projeto] (não seguro)**
5. Clique em **Permitir**

## ✅ Testar o script:

### Teste 1: Criar categoria nova
1. Vá na aba **Itens**
2. Adicione uma nova linha com:
   - ID: qualquer número
   - Nome: "Vestido"
   - Quantidade Total: 5
   - Categoria: **"Roupas"** (nova categoria)
   - Preencha os outros campos
3. **Resultado esperado**: Uma nova aba chamada "Roupas" deve ser criada automaticamente!

### Teste 2: Sincronização Carros → Itens
1. Vá na aba **Carros**
2. Adicione uma nova linha com:
   - ID: qualquer número
   - Item ID: um número que não existe na aba Itens (ex: 999)
   - Placa: "ABC-1234"
   - Marca: "Fiat"
   - Modelo: "Uno"
   - Ano: 2015
3. **Resultado esperado**: Um novo item deve aparecer automaticamente na aba **Itens** com:
   - Nome: "Fiat Uno 2015" (montado automaticamente)
   - Categoria: "Carros"
   - Quantidade: 1

### Teste 3: Sincronização Itens → Carros
1. Vá na aba **Itens**
2. Adicione uma nova linha com:
   - ID: qualquer número
   - Nome: "Honda Civic 2020"
   - Quantidade Total: 1
   - Categoria: **"Carros"**
   - Preencha os outros campos
3. **Resultado esperado**: Um novo registro deve aparecer automaticamente na aba **Carros** com:
   - Marca: "Honda" (extraída automaticamente)
   - Modelo: "Civic" (extraído automaticamente)
   - Ano: "2020" (extraído automaticamente)

### Teste 4: Sincronização em qualquer categoria
1. Vá na aba **Roupas** (ou crie uma nova categoria "Roupas" primeiro)
2. Adicione uma nova linha com:
   - ID: qualquer número
   - Item ID: um número que não existe na aba Itens (ex: 888)
   - Preencha outros campos se houver
3. **Resultado esperado**: Um novo item deve aparecer automaticamente na aba **Itens** com categoria "Roupas"!

## 🔧 Solução de problemas:

### O script não está funcionando

1. **Verifique se o trigger está configurado**:
   - Vá em Extensões > Apps Script > Triggers
   - Deve haver um trigger `onEdit` configurado

2. **Verifique os logs**:
   - No Apps Script, clique em **Executar** → `onEdit`
   - Veja se há erros no console

3. **Verifique as permissões**:
   - O script precisa de permissão para editar a planilha
   - Vá em Extensões > Apps Script > Triggers
   - Clique nos 3 pontinhos ao lado do trigger → **Revisar permissões**

### O script está muito lento

- O script roda a cada edição, então pode demorar alguns segundos
- Se você fizer muitas edições rápidas, aguarde alguns segundos entre cada uma

### Erro: "Não é possível ler a propriedade 'getActiveSheet'"

- Isso pode acontecer se você editar muito rápido
- Tente editar novamente mais devagar

## 📝 Notas importantes:

- ⚠️ **O script só funciona quando você edita diretamente no Google Sheets**, não quando o web app cria itens
- ⚠️ **O script roda automaticamente** quando você edita qualquer célula
- ⚠️ **Não delete o trigger** após configurá-lo, ou o script não funcionará
- ✅ **O script é seguro** - ele só edita sua planilha, não acessa outros dados

## 🆘 Precisa de ajuda?

Se algo não funcionar:
1. Verifique se seguiu todos os passos
2. Veja os logs no Apps Script (Executar → Ver logs)
3. Certifique-se de que o trigger está ativo
