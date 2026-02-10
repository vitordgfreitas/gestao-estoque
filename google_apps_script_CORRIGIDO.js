/**
 * Google Apps Script para automação do Google Sheets - VERSÃO CORRIGIDA
 * 
 * CORREÇÃO APLICADA:
 * - Adicionadas abas "Financiamentos", "Parcelas Financiamento", "Contas a Receber", 
 *   "Contas a Pagar" na lista ABAS_SISTEMA
 * - Isso impede que essas abas sejam tratadas como categorias de itens
 * 
 * INSTRUÇÕES DE INSTALAÇÃO:
 * 1. Abra sua planilha do Google Sheets
 * 2. Vá em Extensões > Apps Script
 * 3. SUBSTITUA todo o código antigo por este
 * 4. Salve o projeto (Ctrl+S ou Cmd+S)
 * 5. O trigger já deve estar configurado, mas verifique:
 *    - Clique em "Triggers" (gatilhos) no menu lateral esquerdo
 *    - Deve ter um trigger para onEdit do tipo "Ao editar"
 * 
 * O QUE ESTE SCRIPT FAZ:
 * - Quando você adiciona um item na aba "Itens" com uma categoria nova, cria automaticamente a aba dessa categoria
 * - Quando você adiciona um item na aba "Itens" de qualquer categoria, preenche automaticamente na aba da categoria
 * - Quando você adiciona um registro em QUALQUER aba de categoria (Carros, Roupas, etc.), cria/atualiza automaticamente o item correspondente na aba "Itens"
 * - Preenche os dados automaticamente de forma inteligente (nome, categoria, etc.)
 * - NOVO: Ignora abas de financiamentos e contas (não são categorias de itens)
 */

// ✅ CORREÇÃO: Lista COMPLETA de abas do sistema (não são categorias)
const ABAS_SISTEMA = [
  "Itens", 
  "Carros", 
  "Compromissos",
  "Financiamentos",           // ✅ ADICIONADO
  "Parcelas Financiamento",   // ✅ ADICIONADO
  "Contas a Receber",         // ✅ ADICIONADO
  "Contas a Pagar",           // ✅ ADICIONADO
  "Categorias_Itens"          // ✅ ADICIONADO (caso exista)
];

/**
 * Função principal que é executada quando uma célula é editada
 */
function onEdit(e) {
  try {
    const sheet = e.source.getActiveSheet();
    const sheetName = sheet.getName();
    const range = e.range;
    const row = range.getRow();
    const col = range.getColumn();
    
    // Ignora edições na linha de cabeçalho
    if (row === 1) {
      return;
    }
    
    // Processa edições na aba "Itens"
    if (sheetName === "Itens") {
      processarEdicaoItens(e, sheet, row, col);
    }
    // Processa edições na aba "Carros" (tratamento especial)
    else if (sheetName === "Carros") {
      processarEdicaoCategoria(e, sheet, row, col, "Carros");
    }
    // Processa edições em qualquer outra aba (categorias)
    // ✅ AGORA ignora corretamente as abas de sistema
    else if (ABAS_SISTEMA.indexOf(sheetName) === -1) {
      processarEdicaoCategoria(e, sheet, row, col, sheetName);
    }
    
  } catch (error) {
    Logger.log("Erro no onEdit: " + error.toString());
    // Não mostra erro para o usuário para não interromper o trabalho
  }
}

/**
 * Processa edições na aba "Itens"
 */
function processarEdicaoItens(e, sheet, row, col) {
  const spreadsheet = e.source;
  
  // Lê os valores da linha editada
  const rowValues = sheet.getRange(row, 1, 1, 8).getValues()[0];
  const id = rowValues[0];
  const nome = rowValues[1];
  const quantidade = rowValues[2];
  const categoria = rowValues[3];
  const descricao = rowValues[4];
  const cidade = rowValues[5];
  const uf = rowValues[6];
  const endereco = rowValues[7];
  
  // Verifica se a linha tem dados mínimos (ID e Nome)
  if (!id || !nome) {
    return;
  }
  
  // Se há uma categoria, verifica/cria a aba da categoria
  if (categoria && categoria.toString().trim() !== "") {
    const categoriaNome = categoria.toString().trim();
    
    // ✅ CORREÇÃO: Não cria aba se for uma categoria de sistema
    if (ABAS_SISTEMA.indexOf(categoriaNome) !== -1) {
      Logger.log("Ignorando criação de aba para categoria de sistema: " + categoriaNome);
      return;
    }
    
    // Cria a aba da categoria se não existir
    criarAbaCategoria(spreadsheet, categoriaNome);
    
    // Sincroniza com a aba da categoria (cria/atualiza registro)
    if (categoriaNome === "Carros") {
      sincronizarItemParaCarros(spreadsheet, id, nome, quantidade, descricao, cidade, uf, endereco, row);
    } else {
      // Para outras categorias, cria registro na aba da categoria
      criarRegistroCategoria(spreadsheet, categoriaNome, id, rowValues);
    }
  }
}

/**
 * Processa edições em qualquer aba de categoria (incluindo Carros)
 */
function processarEdicaoCategoria(e, sheet, row, col, categoriaNome) {
  const spreadsheet = e.source;
  
  // Lê todos os valores da linha editada
  const lastCol = sheet.getLastColumn();
  const rowValues = sheet.getRange(row, 1, 1, lastCol).getValues()[0];
  
  // Primeira coluna é ID da categoria, segunda é Item ID
  const catId = rowValues[0];
  const itemId = rowValues[1];
  
  // Verifica se tem Item ID
  if (!itemId) {
    return;
  }
  
  // Se for Carros, usa função especializada
  if (categoriaNome === "Carros") {
    const placa = rowValues[2] || "";
    const marca = rowValues[3] || "";
    const modelo = rowValues[4] || "";
    const ano = rowValues[5] || "";
    sincronizarCategoriaParaItens(spreadsheet, itemId, categoriaNome, {
      placa: placa,
      marca: marca,
      modelo: modelo,
      ano: ano
    });
  } else {
    // Para outras categorias, sincroniza com dados genéricos
    sincronizarCategoriaParaItens(spreadsheet, itemId, categoriaNome, rowValues);
  }
}

/**
 * Cria uma aba para uma categoria se ela não existir
 */
function criarAbaCategoria(spreadsheet, categoriaNome) {
  try {
    // Lista todas as abas existentes
    const sheets = spreadsheet.getSheets();
    const sheetNames = sheets.map(s => s.getName());
    
    // Se a aba não existe, cria
    if (sheetNames.indexOf(categoriaNome) === -1) {
      const newSheet = spreadsheet.insertSheet(categoriaNome);
      
      // Adiciona cabeçalhos padrão
      const headers = ["ID", "Item ID"];
      newSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      
      // Formata cabeçalho
      const headerRange = newSheet.getRange(1, 1, 1, headers.length);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#4285f4");
      headerRange.setFontColor("#ffffff");
      
      Logger.log("Aba criada: " + categoriaNome);
    }
  } catch (error) {
    Logger.log("Erro ao criar aba " + categoriaNome + ": " + error.toString());
  }
}

/**
 * Cria um registro na aba da categoria
 */
function criarRegistroCategoria(spreadsheet, categoriaNome, itemId, rowValues) {
  try {
    const categoriaSheet = spreadsheet.getSheetByName(categoriaNome);
    if (!categoriaSheet) {
      return;
    }
    
    // Lê cabeçalhos da categoria para saber quais colunas existem
    const headers = categoriaSheet.getRange(1, 1, 1, categoriaSheet.getLastColumn()).getValues()[0];
    
    // Verifica se já existe um registro com este Item ID
    const allData = categoriaSheet.getDataRange().getValues();
    let existingRow = null;
    
    for (let i = 1; i < allData.length; i++) {
      if (allData[i][1] == itemId) { // Item ID está na coluna B (índice 1)
        existingRow = i + 1; // +1 porque índice começa em 0 mas linha começa em 1
        break;
      }
    }
    
    // Prepara valores baseado nos cabeçalhos
    const valores = [];
    valores.push(existingRow ? categoriaSheet.getRange(existingRow, 1).getValue() : categoriaSheet.getLastRow()); // ID
    valores.push(itemId); // Item ID
    
    // Preenche campos adicionais se existirem
    // Tenta mapear campos comuns do item para a categoria
    const nome = rowValues[1] || "";
    const descricao = rowValues[4] || "";
    
    // Para cada cabeçalho adicional (após ID e Item ID), tenta preencher
    for (let i = 2; i < headers.length; i++) {
      const header = headers[i];
      if (!header || header.toString().trim() === "") {
        valores.push("");
        continue;
      }
      
      // Se já existe registro, mantém valor existente
      if (existingRow) {
        const existingValue = categoriaSheet.getRange(existingRow, i + 1).getValue();
        if (existingValue && existingValue.toString().trim() !== "") {
          valores.push(existingValue);
        } else {
          // Tenta preencher com dados do item
          valores.push(preencherCampoCategoria(header, nome, descricao, rowValues));
        }
      } else {
        // Novo registro, tenta preencher automaticamente
        valores.push(preencherCampoCategoria(header, nome, descricao, rowValues));
      }
    }
    
    if (existingRow) {
      // Atualiza registro existente
      categoriaSheet.getRange(existingRow, 1, 1, valores.length).setValues([valores]);
    } else {
      // Cria novo registro
      categoriaSheet.appendRow(valores);
    }
  } catch (error) {
    Logger.log("Erro ao criar registro na categoria " + categoriaNome + ": " + error.toString());
  }
}

/**
 * Preenche um campo da categoria baseado no nome do campo e dados do item
 */
function preencherCampoCategoria(nomeCampo, nomeItem, descricao, rowValues) {
  const campoLower = nomeCampo.toString().toLowerCase();
  
  // Mapeia campos comuns
  if (campoLower.includes("nome") || campoLower.includes("name")) {
    return nomeItem;
  }
  if (campoLower.includes("descrição") || campoLower.includes("descricao") || campoLower.includes("description")) {
    return descricao;
  }
  if (campoLower.includes("quantidade") || campoLower.includes("qtd")) {
    return rowValues[2] || 1;
  }
  if (campoLower.includes("cidade")) {
    return rowValues[5] || "";
  }
  if (campoLower.includes("uf") || campoLower.includes("estado")) {
    return rowValues[6] || "";
  }
  if (campoLower.includes("endereço") || campoLower.includes("endereco") || campoLower.includes("address")) {
    return rowValues[7] || "";
  }
  
  // Retorna vazio se não conseguir mapear
  return "";
}

/**
 * Sincroniza um item da aba Itens para a aba Carros
 */
function sincronizarItemParaCarros(spreadsheet, itemId, nome, quantidade, descricao, cidade, uf, endereco, itemRow) {
  try {
    const carrosSheet = spreadsheet.getSheetByName("Carros");
    if (!carrosSheet) {
      criarAbaCategoria(spreadsheet, "Carros");
      return;
    }
    
    // Verifica se já existe um registro com este Item ID
    const allData = carrosSheet.getDataRange().getValues();
    let existingRow = null;
    
    for (let i = 1; i < allData.length; i++) {
      if (allData[i][1] == itemId) { // Item ID está na coluna B
        existingRow = i + 1;
        break;
      }
    }
    
    if (existingRow) {
      // Atualiza registro existente
      const existingValues = carrosSheet.getRange(existingRow, 1, 1, 6).getValues()[0];
      const catId = existingValues[0];
      let placa = existingValues[2] || "";
      let marca = existingValues[3] || "";
      let modelo = existingValues[4] || "";
      let ano = existingValues[5] || "";
      
      // Se campos estão vazios, tenta preencher com dados do item
      if (!marca || !modelo) {
        const dadosExtraidos = extrairDadosCarro(nome);
        if (!marca && dadosExtraidos.marca) marca = dadosExtraidos.marca;
        if (!modelo && dadosExtraidos.modelo) modelo = dadosExtraidos.modelo;
        if (!ano && dadosExtraidos.ano) ano = dadosExtraidos.ano;
      }
      
      carrosSheet.getRange(existingRow, 1, 1, 6).setValues([[catId, itemId, placa, marca, modelo, ano]]);
    } else {
      // Cria novo registro
      const lastRow = carrosSheet.getLastRow();
      const nextCarroId = lastRow; // ID sequencial
      
      // Extrai informações do nome do item
      const dadosExtraidos = extrairDadosCarro(nome);
      
      carrosSheet.appendRow([
        nextCarroId, 
        itemId, 
        "", // Placa (preencher manualmente)
        dadosExtraidos.marca, 
        dadosExtraidos.modelo, 
        dadosExtraidos.ano
      ]);
    }
  } catch (error) {
    Logger.log("Erro ao sincronizar item para Carros: " + error.toString());
  }
}

/**
 * Sincroniza qualquer categoria para a aba Itens
 * Esta função cria/atualiza automaticamente o item na aba Itens quando você edita uma categoria
 */
function sincronizarCategoriaParaItens(spreadsheet, itemId, categoriaNome, dadosCategoria) {
  try {
    const itensSheet = spreadsheet.getSheetByName("Itens");
    if (!itensSheet) {
      return;
    }
    
    // Busca o item na aba Itens pelo ID
    const allData = itensSheet.getDataRange().getValues();
    let itemRow = null;
    
    for (let i = 1; i < allData.length; i++) {
      if (allData[i][0] == itemId) { // ID está na coluna A
        itemRow = i + 1;
        break;
      }
    }
    
    // Prepara nome do item baseado nos dados da categoria
    let nomeItem = "";
    
    if (categoriaNome === "Carros") {
      // Para carros, monta nome: Marca Modelo Ano
      const marca = dadosCategoria.marca || "";
      const modelo = dadosCategoria.modelo || "";
      const ano = dadosCategoria.ano || "";
      nomeItem = [marca, modelo, ano].filter(x => x).join(" ").trim() || "Carro " + itemId;
    } else {
      // Para outras categorias, tenta usar o primeiro campo de texto disponível
      // ou usa um nome genérico
      if (Array.isArray(dadosCategoria)) {
        // Se dadosCategoria é array, procura primeiro campo de texto útil
        for (let i = 2; i < dadosCategoria.length; i++) {
          if (dadosCategoria[i] && dadosCategoria[i].toString().trim() !== "") {
            nomeItem = dadosCategoria[i].toString().trim();
            break;
          }
        }
      } else if (typeof dadosCategoria === 'object') {
        // Se é objeto, tenta encontrar um campo útil
        const campos = Object.values(dadosCategoria);
        for (const campo of campos) {
          if (campo && campo.toString().trim() !== "") {
            nomeItem = campo.toString().trim();
            break;
          }
        }
      }
      
      // Se não encontrou nome, usa genérico
      if (!nomeItem) {
        nomeItem = categoriaNome + " " + itemId;
      }
    }
    
    if (itemRow) {
      // Atualiza o item existente
      const existingValues = itensSheet.getRange(itemRow, 1, 1, 8).getValues()[0];
      
      // Mantém valores existentes, mas atualiza categoria e nome se necessário
      const nomeAtual = existingValues[1] || nomeItem;
      const quantidadeAtual = existingValues[2] || 1;
      const descricaoAtual = existingValues[4] || "";
      const cidadeAtual = existingValues[5] || "";
      const ufAtual = existingValues[6] || "";
      const enderecoAtual = existingValues[7] || "";
      
      // Se o nome mudou na categoria, atualiza também
      const nomeFinal = (existingValues[1] && existingValues[1].toString().trim() !== "") 
        ? existingValues[1] 
        : nomeItem;
      
      itensSheet.getRange(itemRow, 1, 1, 8).setValues([[
        itemId,
        nomeFinal,
        quantidadeAtual,
        categoriaNome, // Atualiza categoria
        descricaoAtual,
        cidadeAtual,
        ufAtual,
        enderecoAtual
      ]]);
    } else {
      // Cria novo item se não existir
      itensSheet.appendRow([
        itemId,
        nomeItem,
        1, // Quantidade padrão
        categoriaNome,
        "", // Descrição
        "", // Cidade
        "", // UF
        ""  // Endereço
      ]);
    }
  } catch (error) {
    Logger.log("Erro ao sincronizar categoria " + categoriaNome + " para Itens: " + error.toString());
  }
}

/**
 * Extrai marca, modelo e ano de um nome de carro
 */
function extrairDadosCarro(nome) {
  let marcaExtraida = "";
  let modeloExtraido = nome;
  let anoExtraido = "";
  
  if (!nome || nome.toString().trim() === "") {
    return { marca: "", modelo: "", ano: "" };
  }
  
  const nomeStr = nome.toString().trim();
  
  // Tenta extrair ano (4 dígitos no final ou no meio)
  const anoMatch = nomeStr.match(/\b(19|20)\d{2}\b/);
  if (anoMatch) {
    anoExtraido = anoMatch[0];
    modeloExtraido = nomeStr.replace(anoMatch[0], "").trim();
  }
  
  // Tenta identificar marca comum no início
  const marcasComuns = [
    "Fiat", "Volkswagen", "VW", "Chevrolet", "Chevy", "Ford", 
    "Toyota", "Honda", "Hyundai", "Renault", "Peugeot", "Citroën",
    "Nissan", "Mitsubishi", "Mazda", "Subaru", "Jeep", "Dodge",
    "BMW", "Mercedes-Benz", "Mercedes", "Audi", "Volvo", "Land Rover"
  ];
  
  for (const marcaComum of marcasComuns) {
    if (nomeStr.toLowerCase().startsWith(marcaComum.toLowerCase())) {
      marcaExtraida = marcaComum;
      modeloExtraido = nomeStr.substring(marcaComum.length).trim();
      // Remove ano se ainda estiver no modelo
      if (anoExtraido && modeloExtraido.includes(anoExtraido)) {
        modeloExtraido = modeloExtraido.replace(anoExtraido, "").trim();
      }
      break;
    }
  }
  
  return {
    marca: marcaExtraida,
    modelo: modeloExtraido,
    ano: anoExtraido
  };
}

/**
 * Função auxiliar para criar/atualizar cabeçalhos da aba Carros se necessário
 */
function garantirCabeçalhosCarros(spreadsheet) {
  try {
    const carrosSheet = spreadsheet.getSheetByName("Carros");
    if (!carrosSheet) {
      return;
    }
    
    const headers = carrosSheet.getRange(1, 1, 1, 6).getValues()[0];
    const expectedHeaders = ["ID", "Item ID", "Placa", "Marca", "Modelo", "Ano"];
    
    let needsUpdate = false;
    for (let i = 0; i < expectedHeaders.length; i++) {
      if (!headers[i] || headers[i] !== expectedHeaders[i]) {
        needsUpdate = true;
        break;
      }
    }
    
    if (needsUpdate) {
      carrosSheet.getRange(1, 1, 1, 6).setValues([expectedHeaders]);
      const headerRange = carrosSheet.getRange(1, 1, 1, 6);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#4285f4");
      headerRange.setFontColor("#ffffff");
    }
  } catch (error) {
    Logger.log("Erro ao garantir cabeçalhos Carros: " + error.toString());
  }
}
