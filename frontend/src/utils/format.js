/**
 * Utilitários de formatação para o CRM
 */

/**
 * Formata um valor numérico como moeda brasileira (BRL)
 * @param {number|string} value - Valor a ser formatado
 * @returns {string} Valor formatado como R$ X.XXX,XX
 */
export const formatCurrency = (value) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return 'R$ 0,00'
  
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numValue)
}

/**
 * Formata uma data no padrão brasileiro (DD/MM/AAAA)
 * @param {string|Date} dateString - Data a ser formatada
 * @returns {string} Data formatada como DD/MM/AAAA
 */
export const formatDate = (dateString) => {
  if (!dateString) return ''
  
  const date = typeof dateString === 'string' ? new Date(dateString + 'T00:00:00') : dateString
  if (isNaN(date.getTime())) return ''
  
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: 'UTC'
  }).format(date)
}

/**
 * Formata valor tipo "caixa registradora" - sempre assume últimos 2 dígitos como centavos
 * @param {string} value - Valor digitado
 * @returns {string} Valor formatado (ex: "80.000,50")
 */
export const formatCurrencyInput = (value) => {
  // Remove tudo exceto números
  const onlyNumbers = value.replace(/[^\d]/g, '')
  
  // Se está vazio, retorna vazio
  if (!onlyNumbers || onlyNumbers.length === 0) return ''
  
  // Converte para número e divide por 100 (para ter 2 casas decimais)
  const numberValue = parseInt(onlyNumbers, 10) / 100
  
  // Formata com separadores de milhar e vírgula decimal
  return numberValue.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

/**
 * Formata taxa de juros tipo "caixa registradora" - sempre assume últimos 6 dígitos como decimais
 * @param {string} value - Valor digitado
 * @returns {string} Valor formatado (ex: "2,750000" ou "1,234567")
 */
export const formatPercentageInput = (value) => {
  // Remove tudo exceto números
  const onlyNumbers = value.replace(/[^\d]/g, '')
  
  // Se está vazio, retorna vazio
  if (!onlyNumbers || onlyNumbers.length === 0) return ''
  
  // Converte para número e divide por 1000000 (para ter 6 casas decimais)
  const numberValue = parseInt(onlyNumbers, 10) / 1000000
  
  // Formata com vírgula decimal (sem separadores de milhar para %)
  return numberValue.toLocaleString('pt-BR', {
    minimumFractionDigits: 6,
    maximumFractionDigits: 6
  })
}

/**
 * Formata valor decimal como porcentagem para exibição, removendo zeros à direita
 * @param {number} value - Valor decimal (ex: 0.0123456 = 1.23456%)
 * @returns {string} Valor formatado (ex: "1.23456%")
 */
export const formatPercentageDisplay = (value) => {
  if (!value || isNaN(value)) return '0%'
  
  const percentage = value * 100
  // Remove trailing zeros: 1.234500 → 1.2345
  return percentage.toFixed(6).replace(/\.?0+$/, '') + '%'
}

/**
 * Formata uma data e hora no padrão brasileiro (DD/MM/AAAA HH:MM)
 * @param {string|Date} dateString - Data/hora a ser formatada
 * @returns {string} Data/hora formatada como DD/MM/AAAA HH:MM
 */
export const formatDateTime = (dateString) => {
  if (!dateString) return ''
  
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString
  if (isNaN(date.getTime())) return ''
  
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

/**
 * Formata porcentagem
 * @param {number|string} value - Valor a ser formatado (0.02 = 2%)
 * @param {number} decimals - Número de casas decimais (padrão: 2, mínimo: 2)
 * @returns {string} Valor formatado como X,XX%
 */
export const formatPercentage = (value, decimals = 2) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return '0,00%'
  
  // Se valor >= 1, assume que já está em porcentagem (ex: 2 = 2%)
  // Se valor < 1, multiplica por 100 (ex: 0.02 = 2%)
  const percentValue = numValue >= 1 ? numValue : numValue * 100
  
  // Garante pelo menos 2 casas decimais para valores pequenos (ex: 0.15%)
  // Para valores maiores, usa o número de casas especificado
  const minDecimals = Math.max(decimals, 2)
  
  // Se o valor é muito pequeno (< 1%), mostra mais casas decimais automaticamente
  const finalDecimals = percentValue < 1 ? Math.max(minDecimals, 2) : minDecimals
  
  return `${percentValue.toFixed(finalDecimals).replace('.', ',')}%`
}

/**
 * Converte string de moeda para número
 * @param {string} currencyString - String no formato "R$ 1.234,56" ou "1.234,56"
 * @returns {number} Valor numérico
 */
export const parseCurrency = (currencyString) => {
  if (typeof currencyString === 'number') return currencyString
  if (!currencyString) return 0
  
  // Remove R$, espaços e pontos de milhar
  const cleanString = currencyString
    .replace('R$', '')
    .replace(/\s/g, '')
    .replace(/\./g, '')
    .replace(',', '.')
  
  return parseFloat(cleanString) || 0
}

/**
 * Formata valor numérico para exibição com vírgula como separador decimal
 * @param {number|string} value - Valor a ser formatado
 * @param {number} decimals - Número de casas decimais (padrão: 2)
 * @returns {string} Valor formatado (ex: "80000,50")
 */
export const formatDecimalInput = (value, decimals = 2) => {
  if (value === '' || value === null || value === undefined) return decimals === 2 ? '0,00' : '0'
  
  const numValue = typeof value === 'string' ? parseFloat(value.toString().replace(/\./g, '').replace(',', '.')) : value
  if (isNaN(numValue)) return decimals === 2 ? '0,00' : '0'
  
  // Formata com vírgula como separador decimal e sempre mostra o número de casas solicitado
  const formatted = numValue.toFixed(decimals).replace('.', ',')
  
  // Adiciona separadores de milhar na parte inteira
  const parts = formatted.split(',')
  const parteInteira = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  const parteDecimal = parts[1] || ''
  
  return parteDecimal ? `${parteInteira},${parteDecimal}` : parteInteira
}

/**
 * Converte valor formatado (com vírgula) para número
 * @param {string} value - Valor formatado (ex: "80000,50")
 * @returns {number} Valor numérico
 */
export const parseDecimalInput = (value) => {
  if (!value || value === '') return 0
  if (typeof value === 'number') return value
  
  // Remove pontos de milhar e substitui vírgula por ponto
  const cleanValue = value.toString()
    .replace(/\./g, '')  // Remove pontos (separadores de milhar)
    .replace(',', '.')   // Substitui vírgula por ponto (separador decimal)
  const numValue = parseFloat(cleanValue)
  
  return isNaN(numValue) ? 0 : numValue
}

/**
 * Formata valor enquanto digita, permitindo vírgula como separador decimal
 * e adicionando pontos como separadores de milhar automaticamente
 * @param {string} value - Valor digitado
 * @param {number} maxDecimals - Máximo de casas decimais (padrão: 2)
 * @returns {string} Valor formatado para exibição (ex: "80.000,50")
 */
export const formatDecimalWhileTyping = (value, maxDecimals = 2, forceDecimals = false, autoDecimal = false) => {
  // Se está vazio, retorna vazio (não força "0,00")
  if (!value || value === '') return ''
  
  // Remove tudo exceto números, vírgula e ponto
  let cleaned = value.replace(/[^\d,.]/g, '')
  
  // Se está vazio após limpeza, retorna vazio
  if (!cleaned) return ''
  
  // Se tem vírgula, remove pontos (vírgula tem prioridade como separador decimal)
  if (cleaned.includes(',')) {
    cleaned = cleaned.replace(/\./g, '')
    // Garante apenas uma vírgula
    const parts = cleaned.split(',')
    if (parts.length > 2) {
      cleaned = parts[0] + ',' + parts.slice(1).join('')
    }
    
    const parteInteira = parts[0] || ''
    let parteDecimal = parts[1] || ''
    
    // Limita casas decimais
    if (parteDecimal.length > maxDecimals) {
      parteDecimal = parteDecimal.substring(0, maxDecimals)
    }
    
    // Se não tem parte inteira mas tem decimal, mostra como "0,XX"
    if (!parteInteira && parteDecimal) {
      return `0,${parteDecimal}`
    }
    
    // Se não tem parte inteira, retorna vazio
    if (!parteInteira) return ''
    
    // Formata parte inteira com separadores de milhar
    const parteInteiraFormatada = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
    
    return parteDecimal ? `${parteInteiraFormatada},${parteDecimal}` : parteInteiraFormatada
  } else if (cleaned.includes('.')) {
    // Se tem ponto, converte para vírgula
    const parts = cleaned.split('.')
    
    // Se tem mais de um ponto, assume que são separadores de milhar
    if (parts.length > 2) {
      // Última parte pode ser decimal se tiver 1-2 dígitos
      const ultimaParte = parts[parts.length - 1]
      const penultimaParte = parts[parts.length - 2]
      
      // Se última parte tem 1-2 dígitos e penultima tem 3 dígitos, assume decimal
      if (ultimaParte.length <= maxDecimals && penultimaParte.length === 3) {
        const parteInteira = parts.slice(0, -1).join('')
        const parteDecimal = ultimaParte
        const parteInteiraFormatada = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
        return `${parteInteiraFormatada},${parteDecimal}`
      } else {
        // Todos são separadores de milhar, converte último ponto para vírgula
        const parteInteira = parts.slice(0, -1).join('')
        const parteDecimal = parts[parts.length - 1]
        const parteInteiraFormatada = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
        return parteDecimal ? `${parteInteiraFormatada},${parteDecimal}` : parteInteiraFormatada
      }
    } else {
      // Um ponto: converte para vírgula
      const parteInteira = parts[0] || ''
      const parteDepoisPonto = parts[1] || ''
      
      // Limita casas decimais
      if (parteDepoisPonto.length > maxDecimals) {
        parteDepoisPonto = parteDepoisPonto.substring(0, maxDecimals)
      }
      
      // Se não tem parte inteira mas tem decimal, mostra como "0,XX"
      if (!parteInteira && parteDepoisPonto) {
        return `0,${parteDepoisPonto}`
      }
      
      // Se não tem parte inteira, retorna vazio
      if (!parteInteira) return ''
      
      // Formata parte inteira com separadores de milhar
      const parteInteiraFormatada = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
      
      return parteDepoisPonto ? `${parteInteiraFormatada},${parteDepoisPonto}` : parteInteiraFormatada
    }
  } else {
    // Apenas números
    const numeroLimpo = cleaned.replace(/\./g, '')
    if (!numeroLimpo) return ''
    
    // Se autoDecimal está ativado, assume que os últimos 2 dígitos são centavos
    if (autoDecimal) {
      if (numeroLimpo.length >= 3) {
        // 3+ dígitos: últimos 2 são centavos
        const parteInteira = numeroLimpo.slice(0, -maxDecimals)
        const parteDecimal = numeroLimpo.slice(-maxDecimals)
        
        // Formata parte inteira com separadores de milhar
        const parteInteiraFormatada = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
        
        return `${parteInteiraFormatada},${parteDecimal}`
      } else if (numeroLimpo.length === 2) {
        // 2 dígitos: são centavos
        return `0,${numeroLimpo}`
      } else if (numeroLimpo.length === 1) {
        // 1 dígito: é centavo
        return `0,0${numeroLimpo}`
      }
    }
    
    // Se não tem autoDecimal ou tem menos de 3 dígitos sem autoDecimal, formata apenas com separadores de milhar
    const parteInteiraFormatada = numeroLimpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
    return parteInteiraFormatada
  }
}

/**
 * Garante que um valor decimal tenha exatamente 2 casas decimais
 * @param {number|string} value - Valor a ser arredondado
 * @returns {number} Valor com 2 casas decimais
 */
export const roundToTwoDecimals = (value) => {
  // Se já é número, usa diretamente
  if (typeof value === 'number') {
    return Math.round(value * 100) / 100
  }
  
  // Se é string, converte primeiro
  if (typeof value === 'string') {
    // Remove espaços e caracteres não numéricos (exceto ponto e vírgula)
    const cleanValue = value.trim().replace(/[^\d.,-]/g, '')
    // Substitui vírgula por ponto para parseFloat
    const normalizedValue = cleanValue.replace(',', '.')
    const numValue = parseFloat(normalizedValue)
    if (isNaN(numValue)) return 0
    return Math.round(numValue * 100) / 100
  }
  
  return 0
}

/**
 * Formata número com separadores de milhar
 * @param {number|string} value - Valor a ser formatado
 * @param {number} decimals - Número de casas decimais (padrão: 0)
 * @returns {string} Número formatado (ex: 1.234,56)
 */
export const formatNumber = (value, decimals = 0) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return '0'
  
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(numValue)
}

/**
 * Formata o nome de exibição de um item, incluindo informações da categoria
 * Para carros: sempre retorna "Marca Modelo - Placa"
 * @param {Object} item - Item a ser formatado
 * @returns {string} Nome formatado do item
 */
export const formatItemName = (item) => {
  if (!item) return 'Item Desconhecido'
  
  // Para carros, SEMPRE exibir Marca Modelo - Placa
  if (item.categoria === 'Carros') {
    const dados = item.dados_categoria || {}
    const marca = dados.Marca || dados.marca || item.carro?.marca || ''
    const modelo = dados.Modelo || dados.modelo || item.carro?.modelo || ''
    const placa = dados.Placa || dados.placa || item.carro?.placa || ''
    
    const nomeBase = [marca, modelo].filter(Boolean).join(' ')
    
    if (nomeBase && placa) {
      return `${nomeBase} - ${placa}`
    } else if (nomeBase) {
      return nomeBase
    } else if (placa) {
      return placa
    }
    return item.nome || 'Carro sem identificação'
  }
  
  // Para outros itens, adiciona identificadores se existirem
  const dadosCat = item.dados_categoria || {}
  const camposPrioridade = ['Marca', 'Modelo', 'Placa', 'Serial', 'Código']
  const camposChave = []
  
  for (const campo of camposPrioridade) {
    if (dadosCat[campo]) {
      camposChave.push(String(dadosCat[campo]))
    }
  }
  
  if (camposChave.length > 0) {
    return `${item.nome} - ${camposChave.join(' ')}`
  }
  
  return item.nome || 'Item sem nome'
}
