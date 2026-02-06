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
 * @param {number} decimals - Número de casas decimais (padrão: 2)
 * @returns {string} Valor formatado como X,XX%
 */
export const formatPercentage = (value, decimals = 2) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return '0,00%'
  
  // Se valor >= 1, assume que já está em porcentagem (ex: 2 = 2%)
  // Se valor < 1, multiplica por 100 (ex: 0.02 = 2%)
  const percentValue = numValue >= 1 ? numValue : numValue * 100
  
  return `${percentValue.toFixed(decimals).replace('.', ',')}%`
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
 * Garante que um valor decimal tenha exatamente 2 casas decimais
 * @param {number|string} value - Valor a ser arredondado
 * @returns {number} Valor com 2 casas decimais
 */
export const roundToTwoDecimals = (value) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return 0
  
  return Math.round(numValue * 100) / 100
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
