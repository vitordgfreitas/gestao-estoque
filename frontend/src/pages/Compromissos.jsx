import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI, disponibilidadeAPI } from '../services/api'
import api from '../services/api'
import { Calendar, Plus, Info, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatItemName } from '../utils/format'
import { getCidadesPorUF, ESTADOS } from '../utils/municipios'

const UFS = ESTADOS.map(e => e.sigla) // Para compatibilidade com código existente

export default function Compromissos() {
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [categoriaFiltro, setCategoriaFiltro] = useState('')
  const [itensFiltrados, setItensFiltrados] = useState([])
  const [itemSelecionado, setItemSelecionado] = useState(null)
  const [quantidadeFixa, setQuantidadeFixa] = useState(false)
  const [pecasSelecionadas, setPecasSelecionadas] = useState([])
  const [cidadesDisponiveis, setCidadesDisponiveis] = useState([])
  const [formData, setFormData] = useState({
    tipo_compromisso: 'itens_alugados',
    item_id: '',
    peca_id: '',
    carro_id: '',
    quantidade: 1,
    data_inicio: new Date().toISOString().split('T')[0],
    data_fim: new Date().toISOString().split('T')[0],
    descricao: '',
    cidade: '',
    uf: 'DF',
    endereco: '',
    contratante: '',
  })
  const [loading, setLoading] = useState(false)
  const [loadingItens, setLoadingItens] = useState(true)

  useEffect(() => {
    loadCategorias()
    loadItens()
  }, [])

  // Filtra itens quando categoria muda
  useEffect(() => {
    if (categoriaFiltro && categoriaFiltro !== 'Todas as Categorias') {
      const filtrados = itens.filter(item => 
        (item.categoria || '').trim() === categoriaFiltro.trim()
      )
      setItensFiltrados(filtrados)
    } else {
      setItensFiltrados(itens)
    }
    // Limpa item selecionado quando categoria muda
    setFormData(prev => ({ ...prev, item_id: '' }))
    setItemSelecionado(null)
  }, [categoriaFiltro, itens])

  // Atualiza cidades quando UF muda
  useEffect(() => {
    if (formData.uf) {
      setCidadesDisponiveis(getCidadesPorUF(formData.uf))
    } else {
      setCidadesDisponiveis([])
    }
  }, [formData.uf])

  // Atualiza quantidade fixa quando item selecionado muda
  useEffect(() => {
    if (formData.item_id) {
      const item = itensFiltrados.find(i => i.id === parseInt(formData.item_id))
      if (item) {
        setItemSelecionado(item)
        const dadosCat = item.dados_categoria || {}
        const camposItemUnico = ['Placa', 'Serial', 'Código Único', 'Código', 'ID Único', 'Número de Série']
        const temCampoItemUnico = Object.keys(dadosCat).some(campo => camposItemUnico.includes(campo))
        const isCarros = item.categoria === 'Carros'
        const fixa = isCarros || temCampoItemUnico
        setQuantidadeFixa(fixa)
        if (fixa) {
          setFormData(prev => ({ ...prev, quantidade: 1 }))
        }
      }
    } else {
      setItemSelecionado(null)
      setQuantidadeFixa(false)
    }
  }, [formData.item_id, itensFiltrados])

  const loadCategorias = async () => {
    try {
      const response = await categoriasAPI.listar()
      const cats = response.data || []
      setCategorias(cats)
      if (cats.length > 0) {
        setCategoriaFiltro(cats[0])
      } else {
        setCategoriaFiltro('Todas as Categorias')
      }
    } catch (error) {
      console.error('Erro ao carregar categorias:', error)
      setCategorias([])
      setCategoriaFiltro('Todas as Categorias')
    }
  }

  const loadItens = async () => {
    try {
      setLoadingItens(true)
      const response = await itensAPI.listar()
      setItens(response.data)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao carregar itens')
    } finally {
      setLoadingItens(false)
    }
  }


  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (formData.tipo_compromisso === 'pecas_carro') {
        // Associar múltiplas peças ao carro
        if (pecasSelecionadas.length === 0) {
          toast.error('Adicione pelo menos uma peça antes de salvar')
          setLoading(false)
          return
        }

        const promises = pecasSelecionadas.map(peca =>
          api.post('/api/pecas-carros', {
            peca_id: parseInt(peca.peca_id),
            carro_id: parseInt(formData.carro_id),
            quantidade: parseInt(peca.quantidade),
            data_instalacao: formData.data_inicio,
            observacoes: formData.descricao || ''
          })
        )

        await Promise.all(promises)
        toast.success(`${pecasSelecionadas.length} peça(s) associada(s) ao carro com sucesso!`)
        
        setFormData({
          tipo_compromisso: 'pecas_carro',
          item_id: '',
          peca_id: '',
          carro_id: '',
          quantidade: 1,
          data_inicio: new Date().toISOString().split('T')[0],
          data_fim: new Date().toISOString().split('T')[0],
          descricao: '',
          cidade: '',
          uf: 'DF',
          endereco: '',
          contratante: '',
        })
        setPecasSelecionadas([])
      } else {
        // Fluxo original para itens alugados
        // Verifica disponibilidade antes de criar
        const disponibilidade = await disponibilidadeAPI.verificar({
          item_id: parseInt(formData.item_id),
          data_consulta: formData.data_inicio,
        })

        const disponivelMinimo = disponibilidade.data.quantidade_disponivel
        const quantidadeSolicitada = parseInt(formData.quantidade)

        if (disponivelMinimo < quantidadeSolicitada) {
          toast.error(`Quantidade insuficiente! Disponível: ${disponivelMinimo}, Solicitado: ${quantidadeSolicitada}`)
          setLoading(false)
          return
        }

        await compromissosAPI.criar({
          ...formData,
          item_id: parseInt(formData.item_id),
          quantidade: parseInt(formData.quantidade),
        })
        toast.success('Compromisso registrado com sucesso!')
        setFormData({
          tipo_compromisso: 'itens_alugados',
          item_id: '',
          peca_id: '',
          carro_id: '',
          quantidade: 1,
          data_inicio: new Date().toISOString().split('T')[0],
          data_fim: new Date().toISOString().split('T')[0],
          descricao: '',
          cidade: '',
          uf: 'DF',
          endereco: '',
          contratante: '',
        })
        setItemSelecionado(null)
        setQuantidadeFixa(false)
      }
    } catch (error) {
      if (error.response?.status === 400 && error.response?.data?.detail?.includes('insuficiente')) {
        toast.error(error.response.data.detail)
      } else {
        toast.error(error.response?.data?.detail || 'Erro ao associar peça/registrar compromisso')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const value = e.target.value
    setFormData({
      ...formData,
      [e.target.name]: value
    })

    if (e.target.name === 'data_inicio' && value > formData.data_fim) {
      setFormData(prev => ({ ...prev, data_fim: value }))
    }
  }

  if (loadingItens) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Registrar Compromisso</h1>
        <p className="text-dark-400">Registre um novo aluguel ou compromisso para um item do estoque</p>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="card space-y-6"
      >
        {/* Tipo de Compromisso */}
        <div>
          <label className="label">Tipo de Compromisso *</label>
          <select
            value={formData.tipo_compromisso}
            onChange={(e) => {
              setFormData({ 
                ...formData, 
                tipo_compromisso: e.target.value,
                item_id: '',
                peca_id: '',
                carro_id: ''
              })
              setItemSelecionado(null)
            }}
            className="input"
            required
          >
            <option value="itens_alugados">Itens Alugados</option>
            <option value="pecas_carro">Peças de Carro</option>
          </select>
        </div>

        {formData.tipo_compromisso === 'pecas_carro' ? (
          <>
            {/* Interface para Peças de Carro */}
            <div>
              <label className="label">Carro *</label>
              <select
                value={formData.carro_id}
                onChange={(e) => setFormData({ ...formData, carro_id: e.target.value })}
                required
                className="input"
              >
                <option value="">Selecione um carro</option>
                {itens.filter(i => i.categoria === 'Carros').map(carro => {
                  const marca = carro.dados_categoria?.Marca || carro.carro?.marca || ''
                  const modelo = carro.dados_categoria?.Modelo || carro.carro?.modelo || ''
                  const placa = carro.dados_categoria?.Placa || carro.carro?.placa || ''
                  const nome = [marca, modelo].filter(Boolean).join(' ') || carro.nome
                  return (
                    <option key={carro.id} value={carro.id}>
                      {nome}{placa ? ` - ${placa}` : ''}
                    </option>
                  )
                })}
              </select>
            </div>

            {/* Adicionar Peças */}
            <div className="space-y-4 p-4 bg-dark-700/30 rounded-lg border border-dark-600">
              <h3 className="text-lg font-semibold text-dark-50">Adicionar Peças</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="label">Peça</label>
                  <select
                    value={formData.peca_id}
                    onChange={(e) => setFormData({ ...formData, peca_id: e.target.value })}
                    className="input"
                  >
                    <option value="">Selecione uma peça</option>
                    {itens.filter(i => i.categoria === 'Peças de Carro').map(peca => (
                      <option key={peca.id} value={peca.id}>
                        {peca.nome}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Quantidade</label>
                  <input
                    type="number"
                    value={formData.quantidade}
                    onChange={(e) => setFormData({ ...formData, quantidade: e.target.value })}
                    min="1"
                    className="input"
                  />
                </div>

                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={() => {
                      if (!formData.peca_id) {
                        toast.error('Selecione uma peça')
                        return
                      }
                      const peca = itens.find(i => i.id === parseInt(formData.peca_id))
                      const jaAdicionada = pecasSelecionadas.find(p => p.peca_id === formData.peca_id)
                      
                      if (jaAdicionada) {
                        toast.error('Peça já adicionada à lista')
                        return
                      }

                      setPecasSelecionadas([...pecasSelecionadas, {
                        peca_id: formData.peca_id,
                        peca_nome: peca?.nome || '',
                        quantidade: formData.quantidade
                      }])
                      setFormData({ ...formData, peca_id: '', quantidade: 1 })
                      toast.success('Peça adicionada à lista')
                    }}
                    className="btn btn-primary w-full flex items-center justify-center gap-2"
                  >
                    <Plus size={20} />
                    Adicionar
                  </button>
                </div>
              </div>

              {/* Lista de Peças Selecionadas */}
              {pecasSelecionadas.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-sm font-semibold text-dark-300">Peças a Instalar ({pecasSelecionadas.length})</h4>
                  <div className="space-y-2">
                    {pecasSelecionadas.map((peca, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-dark-800 rounded-lg border border-dark-600">
                        <div>
                          <span className="text-dark-50 font-medium">{peca.peca_nome}</span>
                          <span className="text-dark-400 text-sm ml-2">x{peca.quantidade}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setPecasSelecionadas(pecasSelecionadas.filter((_, i) => i !== index))
                            toast.success('Peça removida da lista')
                          }}
                          className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                          title="Remover"
                        >
                          <X size={16} className="text-red-400" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Data de Instalação *</label>
                <input
                  type="date"
                  value={formData.data_inicio}
                  onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                  required
                  className="input"
                />
              </div>
            </div>

            <div>
              <label className="label">Observações</label>
              <textarea
                value={formData.descricao}
                onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                rows="3"
                className="input resize-none"
                placeholder="Ex: Peça original, instalada na revisão..."
              />
            </div>
          </>
        ) : (
          <>
            {/* Interface original para itens alugados */}
        {/* Filtro por categoria */}
        <div>
          <label className="label">Categoria *</label>
          <select
            value={categoriaFiltro}
            onChange={(e) => setCategoriaFiltro(e.target.value)}
            required
            className="input"
          >
            <option value="Todas as Categorias">Todas as Categorias</option>
            {categorias.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        {/* Seleção do item */}
        <div>
          <label className="label">Item *</label>
          {itensFiltrados.length === 0 ? (
            <div className="p-4 bg-yellow-600/20 border border-yellow-600/30 rounded-lg">
              <p className="text-sm text-yellow-400">
                ⚠️ Não há itens cadastrados na categoria selecionada.
              </p>
            </div>
          ) : (
            <select
              name="item_id"
              value={formData.item_id}
              onChange={handleChange}
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
          )}
        </div>

        {/* Quantidade */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Quantidade *</label>
            {quantidadeFixa ? (
              <div>
                <input
                  type="number"
                  name="quantidade"
                  value={1}
                  disabled
                  className="input opacity-50"
                />
                <div className="mt-2 p-3 bg-primary-600/20 border border-primary-600/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Info className="text-primary-400 mt-0.5" size={16} />
                    <p className="text-xs text-primary-400">
                      Para {itemSelecionado?.categoria || 'esta categoria'}, a quantidade é sempre 1 (cada item é único).
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <input
                type="number"
                name="quantidade"
                value={formData.quantidade}
                onChange={handleChange}
                required
                min="1"
                max={itemSelecionado?.quantidade_total || undefined}
                className="input"
              />
            )}
          </div>

          <div>
            <label className="label">Data de Início *</label>
            <input
              type="date"
              name="data_inicio"
              value={formData.data_inicio}
              onChange={handleChange}
              required
              className="input"
            />
          </div>

          <div>
            <label className="label">Data de Fim *</label>
            <input
              type="date"
              name="data_fim"
              value={formData.data_fim}
              onChange={handleChange}
              required
              min={formData.data_inicio}
              className="input"
            />
          </div>
        </div>

        <div>
          <label className="label">Descrição (opcional)</label>
          <textarea
            name="descricao"
            value={formData.descricao}
            onChange={handleChange}
            rows="3"
            className="input resize-none"
            placeholder="Ex: Evento corporativo, Licitação pública..."
          />
        </div>

        <div className="space-y-4 pt-6 border-t border-dark-700">
          <h3 className="text-lg font-semibold text-dark-50 flex items-center gap-2">
            <div className="w-1 h-6 bg-primary-500 rounded-full"></div>
            Localização do Compromisso
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">UF *</label>
              <select
                name="uf"
                value={formData.uf}
                onChange={handleChange}
                required
                className="input"
              >
                {UFS.map(uf => (
                  <option key={uf} value={uf}>{uf}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Cidade *</label>
              <select
                name="cidade"
                value={formData.cidade}
                onChange={handleChange}
                required
                className="input"
              >
                <option value="">Selecione uma cidade</option>
                {cidadesDisponiveis.map(cidade => (
                  <option key={cidade} value={cidade}>{cidade}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="label">Endereço (opcional)</label>
            <input
              type="text"
              name="endereco"
              value={formData.endereco}
              onChange={handleChange}
              className="input"
              placeholder="Ex: Rua das Flores, 123 - Centro..."
            />
          </div>
        </div>

        <div>
          <label className="label">Contratante (opcional)</label>
          <input
            type="text"
            name="contratante"
            value={formData.contratante}
            onChange={handleChange}
            className="input"
            placeholder="Ex: Empresa ABC, Prefeitura de Cidade..."
          />
        </div>

          </>
        )}

        {/* Button moved outside conditional */}
        <button
          type="submit"
          disabled={loading || (formData.tipo_compromisso === 'itens_alugados' && itensFiltrados.length === 0)}
          className="btn btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
              Salvando...
            </>
          ) : (
            <>
              <Calendar size={20} />
              {formData.tipo_compromisso === 'pecas_carro' ? 'Associar Peça ao Carro' : 'Registrar Compromisso'}
            </>
          )}
        </button>
      </motion.form>
    </div>
  )
}
