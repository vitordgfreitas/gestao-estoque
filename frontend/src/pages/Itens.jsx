import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { itensAPI, categoriasAPI } from '../services/api'
import { Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import { getCidadesPorUF, ESTADOS } from '../utils/municipios'

const MARCAS_CARROS = [
  'Fiat', 'Volkswagen', 'Chevrolet', 'Ford', 'Toyota', 'Honda', 'Hyundai', 
  'Renault', 'Nissan', 'Peugeot', 'Citroën', 'Jeep', 'Mitsubishi', 'Kia',
  'BMW', 'Mercedes-Benz', 'Audi', 'Volvo', 'Land Rover', 'Jaguar', 'Porsche',
  'Subaru', 'Suzuki', 'Chery', 'JAC', 'Troller', 'RAM', 'Dodge', 'Chrysler',
  'Mini', 'Smart', 'BYD', 'GWM', 'Caoa Chery', 'Outra'
]

export default function Itens() {
  const [categorias, setCategorias] = useState([])
  const [camposCategoria, setCamposCategoria] = useState([])
  const [loadingCategorias, setLoadingCategorias] = useState(true)
  const [cidadesDisponiveis, setCidadesDisponiveis] = useState([])
  const [formData, setFormData] = useState({
    nome: '',
    quantidade_total: 1,
    categoria: '',
    descricao: '',
    cidade: '',
    uf: 'SP',
    endereco: '',
  })
  const [camposDinamicos, setCamposDinamicos] = useState({})
  const [loading, setLoading] = useState(false)

  // Carrega categorias ao montar componente
  useEffect(() => {
    loadCategorias()
  }, [])

  // Carrega campos quando categoria muda
  useEffect(() => {
    if (formData.categoria) {
      loadCamposCategoria(formData.categoria)
    } else {
      setCamposCategoria([])
      setCamposDinamicos({})
    }
  }, [formData.categoria])

  // Atualiza cidades quando UF muda
  useEffect(() => {
    if (formData.uf) {
      setCidadesDisponiveis(getCidadesPorUF(formData.uf))
    } else {
      setCidadesDisponiveis([])
    }
  }, [formData.uf])

  const loadCategorias = async () => {
    try {
      const response = await categoriasAPI.listar()
      const cats = response.data
      setCategorias(cats)
      if (cats.length > 0 && !formData.categoria) {
        setFormData(prev => ({ ...prev, categoria: cats[0] }))
      }
    } catch (error) {
      console.error('Erro ao carregar categorias:', error)
      toast.error('Erro ao carregar categorias')
      // Fallback para categorias padrão
      setCategorias(['Estrutura de Evento', 'Carros'])
      if (!formData.categoria) {
        setFormData(prev => ({ ...prev, categoria: 'Estrutura de Evento' }))
      }
    } finally {
      setLoadingCategorias(false)
    }
  }

  const loadCamposCategoria = async (categoria) => {
    try {
      const response = await categoriasAPI.obterCampos(categoria)
      const campos = response.data || []
      setCamposCategoria(campos)
      
      // Inicializa campos dinâmicos vazios
      const novosCampos = {}
      campos.forEach(campo => {
        novosCampos[campo] = ''
      })
      setCamposDinamicos(novosCampos)
    } catch (error) {
      console.error('Erro ao carregar campos da categoria:', error)
      setCamposCategoria([])
      setCamposDinamicos({})
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))

    // Se mudou categoria, limpa campos dinâmicos
    if (name === 'categoria') {
      setCamposDinamicos({})
    }

    // Para Carros, gera nome automaticamente
    if (name === 'categoria' && value === 'Carros') {
      setFormData(prev => ({ ...prev, quantidade_total: 1 }))
    }
  }

  const handleCampoDinamicoChange = (campo, value) => {
    setCamposDinamicos(prev => ({
      ...prev,
      [campo]: value
    }))

    // Para Carros, gera nome automaticamente quando marca e modelo são preenchidos
    if (formData.categoria === 'Carros') {
      const marca = campo === 'Marca' ? value : camposDinamicos['Marca'] || ''
      const modelo = campo === 'Modelo' ? value : camposDinamicos['Modelo'] || ''
      if (marca && modelo) {
        setFormData(prev => ({ ...prev, nome: `${marca} ${modelo}`.trim() }))
      }
    }
  }

  const inferirTipoCampo = (campoNome) => {
    const campoLower = campoNome.toLowerCase()
    if (campoLower.includes('ano') || campoLower.includes('year')) {
      return 'number'
    }
    if (campoLower.includes('quantidade') || campoLower.includes('qtd') || campoLower.includes('amount')) {
      return 'number'
    }
    if (campoLower.includes('data') || campoLower.includes('date')) {
      return 'date'
    }
    return 'text'
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Validação básica
      if (!formData.nome.trim() || !formData.cidade.trim() || !formData.uf) {
        toast.error('Por favor, preencha os campos obrigatórios')
        setLoading(false)
        return
      }

      // Valida campos dinâmicos obrigatórios
      for (const campo of camposCategoria) {
        const valor = camposDinamicos[campo]
        if (!valor || (typeof valor === 'string' && !valor.trim())) {
          toast.error(`Por favor, preencha o campo: ${campo}`)
          setLoading(false)
          return
        }
      }

      // Prepara payload
      const payload = {
        ...formData,
        quantidade_total: parseInt(formData.quantidade_total),
      }

      // Adiciona campos_categoria se houver campos dinâmicos
      if (camposCategoria.length > 0 && Object.keys(camposDinamicos).length > 0) {
        const camposCat = {}
        camposCategoria.forEach(campo => {
          let valor = camposDinamicos[campo]
          // Converte datas para string ISO
          if (valor instanceof Date) {
            valor = valor.toISOString().split('T')[0]
          }
          camposCat[campo] = valor
        })
        payload.campos_categoria = camposCat
      }

      // Para Carros sem campos_categoria (compatibilidade), usa campos antigos
      if (formData.categoria === 'Carros' && camposCategoria.length === 0) {
        payload.placa = camposDinamicos['Placa'] || ''
        payload.marca = camposDinamicos['Marca'] || ''
        payload.modelo = camposDinamicos['Modelo'] || ''
        payload.ano = camposDinamicos['Ano'] ? parseInt(camposDinamicos['Ano']) : null
      }

      await itensAPI.criar(payload)
      toast.success('Item registrado com sucesso!')
      
      // Reset form
      setFormData({
        nome: '',
        quantidade_total: formData.categoria === 'Carros' ? 1 : 1,
        categoria: formData.categoria, // Mantém categoria selecionada
        descricao: '',
        cidade: '',
        uf: 'SP',
        endereco: '',
      })
      setCamposDinamicos({})
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao registrar item')
    } finally {
      setLoading(false)
    }
  }

  const renderCampoDinamico = (campo) => {
    const tipo = inferirTipoCampo(campo)
    const valor = camposDinamicos[campo] || ''

    // Tratamento especial para Carros
    if (formData.categoria === 'Carros') {
      if (campo === 'Marca') {
        return (
          <select
            value={valor}
            onChange={(e) => handleCampoDinamicoChange(campo, e.target.value)}
            required
            className="input"
          >
            <option value="">Selecione a marca</option>
            {MARCAS_CARROS.map(marca => (
              <option key={marca} value={marca}>{marca}</option>
            ))}
          </select>
        )
      }
      if (campo === 'Ano') {
        return (
          <input
            type="number"
            value={valor}
            onChange={(e) => handleCampoDinamicoChange(campo, e.target.value)}
            required
            min="1900"
            max="2100"
            className="input"
            placeholder="Ex: 2020"
          />
        )
      }
      if (campo === 'Placa') {
        return (
          <input
            type="text"
            value={valor}
            onChange={(e) => handleCampoDinamicoChange(campo, e.target.value.toUpperCase())}
            required
            maxLength={10}
            className="input"
            placeholder="ABC-1234"
          />
        )
      }
    }

    // Campos genéricos baseados no tipo inferido
    switch (tipo) {
      case 'number':
        if (campo.toLowerCase().includes('ano')) {
          return (
            <input
              type="number"
              value={valor}
              onChange={(e) => handleCampoDinamicoChange(campo, e.target.value)}
              required
              min="1900"
              max="2100"
              className="input"
            />
          )
        }
        return (
          <input
            type="number"
            value={valor}
            onChange={(e) => handleCampoDinamicoChange(campo, e.target.value)}
            required
            min="1"
            className="input"
          />
        )
      case 'date':
        return (
          <input
            type="date"
            value={valor}
            onChange={(e) => handleCampoDinamicoChange(campo, e.target.value)}
            required
            className="input"
          />
        )
      default:
        return (
          <input
            type="text"
            value={valor}
            onChange={(e) => handleCampoDinamicoChange(campo, e.target.value)}
            required
            className="input"
            placeholder={`Digite ${campo.toLowerCase()}...`}
          />
        )
    }
  }

  if (loadingCategorias) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  const isCarros = formData.categoria === 'Carros'
  const temCamposCategoria = camposCategoria.length > 0
  const quantidadeFixa = isCarros || camposCategoria.some(c => 
    ['Placa', 'Serial', 'Código Único', 'Código', 'ID Único'].includes(c)
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Registrar Novo Item</h1>
        <p className="text-dark-400">Preencha os campos abaixo para cadastrar um novo item no sistema</p>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="card space-y-6"
      >
        {/* Informações Básicas */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-dark-50 flex items-center gap-2">
            <div className="w-1 h-6 bg-primary-500 rounded-full"></div>
            Informações Básicas
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Categoria *</label>
              <select
                name="categoria"
                value={formData.categoria}
                onChange={handleChange}
                required
                className="input"
              >
                {categorias.length === 0 ? (
                  <>
                    <option value="Estrutura de Evento">Estrutura de Evento</option>
                    <option value="Carros">Carros</option>
                  </>
                ) : (
                  categorias.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))
                )}
              </select>
            </div>

            {!quantidadeFixa && (
              <div>
                <label className="label">Quantidade Total *</label>
                <input
                  type="number"
                  name="quantidade_total"
                  value={formData.quantidade_total}
                  onChange={handleChange}
                  required
                  min="1"
                  className="input"
                />
              </div>
            )}
          </div>

          {quantidadeFixa && (
            <div className="p-4 bg-primary-600/20 border border-primary-600/30 rounded-lg">
              <p className="text-sm text-primary-400">
                ℹ️ Para {formData.categoria}, a quantidade é sempre 1 (cada item é único).
              </p>
            </div>
          )}

          {/* Campos específicos da categoria */}
          {temCamposCategoria && (
            <div className="space-y-4 pt-4 border-t border-dark-700">
              <h4 className="text-md font-semibold text-dark-50">
                Detalhes de {formData.categoria}
              </h4>
              {camposCategoria.map(campo => (
                <div key={campo}>
                  <label className="label">{campo} *</label>
                  {renderCampoDinamico(campo)}
                </div>
              ))}
            </div>
          )}

          {/* Campos hardcoded para Carros (compatibilidade) */}
          {isCarros && !temCamposCategoria && (
            <div className="space-y-4 pt-4 border-t border-dark-700">
              <h4 className="text-md font-semibold text-dark-50">Informações do Veículo</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Marca *</label>
                  <select
                    value={camposDinamicos['Marca'] || ''}
                    onChange={(e) => handleCampoDinamicoChange('Marca', e.target.value)}
                    required
                    className="input"
                  >
                    <option value="">Selecione a marca</option>
                    {MARCAS_CARROS.map(marca => (
                      <option key={marca} value={marca}>{marca}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Modelo *</label>
                  <input
                    type="text"
                    value={camposDinamicos['Modelo'] || ''}
                    onChange={(e) => handleCampoDinamicoChange('Modelo', e.target.value)}
                    required
                    className="input"
                    placeholder="Ex: Uno, Gol, Celta..."
                  />
                </div>
                <div>
                  <label className="label">Placa *</label>
                  <input
                    type="text"
                    value={camposDinamicos['Placa'] || ''}
                    onChange={(e) => handleCampoDinamicoChange('Placa', e.target.value.toUpperCase())}
                    required
                    maxLength={10}
                    className="input"
                    placeholder="ABC-1234"
                  />
                </div>
                <div>
                  <label className="label">Ano *</label>
                  <input
                    type="number"
                    value={camposDinamicos['Ano'] || ''}
                    onChange={(e) => handleCampoDinamicoChange('Ano', e.target.value)}
                    required
                    min="1900"
                    max="2100"
                    className="input"
                    placeholder="Ex: 2020"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Nome do item */}
          <div>
            <label className="label">Nome do Item *</label>
            <input
              type="text"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              required
              className="input"
              placeholder={
                isCarros 
                  ? "Será gerado automaticamente (Marca Modelo)" 
                  : "Ex: Alambrado, Mesa, Cadeira..."
              }
              disabled={isCarros && camposDinamicos['Marca'] && camposDinamicos['Modelo']}
            />
            {isCarros && camposDinamicos['Marca'] && camposDinamicos['Modelo'] && (
              <p className="text-xs text-dark-400 mt-1">
                Nome gerado automaticamente: {formData.nome}
              </p>
            )}
          </div>

          <div>
            <label className="label">Descrição (opcional)</label>
            <textarea
              name="descricao"
              value={formData.descricao}
              onChange={handleChange}
              rows="3"
              className="input resize-none"
              placeholder="Ex: Mesa retangular de madeira, tamanho 3x2 metros..."
            />
          </div>
        </div>

        {/* Localização */}
        <div className="space-y-4 pt-6 border-t border-dark-700">
          <h3 className="text-lg font-semibold text-dark-50 flex items-center gap-2">
            <div className="w-1 h-6 bg-primary-500 rounded-full"></div>
            Localização do Item
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
                {ESTADOS.map(estado => (
                  <option key={estado.sigla} value={estado.sigla}>{estado.sigla}</option>
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

        {/* Botões */}
        <div className="flex gap-4 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary flex-1 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                Registrando...
              </>
            ) : (
              <>
                <Plus size={20} />
                Registrar Item
              </>
            )}
          </button>
        </div>
      </motion.form>
    </div>
  )
}
