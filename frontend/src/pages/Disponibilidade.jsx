import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { disponibilidadeAPI, itensAPI, categoriasAPI } from '../services/api'
import { Search, CheckCircle2, XCircle, ChevronDown, ChevronUp, MapPin } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatItemName, formatDate } from '../utils/format'

export default function Disponibilidade() {
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [localizacoes, setLocalizacoes] = useState([])
  const [dataConsulta, setDataConsulta] = useState(new Date().toISOString().split('T')[0])
  const [modoConsulta, setModoConsulta] = useState('todos')
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas as Categorias')
  const [localizacaoFiltro, setLocalizacaoFiltro] = useState('Todas as Localizações')
  const [itemSelecionado, setItemSelecionado] = useState('')
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expandedGroups, setExpandedGroups] = useState({})

  useEffect(() => {
    loadItens()
    loadCategorias()
  }, [])

  useEffect(() => {
    if (itens.length > 0) {
      const locs = new Set()
      itens.forEach(item => {
        if (item.cidade && item.uf) {
          locs.add(`${item.cidade} - ${item.uf}`)
        }
      })
      setLocalizacoes(Array.from(locs).sort())
    }
  }, [itens])

  const loadItens = async () => {
    try {
      const response = await itensAPI.listar()
      setItens(response.data)
    } catch (error) {
      console.error('Erro ao carregar itens:', error)
    }
  }

  const loadCategorias = async () => {
    try {
      const response = await categoriasAPI.listar()
      setCategorias(response.data || [])
    } catch (error) {
      console.error('Erro ao carregar categorias:', error)
    }
  }

  const construirNomeItem = (item) => {
    let nome = item.nome
    const dadosCat = item.dados_categoria || {}
    const camposPrioridade = ['Marca', 'Modelo', 'Placa', 'Serial', 'Código']
    const camposChave = []
    
    for (const campo of camposPrioridade) {
      if (dadosCat[campo]) {
        camposChave.push(String(dadosCat[campo]))
      }
    }
    
    if (camposChave.length > 0) {
      nome = `${item.nome} - ${camposChave.join(' ')}`
    }
    
    if (item.categoria === 'Carros' && item.carro) {
      nome = `${item.carro.marca || ''} ${item.carro.modelo || ''} - ${item.carro.placa || ''}`.trim()
    }
    
    return nome
  }

  const obterCamposAgrupamento = (categoria, dadosCategoria) => {
    if (!dadosCategoria || !categoria) return null
    
    if (categoria === 'Carros') {
      return ['Marca', 'Modelo']
    }
    
    const camposPossiveis = ['Marca', 'Modelo', 'Tipo', 'Categoria', 'Fabricante']
    return Object.keys(dadosCategoria).filter(campo => camposPossiveis.includes(campo))
  }

  const obterValorAgrupamento = (item, camposAgrupamento) => {
    if (!camposAgrupamento || camposAgrupamento.length === 0) return null
    
    const dadosCat = item.dados_categoria || {}
    const valores = []
    
    camposAgrupamento.forEach(campo => {
      const valor = dadosCat[campo]
      if (valor) {
        valores.push(String(valor))
      }
    })
    
    return valores.length > 0 ? valores.join(' ') : item.nome
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResultado(null)

    try {
      const payload = {
        item_id: modoConsulta === 'especifico' && itemSelecionado ? parseInt(itemSelecionado) : null,
        data_consulta: dataConsulta,
        filtro_categoria: categoriaFiltro !== 'Todas as Categorias' ? categoriaFiltro : null,
        filtro_localizacao: localizacaoFiltro !== 'Todas as Localizações' ? localizacaoFiltro : null,
      }
      
      const response = await disponibilidadeAPI.verificar(payload)
      setResultado(response.data)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao verificar disponibilidade')
    } finally {
      setLoading(false)
    }
  }

  const toggleGroup = (groupId) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }))
  }

  const itensFiltrados = itens.filter(item => {
    if (categoriaFiltro !== 'Todas as Categorias' && item.categoria !== categoriaFiltro) {
      return false
    }
    if (localizacaoFiltro !== 'Todas as Localizações') {
      const [cidade, uf] = localizacaoFiltro.split(' - ')
      if (item.cidade !== cidade || item.uf !== uf) {
        return false
      }
    }
    return true
  })

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Verificar Disponibilidade</h1>
        <p className="text-dark-400">Consulte a disponibilidade de itens em datas específicas</p>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="card space-y-6"
      >
        <div>
          <label className="label">Data de Consulta *</label>
          <input
            type="date"
            value={dataConsulta}
            onChange={(e) => setDataConsulta(e.target.value)}
            required
            className="input"
          />
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Filtrar por Categoria</label>
            <select
              value={categoriaFiltro}
              onChange={(e) => setCategoriaFiltro(e.target.value)}
              className="input"
            >
              <option value="Todas as Categorias">Todas as Categorias</option>
              {categorias.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Filtrar por Localização</label>
            <select
              value={localizacaoFiltro}
              onChange={(e) => setLocalizacaoFiltro(e.target.value)}
              className="input"
            >
              <option value="Todas as Localizações">Todas as Localizações</option>
              {localizacoes.map(loc => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label mb-4 block">Tipo de Consulta</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                value="todos"
                checked={modoConsulta === 'todos'}
                onChange={(e) => setModoConsulta(e.target.value)}
                className="w-4 h-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-dark-300">Todos os Itens</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                value="especifico"
                checked={modoConsulta === 'especifico'}
                onChange={(e) => setModoConsulta(e.target.value)}
                className="w-4 h-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-dark-300">Item Específico</span>
            </label>
          </div>
        </div>

        {modoConsulta === 'especifico' && (
          <div>
            <label className="label">Selecione o Item *</label>
            <select
              value={itemSelecionado}
              onChange={(e) => setItemSelecionado(e.target.value)}
              required
              className="input"
            >
              <option value="">Selecione um item</option>
              {itensFiltrados.map(item => (
                <option key={item.id} value={item.id}>
                  {formatItemName(item)}
                </option>
              ))}
            </select>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
              Verificando...
            </>
          ) : (
            <>
              <Search size={20} />
              Verificar Disponibilidade
            </>
          )}
        </button>
      </motion.form>

      {resultado && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Resultado de item específico */}
          {resultado.item && (
            <div className="card">
              <h3 className="text-lg font-semibold text-dark-50 mb-2">
                Disponibilidade para "{resultado.item.nome}"
              </h3>
              
              {/* Mostra campos específicos da categoria */}
              {resultado.item.dados_categoria && Object.keys(resultado.item.dados_categoria).length > 0 && (
                <div className="mb-4 p-3 bg-dark-700/50 rounded-lg">
                  <p className="text-xs text-dark-500 mb-2">Detalhes:</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {Object.entries(resultado.item.dados_categoria).map(([campo, valor]) => {
                      // Pula campos vazios ou IDs
                      if (!valor || campo === 'ID' || campo === 'Item ID') {
                        return null
                      }
                      return (
                        <div key={campo} className="text-sm">
                          <span className="text-dark-400">{campo}:</span>{' '}
                          <span className="text-dark-200 font-medium">{valor}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
              
              {localizacaoFiltro !== 'Todas as Localizações' && (
                <div className="mb-4 p-3 bg-primary-600/20 border border-primary-600/30 rounded-lg">
                  <p className="text-sm text-primary-400">
                    📍 Filtro aplicado: Localização '{localizacaoFiltro}'
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="p-4 bg-dark-700/50 rounded-lg">
                  <p className="text-sm text-dark-400 mb-1">Total</p>
                  <p className="text-2xl font-bold text-dark-50">{resultado.quantidade_total}</p>
                </div>
                <div className="p-4 bg-dark-700/50 rounded-lg">
                  <p className="text-sm text-dark-400 mb-1">Total ocupado</p>
                  <p className="text-2xl font-bold text-yellow-500">
                    {(resultado.quantidade_comprometida || 0) + (resultado.quantidade_instalada || 0)}
                  </p>
                  <p className="text-xs text-dark-500 mt-1">
                    comprometido + instalado
                  </p>
                </div>
                <div className="p-4 bg-dark-700/50 rounded-lg">
                  <p className="text-sm text-dark-400 mb-1">Instalado em Carros</p>
                  <p className="text-2xl font-bold text-blue-500">{resultado.quantidade_instalada || 0}</p>
                </div>
                <div className="p-4 bg-dark-700/50 rounded-lg">
                  <p className="text-sm text-dark-400 mb-1">Disponível</p>
                  <p className={`text-2xl font-bold ${resultado.quantidade_disponivel > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {resultado.quantidade_disponivel}
                  </p>
                </div>
              </div>

              {resultado.compromissos_ativos && resultado.compromissos_ativos.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-md font-semibold text-dark-50 mb-4">Compromissos Ativos nesta Data</h4>
                  <div className="space-y-3">
                    {resultado.compromissos_ativos.map(comp => (
                      <div key={comp.id} className="p-4 bg-dark-700/50 rounded-lg border border-dark-700">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-dark-50">Compromisso #{comp.id}</p>
                            <p className="text-sm text-dark-400 mt-1">
                              {formatDate(comp.data_inicio)} a {formatDate(comp.data_fim)}
                            </p>
                            <p className="text-sm text-dark-400">Quantidade: {comp.quantidade}</p>
                            {comp.descricao && (
                              <p className="text-sm text-dark-400 mt-2">{comp.descricao}</p>
                            )}
                            {comp.contratante && (
                              <p className="text-sm text-dark-400 mt-1">Contratante: {comp.contratante}</p>
                            )}
                            {comp.cidade && comp.uf && (
                              <div className="flex items-center gap-1 mt-2 text-sm text-dark-400">
                                <MapPin size={14} />
                                <span>{comp.cidade} - {comp.uf}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Resultado de todos os itens com agrupamento */}
          {resultado.resultados && resultado.resultados.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-dark-50 mb-6">
                Disponibilidade em {formatDate(dataConsulta)}
              </h3>

              {categoriaFiltro !== 'Todas as Categorias' && (
                <div className="mb-4 p-3 bg-primary-600/20 border border-primary-600/30 rounded-lg">
                  <p className="text-sm text-primary-400">
                    📦 Filtro aplicado: Categoria '{categoriaFiltro}'
                  </p>
                </div>
              )}

              {localizacaoFiltro !== 'Todas as Localizações' && (
                <div className="mb-4 p-3 bg-primary-600/20 border border-primary-600/30 rounded-lg">
                  <p className="text-sm text-primary-400">
                    📍 Filtro aplicado: Localização '{localizacaoFiltro}'
                  </p>
                </div>
              )}

              {/* Agrupa resultados por categoria */}
              {(() => {
                const porCategoria = {}
                resultado.resultados.forEach(r => {
                  const cat = r.item.categoria || 'Sem Categoria'
                  if (!porCategoria[cat]) {
                    porCategoria[cat] = []
                  }
                  porCategoria[cat].push(r)
                })

                return Object.entries(porCategoria).map(([categoria, resultados]) => {
                  // Agrupa por campos de agrupamento se existirem
                  const primeiroItem = resultados[0].item
                  const camposAgrupamento = obterCamposAgrupamento(categoria, primeiroItem.dados_categoria)
                  
                  if (camposAgrupamento && camposAgrupamento.length > 0) {
                    const grupos = {}
                    resultados.forEach(r => {
                      const chave = obterValorAgrupamento(r.item, camposAgrupamento) || r.item.nome
                      if (!grupos[chave]) {
                        grupos[chave] = []
                      }
                      grupos[chave].push(r)
                    })

                    return Object.entries(grupos).map(([chaveGrupo, grupoResultados]) => {
                      const totalDisponivel = grupoResultados.reduce((sum, r) => sum + r.quantidade_disponivel, 0)
                      const totalOcupado = grupoResultados.reduce((sum, r) => sum + (r.quantidade_comprometida || 0) + (r.quantidade_instalada || 0), 0)
                      const totalItens = grupoResultados.length
                      const grupoId = `${categoria}-${chaveGrupo}`
                      const isExpanded = expandedGroups[grupoId]
                      
                      // Usa o nome do primeiro item como título principal
                      const primeiroItemGrupo = grupoResultados[0].item
                      const tituloGrupo = primeiroItemGrupo.nome

                      return (
                        <div key={grupoId} className="mb-4 border border-dark-700 rounded-lg overflow-hidden">
                          <button
                            onClick={() => toggleGroup(grupoId)}
                            className="w-full p-4 bg-dark-700/50 hover:bg-dark-700 transition-colors flex items-center justify-between"
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-xl">{categoria === 'Carros' ? '🚗' : '📦'}</span>
                              <div className="text-left">
                                <p className="font-semibold text-dark-50">{tituloGrupo}</p>
                                {chaveGrupo !== tituloGrupo && (
                                  <p className="text-xs text-dark-500 mb-1">{chaveGrupo}</p>
                                )}
                                <p className="text-sm text-dark-400">
                                  {totalDisponivel} disponível(is) de {totalItens} total
                                </p>
                              </div>
                            </div>
                            {isExpanded ? <ChevronUp className="text-dark-400" /> : <ChevronDown className="text-dark-400" />}
                          </button>

                          {isExpanded && (
                            <div className="p-4 space-y-4">
                              <div className="grid grid-cols-3 gap-4">
                                <div>
                                  <p className="text-sm text-dark-400">Total de Itens</p>
                                  <p className="text-xl font-bold text-dark-50">{totalItens}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-dark-400">Ocupados</p>
                                  <p className="text-xl font-bold text-yellow-500">{totalOcupado}</p>
                                </div>
                                <div>
                                  <p className="text-sm text-dark-400">Disponíveis</p>
                                  <p className="text-xl font-bold text-green-500">{totalDisponivel}</p>
                                </div>
                              </div>

                              <div className="border-t border-dark-700 pt-4 space-y-3">
                                {grupoResultados.map((r, idx) => {
                                  const item = r.item
                                  const dadosCat = item.dados_categoria || {}
                                  const camposId = ['Placa', 'Serial', 'Código', 'Código Único']
                                  const identificador = camposId.find(c => dadosCat[c]) || null

                                  return (
                                    <div key={idx} className="p-3 bg-dark-800 rounded-lg">
                                      <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                          {identificador ? (
                                            <p className="font-medium text-dark-50">
                                              {identificador}: {dadosCat[identificador]}
                                            </p>
                                          ) : (
                                            <p className="font-medium text-dark-50">{item.nome}</p>
                                          )}
                                          
                                          {/* Mostra campos específicos da categoria */}
                                          {Object.keys(dadosCat).length > 0 && (
                                            <div className="mt-2 space-y-1">
                                              {Object.entries(dadosCat).map(([campo, valor]) => {
                                                // Pula campos que já estão sendo mostrados como identificador ou campos vazios
                                                if (campo === identificador || !valor || campo === 'ID' || campo === 'Item ID') {
                                                  return null
                                                }
                                                return (
                                                  <div key={campo} className="text-xs text-dark-400">
                                                    <span className="text-dark-500">{campo}:</span> <span className="text-dark-300">{valor}</span>
                                                  </div>
                                                )
                                              })}
                                            </div>
                                          )}
                                          
                                          <div className="flex items-center gap-4 mt-2 text-sm">
                                            <span className={`font-medium ${r.quantidade_disponivel > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                              {r.quantidade_disponivel > 0 ? '✅ Disponível' : '❌ Indisponível'}
                                            </span>
                                            {((r.quantidade_comprometida || 0) + (r.quantidade_instalada || 0)) > 0 && (
                                              <span className="text-dark-400">
                                                Ocupado: {(r.quantidade_comprometida || 0) + (r.quantidade_instalada || 0)}
                                              </span>
                                            )}
                                          </div>
                                          {item.cidade && item.uf && (
                                            <div className="flex items-center gap-1 mt-2 text-sm text-dark-400">
                                              <MapPin size={12} />
                                              <span>{item.cidade} - {item.uf}</span>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })
                  } else {
                    // Sem agrupamento, mostra lista simples
                    return (
                      <div key={categoria} className="mb-6">
                        <h4 className="text-md font-semibold text-dark-50 mb-4">
                          {categoria === 'Carros' ? '🚗' : '📦'} {categoria}
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {resultados.map((r, idx) => {
                            const dadosCat = r.item.dados_categoria || {}
                            
                            return (
                              <div key={idx} className="p-4 bg-dark-700/50 rounded-lg border border-dark-700">
                                <h5 className="font-semibold text-dark-50 mb-2">{r.item.nome}</h5>
                                
                                {/* Mostra campos específicos da categoria */}
                                {Object.keys(dadosCat).length > 0 && (
                                  <div className="mb-3 space-y-1">
                                    {Object.entries(dadosCat).map(([campo, valor]) => {
                                      // Pula campos vazios ou IDs
                                      if (!valor || campo === 'ID' || campo === 'Item ID') {
                                        return null
                                      }
                                      return (
                                        <div key={campo} className="text-xs text-dark-400">
                                          <span className="text-dark-500">{campo}:</span> <span className="text-dark-300">{valor}</span>
                                        </div>
                                      )
                                    })}
                                  </div>
                                )}
                                
                                <div className="flex items-center justify-between">
                                  <span className="text-sm text-dark-400">Disponível:</span>
                                  <span className={`font-bold ${r.quantidade_disponivel > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {r.quantidade_disponivel}
                                  </span>
                                </div>
                                {((r.quantidade_comprometida || 0) + (r.quantidade_instalada || 0)) > 0 && (
                                  <div className="flex items-center justify-between mt-2">
                                    <span className="text-sm text-dark-400">Ocupado:</span>
                                    <span className="font-medium text-yellow-500">{(r.quantidade_comprometida || 0) + (r.quantidade_instalada || 0)}</span>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  }
                })
              })()}
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
