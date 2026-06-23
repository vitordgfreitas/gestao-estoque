import municipiosData from '../data/municipios.json'

/**
 * Lista completa dos estados brasileiros
 */
export const ESTADOS = [
  { sigla: 'AC', nome: 'Acre' },
  { sigla: 'AL', nome: 'Alagoas' },
  { sigla: 'AP', nome: 'Amapá' },
  { sigla: 'AM', nome: 'Amazonas' },
  { sigla: 'BA', nome: 'Bahia' },
  { sigla: 'CE', nome: 'Ceará' },
  { sigla: 'DF', nome: 'Distrito Federal' },
  { sigla: 'ES', nome: 'Espírito Santo' },
  { sigla: 'GO', nome: 'Goiás' },
  { sigla: 'MA', nome: 'Maranhão' },
  { sigla: 'MT', nome: 'Mato Grosso' },
  { sigla: 'MS', nome: 'Mato Grosso do Sul' },
  { sigla: 'MG', nome: 'Minas Gerais' },
  { sigla: 'PA', nome: 'Pará' },
  { sigla: 'PB', nome: 'Paraíba' },
  { sigla: 'PR', nome: 'Paraná' },
  { sigla: 'PE', nome: 'Pernambuco' },
  { sigla: 'PI', nome: 'Piauí' },
  { sigla: 'RJ', nome: 'Rio de Janeiro' },
  { sigla: 'RN', nome: 'Rio Grande do Norte' },
  { sigla: 'RS', nome: 'Rio Grande do Sul' },
  { sigla: 'RO', nome: 'Rondônia' },
  { sigla: 'RR', nome: 'Roraima' },
  { sigla: 'SC', nome: 'Santa Catarina' },
  { sigla: 'SP', nome: 'São Paulo' },
  { sigla: 'SE', nome: 'Sergipe' },
  { sigla: 'TO', nome: 'Tocantins' }
]

/**
 * Array simples com as siglas dos estados (compatível com código existente)
 */
export const UFS = ESTADOS.map(e => e.sigla)

/**
 * Retorna a lista de cidades de um estado específico
 * @param {string} uf - Sigla do estado (ex: 'SP', 'MG')
 * @returns {string[]} Array com nomes das cidades ordenadas alfabeticamente
 */
export const getCidadesPorUF = (uf) => {
  if (!uf) return []
  return municipiosData[uf] || []
}

/**
 * Retorna todos os municípios organizados por UF
 * @returns {Object} Objeto com UF como chave e array de cidades como valor
 */
export const getAllMunicipios = () => {
  return municipiosData
}

/**
 * Retorna o nome completo do estado a partir da sigla
 * @param {string} sigla - Sigla do estado (ex: 'SP')
 * @returns {string} Nome completo do estado (ex: 'São Paulo')
 */
export const getNomeEstado = (sigla) => {
  const estado = ESTADOS.find(e => e.sigla === sigla)
  return estado ? estado.nome : sigla
}

/**
 * Busca municípios por termo de pesquisa (útil para autocomplete)
 * @param {string} termo - Termo de busca
 * @param {string} uf - (Opcional) Filtrar por estado
 * @returns {Array<{cidade: string, uf: string}>} Array de objetos com cidade e UF
 */
export const buscarMunicipios = (termo, uf = null) => {
  const resultados = []
  const termoLower = termo.toLowerCase()
  
  const ufs = uf ? [uf] : Object.keys(municipiosData)
  
  for (const estado of ufs) {
    const cidades = municipiosData[estado] || []
    for (const cidade of cidades) {
      if (cidade.toLowerCase().includes(termoLower)) {
        resultados.push({ cidade, uf: estado })
      }
    }
  }
  
  return resultados
}
