import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import api from '../services/api'
import { Plus, Car, Package, Calendar, Trash2, Edit } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatDate } from '../utils/format'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']

export default function PecasCarros() {
  const [carros, setCarros] = useState([])
  const [pecas, setPecas] = useState([])
  const [associacoes, setAssociacoes] = useState([])
  const [loading, setLoading] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedAssociacao, setSelectedAssociacao] = useState(null)
  const [formData, setFormData] = useState({
    carro_id: '',
    peca_id: '',
    quantidade: 1,
    data_instalacao: new Date().toISOString().split('T')[0],
    observacoes: ''
  })

  useEffect(() => {
    loadDados()
  }, [])

  const loadDados = async () => {
    try {
      setLoading(true)
      // Carrega carros, peças e associações
      const [itensResp, associacoesResp] = await Promise.all([
        api.get('/api/itens'),
        api.get('/api/pecas-carros')
      ])
      
      const todosItens = itensResp.data || []
      setCarros(todosItens.filter(i => i.categoria === 'Carros'))
      setPecas(todosItens.filter(i => i.categoria === 'Peças de Carro'))
      setAssociacoes(associacoesResp.data || [])
    } catch (error) {
      toast.error('Erro ao carregar dados')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setFormLoading(true)
      
      const data = {
        carro_id: parseInt(formData.carro_id),
        peca_id: parseInt(formData.peca_id),
        quantidade: parseInt(formData.quantidade),
        data_instalacao: formData.data_instalacao,
        observacoes: formData.observacoes
      }

      if (selectedAssociacao) {
        await api.put(`/api/pecas-carros/${selectedAssociacao.id}`, data)
        toast.success('Associação atualizada com sucesso!')
      } else {
        await api.post('/api/pecas-carros', data)
        toast.success('Peça associada ao carro com sucesso!')
      }

      setShowForm(false)
      setSelectedAssociacao(null)
      setFormData({
        carro_id: '',
        peca_id: '',
        quantidade: 1,
        data_instalacao: new Date().toISOString().split('T')[0],
        observacoes: ''
      })
      await loadDados()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar associação')
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Tem certeza que deseja remover esta associação?')) return

    try {
      await api.delete(`/api/pecas-carros/${id}`)
      toast.success('Associação removida com sucesso!')
      await loadDados()
    } catch (error) {
      toast.error('Erro ao remover associação')
    }
  }

  const handleEdit = (associacao) => {
    setSelectedAssociacao(associacao)
    setFormData({
      carro_id: associacao.carro_id,
      peca_id: associacao.peca_id,
      quantidade: associacao.quantidade,
      data_instalacao: associacao.data_instalacao || new Date().toISOString().split('T')[0],
      observacoes: associacao.observacoes || ''
    })
    setShowForm(true)
  }

  const getNomeCarro = (carroId) => {
    const carro = carros.find(c => c.id === carroId)
    if (!carro) return `Carro #${carroId}`
    
    const marca = carro.dados_categoria?.Marca || carro.carro?.marca || ''
    const modelo = carro.dados_categoria?.Modelo || carro.carro?.modelo || ''
    const placa = carro.dados_categoria?.Placa || carro.carro?.placa || ''
    
    return `${marca} ${modelo} - ${placa}`.trim()
  }

  const getNomePeca = (pecaId) => {
    const peca = pecas.find(p => p.id === pecaId)
    return peca?.nome || `Peça #${pecaId}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Peças em Carros</h1>
          <p className="text-dark-400 mt-1">Gerencie as peças instaladas em cada carro</p>
        </div>
        <button
          onClick={() => {
            setShowForm(true)
            setSelectedAssociacao(null)
            setFormData({
              carro_id: '',
              peca_id: '',
              quantidade: 1,
              data_instalacao: new Date().toISOString().split('T')[0],
              observacoes: ''
            })
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
        >
          <Plus size={20} />
          Adicionar Peça ao Carro
        </button>
      </div>

      {/* Alertas */}
      {carros.length === 0 && (
        <div className="p-4 bg-yellow-600/20 border border-yellow-600/30 rounded-lg">
          <p className="text-sm text-yellow-400">
            ⚠️ Não há carros cadastrados. Cadastre carros primeiro na aba "Itens".
          </p>
        </div>
      )}

      {pecas.length === 0 && (
        <div className="p-4 bg-yellow-600/20 border border-yellow-600/30 rounded-lg">
          <p className="text-sm text-yellow-400">
            ⚠️ Não há peças cadastradas. Cadastre peças com a categoria "Peças de Carro" na aba "Itens".
          </p>
        </div>
      )}

      {/* Formulário */}
      {showForm && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-800 rounded-lg p-6 border border-dark-700"
        >
          <h2 className="text-xl font-bold text-white mb-4">
            {selectedAssociacao ? 'Editar Associação' : 'Nova Associação Peça-Carro'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Carro *</label>
                <select
                  value={formData.carro_id}
                  onChange={(e) => setFormData({ ...formData, carro_id: e.target.value })}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                >
                  <option value="">Selecione um carro</option>
                  {carros.map(carro => (
                    <option key={carro.id} value={carro.id}>
                      {getNomeCarro(carro.id)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Peça *</label>
                <select
                  value={formData.peca_id}
                  onChange={(e) => setFormData({ ...formData, peca_id: e.target.value })}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                >
                  <option value="">Selecione uma peça</option>
                  {pecas.map(peca => (
                    <option key={peca.id} value={peca.id}>
                      {peca.nome}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Quantidade *</label>
                <input
                  type="number"
                  min="1"
                  value={formData.quantidade}
                  onChange={(e) => setFormData({ ...formData, quantidade: e.target.value })}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Data de Instalação</label>
                <input
                  type="date"
                  value={formData.data_instalacao}
                  onChange={(e) => setFormData({ ...formData, data_instalacao: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Observações</label>
              <textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                rows="3"
                className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                placeholder="Ex: Peça original, instalada na revisão de 10.000km..."
              />
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={formLoading}
                className="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {formLoading ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setSelectedAssociacao(null)
                }}
                className="px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Lista de Associações */}
      <div className="bg-dark-800 rounded-lg border border-dark-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-dark-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider">Carro</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider">Peça</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider">Quantidade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider">Data Instalação</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider">Observações</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-dark-300 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700">
              {associacoes.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-dark-400">
                    Nenhuma peça associada a carros ainda.
                  </td>
                </tr>
              ) : (
                associacoes.map((associacao) => (
                  <tr key={associacao.id} className="hover:bg-dark-700/50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Car className="text-primary-400" size={18} />
                        <span className="text-white">{getNomeCarro(associacao.carro_id)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Package className="text-green-400" size={18} />
                        <span className="text-white">{getNomePeca(associacao.peca_id)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-white">
                      {associacao.quantidade}x
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-dark-300">
                      <div className="flex items-center gap-2">
                        <Calendar size={14} />
                        {formatDate(associacao.data_instalacao)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-dark-300 max-w-xs truncate">
                      {associacao.observacoes || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => handleEdit(associacao)}
                          className="p-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(associacao.id)}
                          className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
