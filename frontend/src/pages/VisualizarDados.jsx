import { useState, useEffect } from 'react'
import React from 'react'
import { motion } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import { Search, Edit, Trash2, Eye, X } from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
const MARCAS_CARROS = [
  'Fiat', 'Volkswagen', 'Chevrolet', 'Ford', 'Toyota', 'Honda', 'Hyundai', 
  'Renault', 'Nissan', 'Peugeot', 'Citroën', 'Jeep', 'Mitsubishi', 'Kia',
  'BMW', 'Mercedes-Benz', 'Audi', 'Volvo', 'Land Rover', 'Jaguar', 'Porsche',
  'Subaru', 'Suzuki', 'Chery', 'JAC', 'Troller', 'RAM', 'Dodge', 'Chrysler',
  'Mini', 'Smart', 'BYD', 'GWM', 'Caoa Chery', 'Outra'
]

export default function VisualizarDados() {
  const [itens, setItens] = useState([])
  const [compromissos, setCompromissos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('itens')
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroCategoria, setFiltroCategoria] = useState('')
  
  // Estados para edição/exclusão
  const [editingItem, setEditingItem] = useState(null)
  const [editingCompromisso, setEditingCompromisso] = useState(null)
  const [deletingItem, setDeletingItem] = useState(null)
  const [deletingCompromisso, setDeletingCompromisso] = useState(null)
  const [viewingItem, setViewingItem] = useState(null)
  const [viewingCompromisso, setViewingCompromisso] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [itensRes, compRes, catRes] = await Promise.all([
        itensAPI.listar(),
        compromissosAPI.listar(),
        categoriasAPI.listar().catch(() => ({ data: [] }))
      ])
      setItens(itensRes.data)
      setCompromissos(compRes.data)
      setCategorias(catRes.data || [])
    } catch (error) {
      toast.error('Erro ao carregar dados')
      console.error('Erro ao carregar dados:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteItem = async () => {
    if (!deletingItem) return
    try {
      await itensAPI.deletar(deletingItem.id)
      toast.success('Item deletado com sucesso!')
      setItens(itens.filter(i => i.id !== deletingItem.id))
      setDeletingItem(null)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao deletar item')
    }
  }

  const handleDeleteCompromisso = async () => {
    if (!deletingCompromisso) return
    try {
      await compromissosAPI.deletar(deletingCompromisso.id)
      toast.success('Compromisso deletado com sucesso!')
      setCompromissos(compromissos.filter(c => c.id !== deletingCompromisso.id))
      setDeletingCompromisso(null)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao deletar compromisso')
    }
  }

  const handleSaveItem = async (itemData) => {
    try {
      await itensAPI.atualizar(editingItem.id, itemData)
      toast.success('Item atualizado com sucesso!')
      await loadData()
      setEditingItem(null)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar item')
    }
  }

  const handleSaveCompromisso = async (compData) => {
    try {
      await compromissosAPI.atualizar(editingCompromisso.id, compData)
      toast.success('Compromisso atualizado com sucesso!')
      await loadData()
      setEditingCompromisso(null)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar compromisso')
    }
  }

  const filteredItens = itens.filter(item => {
    const matchSearch = item.nome?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.categoria?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchCategoria = !filtroCategoria || item.categoria === filtroCategoria
    return matchSearch && matchCategoria
  })

  // Agrupa itens por categoria
  const itensPorCategoria = filteredItens.reduce((acc, item) => {
    const categoria = item.categoria || 'Sem Categoria'
    if (!acc[categoria]) {
      acc[categoria] = []
    }
    acc[categoria].push(item)
    return acc
  }, {})

  const filteredCompromissos = compromissos.filter(comp =>
    comp.item?.nome?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    comp.contratante?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Visualizar Dados</h1>
        <p className="text-dark-400">Visualize e gerencie todos os itens e compromissos cadastrados</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-700">
        <button
          onClick={() => setActiveTab('itens')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${
            activeTab === 'itens'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-dark-400 hover:text-dark-200'
          }`}
        >
          Itens ({itens.length})
        </button>
        <button
          onClick={() => setActiveTab('compromissos')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${
            activeTab === 'compromissos'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-dark-400 hover:text-dark-200'
          }`}
        >
          Compromissos ({compromissos.length})
        </button>
      </div>

      {/* Search e Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-dark-400" size={20} />
          <input
            type="text"
            placeholder="Buscar por nome ou categoria..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-12"
          />
        </div>
        {activeTab === 'itens' && (
          <div>
            <select
              value={filtroCategoria}
              onChange={(e) => setFiltroCategoria(e.target.value)}
              className="input w-full"
            >
              <option value="">Todas as categorias</option>
              {categorias.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="card overflow-hidden p-0"
      >
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                {activeTab === 'itens' ? (
                  <>
                    <th>ID</th>
                    <th>Nome</th>
                    <th>Categoria</th>
                    <th>Quantidade</th>
                    <th>Localização</th>
                    <th>Ações</th>
                  </>
                ) : (
                  <>
                    <th>ID</th>
                    <th>Item</th>
                    <th>Quantidade</th>
                    <th>Início</th>
                    <th>Fim</th>
                    <th>Localização</th>
                    <th>Ações</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {activeTab === 'itens' ? (
                Object.keys(itensPorCategoria).length > 0 ? (
                  Object.entries(itensPorCategoria).map(([categoria, itensCategoria], catIndex) => (
                    <React.Fragment key={categoria}>
                      {/* Cabeçalho da Categoria */}
                      <tr className="bg-dark-700/50">
                        <td colSpan="6" className="px-4 py-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="px-3 py-1 bg-primary-600/20 text-primary-400 rounded-lg font-semibold text-sm">
                                {categoria}
                              </span>
                              <span className="text-dark-400 text-sm">
                                {itensCategoria.length} {itensCategoria.length === 1 ? 'item' : 'itens'}
                              </span>
                            </div>
                            <span className="text-dark-500 text-sm">
                              Total: {itensCategoria.reduce((sum, item) => sum + (item.quantidade_total || 0), 0)} unidades
                            </span>
                          </div>
                        </td>
                      </tr>
                      {/* Itens da Categoria */}
                      {itensCategoria.map((item, index) => (
                        <motion.tr
                          key={item.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: (catIndex * 0.1) + (index * 0.05) }}
                          className="hover:bg-dark-700/30"
                        >
                          <td className="font-mono text-xs text-dark-400">{item.id}</td>
                          <td className="font-medium text-dark-50">{item.nome}</td>
                          <td>
                            <span className="px-2 py-1 bg-primary-600/20 text-primary-400 rounded text-xs">
                              {item.categoria}
                            </span>
                          </td>
                          <td>{item.quantidade_total}</td>
                          <td className="text-dark-400">{item.cidade} - {item.uf}</td>
                          <td>
                            <div className="flex items-center gap-2">
                              <button 
                                onClick={() => setViewingItem(item)}
                                className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                                title="Ver detalhes"
                              >
                                <Eye size={16} className="text-dark-400" />
                              </button>
                              <button 
                                onClick={() => setEditingItem(item)}
                                className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                                title="Editar"
                              >
                                <Edit size={16} className="text-primary-400" />
                              </button>
                              <button 
                                onClick={() => setDeletingItem(item)}
                                className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                                title="Deletar"
                              >
                                <Trash2 size={16} className="text-red-400" />
                              </button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </React.Fragment>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-dark-400">
                      Nenhum item encontrado
                    </td>
                  </tr>
                )
              ) : (
                filteredCompromissos.length > 0 ? (
                  filteredCompromissos.map((comp, index) => (
                    <motion.tr
                      key={comp.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <td className="font-mono text-xs text-dark-400">{comp.id}</td>
                      <td className="font-medium text-dark-50">{comp.item?.nome || 'Item Deletado'}</td>
                      <td>{comp.quantidade}</td>
                      <td className="text-dark-400">{new Date(comp.data_inicio).toLocaleDateString('pt-BR')}</td>
                      <td className="text-dark-400">{new Date(comp.data_fim).toLocaleDateString('pt-BR')}</td>
                      <td className="text-dark-400">{comp.cidade} - {comp.uf}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => setViewingCompromisso(comp)}
                            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                            title="Ver detalhes"
                          >
                            <Eye size={16} className="text-dark-400" />
                          </button>
                          <button 
                            onClick={() => setEditingCompromisso(comp)}
                            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                            title="Editar"
                          >
                            <Edit size={16} className="text-primary-400" />
                          </button>
                          <button 
                            onClick={() => setDeletingCompromisso(comp)}
                            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                            title="Deletar"
                          >
                            <Trash2 size={16} className="text-red-400" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="text-center py-12 text-dark-400">
                      Nenhum compromisso encontrado
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Modal de Visualização de Item */}
      {viewingItem && (
        <Modal
          isOpen={!!viewingItem}
          onClose={() => setViewingItem(null)}
          title={`Detalhes do Item #${viewingItem.id}`}
        >
          <div className="space-y-4">
            <div>
              <label className="text-sm text-dark-400">Nome</label>
              <p className="text-dark-50 font-medium">{viewingItem.nome}</p>
            </div>
            <div>
              <label className="text-sm text-dark-400">Categoria</label>
              <p className="text-dark-50">{viewingItem.categoria}</p>
            </div>
            <div>
              <label className="text-sm text-dark-400">Quantidade Total</label>
              <p className="text-dark-50">{viewingItem.quantidade_total}</p>
            </div>
            {viewingItem.descricao && (
              <div>
                <label className="text-sm text-dark-400">Descrição</label>
                <p className="text-dark-50">{viewingItem.descricao}</p>
              </div>
            )}
            {viewingItem.dados_categoria && Object.keys(viewingItem.dados_categoria).length > 0 && (
              <div>
                <label className="text-sm text-dark-400">Detalhes de {viewingItem.categoria}</label>
                <div className="mt-2 space-y-2">
                  {Object.entries(viewingItem.dados_categoria).map(([campo, valor]) => (
                    <div key={campo} className="flex justify-between">
                      <span className="text-dark-400">{campo}:</span>
                      <span className="text-dark-50">{String(valor)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <label className="text-sm text-dark-400">Localização</label>
              <p className="text-dark-50">{viewingItem.cidade} - {viewingItem.uf}</p>
              {viewingItem.endereco && (
                <p className="text-dark-400 text-sm mt-1">{viewingItem.endereco}</p>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Modal de Edição de Item */}
      {editingItem && (
        <EditItemModal
          item={editingItem}
          categorias={categorias}
          onClose={() => setEditingItem(null)}
          onSave={handleSaveItem}
        />
      )}

      {/* Modal de Edição de Compromisso */}
      {editingCompromisso && (
        <EditCompromissoModal
          compromisso={editingCompromisso}
          itens={itens}
          onClose={() => setEditingCompromisso(null)}
          onSave={handleSaveCompromisso}
        />
      )}

      {/* Modal de Visualização de Compromisso */}
      {viewingCompromisso && (
        <Modal
          isOpen={!!viewingCompromisso}
          onClose={() => setViewingCompromisso(null)}
          title={`Detalhes do Compromisso #${viewingCompromisso.id}`}
        >
          <div className="space-y-4">
            <div>
              <label className="text-sm text-dark-400">Item</label>
              <p className="text-dark-50 font-medium">{viewingCompromisso.item?.nome || 'Item Deletado'}</p>
            </div>
            <div>
              <label className="text-sm text-dark-400">Quantidade</label>
              <p className="text-dark-50">{viewingCompromisso.quantidade}</p>
            </div>
            <div>
              <label className="text-sm text-dark-400">Período</label>
              <p className="text-dark-50">
                {new Date(viewingCompromisso.data_inicio).toLocaleDateString('pt-BR')} a {new Date(viewingCompromisso.data_fim).toLocaleDateString('pt-BR')}
              </p>
            </div>
            {viewingCompromisso.descricao && (
              <div>
                <label className="text-sm text-dark-400">Descrição</label>
                <p className="text-dark-50">{viewingCompromisso.descricao}</p>
              </div>
            )}
            <div>
              <label className="text-sm text-dark-400">Localização</label>
              <p className="text-dark-50">{viewingCompromisso.cidade} - {viewingCompromisso.uf}</p>
              {viewingCompromisso.endereco && (
                <p className="text-dark-400 text-sm mt-1">{viewingCompromisso.endereco}</p>
              )}
            </div>
            {viewingCompromisso.contratante && (
              <div>
                <label className="text-sm text-dark-400">Contratante</label>
                <p className="text-dark-50">{viewingCompromisso.contratante}</p>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Confirmação de Exclusão de Item */}
      <ConfirmDialog
        isOpen={!!deletingItem}
        onClose={() => setDeletingItem(null)}
        onConfirm={handleDeleteItem}
        title="Confirmar Exclusão"
        message={`Tem certeza que deseja excluir o item "${deletingItem?.nome}"? Esta ação não pode ser desfeita.`}
      />

      {/* Confirmação de Exclusão de Compromisso */}
      <ConfirmDialog
        isOpen={!!deletingCompromisso}
        onClose={() => setDeletingCompromisso(null)}
        onConfirm={handleDeleteCompromisso}
        title="Confirmar Exclusão"
        message={`Tem certeza que deseja excluir este compromisso? Esta ação não pode ser desfeita.`}
      />
    </div>
  )
}

// Componente de Edição de Item
function EditItemModal({ item, categorias, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome: item.nome || '',
    quantidade_total: item.quantidade_total || 1,
    categoria: item.categoria || '',
    descricao: item.descricao || '',
    cidade: item.cidade || '',
    uf: item.uf || 'SP',
    endereco: item.endereco || '',
  })
  const [camposCategoria, setCamposCategoria] = useState([])
  const [camposDinamicos, setCamposDinamicos] = useState(item.dados_categoria || {})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (formData.categoria) {
      loadCamposCategoria(formData.categoria)
    }
  }, [formData.categoria])

  const loadCamposCategoria = async (categoria) => {
    try {
      const response = await categoriasAPI.obterCampos(categoria)
      const campos = response.data || []
      setCamposCategoria(campos)
      
      // Inicializa campos dinâmicos se não existirem
      if (campos.length > 0 && Object.keys(camposDinamicos).length === 0) {
        const novosCampos = {}
        campos.forEach(campo => {
          novosCampos[campo] = item.dados_categoria?.[campo] || ''
        })
        setCamposDinamicos(novosCampos)
      }
    } catch (error) {
      setCamposCategoria([])
    }
  }

  const handleCampoDinamicoChange = (campo, value) => {
    setCamposDinamicos(prev => ({
      ...prev,
      [campo]: value
    }))
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

  const renderCampoDinamico = (campo) => {
    const tipo = inferirTipoCampo(campo)
    const valor = camposDinamicos[campo] || ''

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
          />
        )
      }
    }

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
          />
        )
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        ...formData,
        quantidade_total: parseInt(formData.quantidade_total),
      }
      if (camposCategoria.length > 0 && Object.keys(camposDinamicos).length > 0) {
        payload.campos_categoria = camposDinamicos
      }
      await onSave(payload)
    } finally {
      setLoading(false)
    }
  }

  const quantidadeFixa = formData.categoria === 'Carros' || camposCategoria.some(c => 
    ['Placa', 'Serial', 'Código Único'].includes(c)
  )

  return (
    <Modal isOpen={true} onClose={onClose} title={`Editar Item #${item.id}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Categoria *</label>
          <select
            value={formData.categoria}
            onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
            required
            className="input"
          >
            {categorias.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Nome *</label>
          <input
            type="text"
            value={formData.nome}
            onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
            required
            className="input"
          />
        </div>

        {!quantidadeFixa && (
          <div>
            <label className="label">Quantidade Total *</label>
            <input
              type="number"
              value={formData.quantidade_total}
              onChange={(e) => setFormData({ ...formData, quantidade_total: e.target.value })}
              required
              min="1"
              className="input"
            />
          </div>
        )}

        <div>
          <label className="label">Descrição</label>
          <textarea
            value={formData.descricao}
            onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
            rows="3"
            className="input resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Cidade *</label>
            <input
              type="text"
              value={formData.cidade}
              onChange={(e) => setFormData({ ...formData, cidade: e.target.value })}
              required
              className="input"
            />
          </div>
          <div>
            <label className="label">UF *</label>
            <select
              value={formData.uf}
              onChange={(e) => setFormData({ ...formData, uf: e.target.value })}
              required
              className="input"
            >
              {UFS.map(uf => (
                <option key={uf} value={uf}>{uf}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Endereço</label>
          <input
            type="text"
            value={formData.endereco}
            onChange={(e) => setFormData({ ...formData, endereco: e.target.value })}
            className="input"
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
            Cancelar
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary flex-1">
            {loading ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// Componente de Edição de Compromisso
function EditCompromissoModal({ compromisso, itens, onClose, onSave }) {
  const [formData, setFormData] = useState({
    item_id: compromisso.item_id || '',
    quantidade: compromisso.quantidade || 1,
    data_inicio: compromisso.data_inicio?.split('T')[0] || new Date().toISOString().split('T')[0],
    data_fim: compromisso.data_fim?.split('T')[0] || new Date().toISOString().split('T')[0],
    descricao: compromisso.descricao || '',
    cidade: compromisso.cidade || '',
    uf: compromisso.uf || 'SP',
    endereco: compromisso.endereco || '',
    contratante: compromisso.contratante || '',
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await onSave({
        ...formData,
        item_id: parseInt(formData.item_id),
        quantidade: parseInt(formData.quantidade),
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={true} onClose={onClose} title={`Editar Compromisso #${compromisso.id}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Item *</label>
          <select
            value={formData.item_id}
            onChange={(e) => setFormData({ ...formData, item_id: e.target.value })}
            required
            className="input"
          >
            <option value="">Selecione um item</option>
            {itens.map(item => (
              <option key={item.id} value={item.id}>
                {item.nome}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="label">Quantidade *</label>
            <input
              type="number"
              value={formData.quantidade}
              onChange={(e) => setFormData({ ...formData, quantidade: e.target.value })}
              required
              min="1"
              className="input"
            />
          </div>
          <div>
            <label className="label">Data Início *</label>
            <input
              type="date"
              value={formData.data_inicio}
              onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
              required
              className="input"
            />
          </div>
          <div>
            <label className="label">Data Fim *</label>
            <input
              type="date"
              value={formData.data_fim}
              onChange={(e) => setFormData({ ...formData, data_fim: e.target.value })}
              required
              min={formData.data_inicio}
              className="input"
            />
          </div>
        </div>

        <div>
          <label className="label">Descrição</label>
          <textarea
            value={formData.descricao}
            onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
            rows="3"
            className="input resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Cidade *</label>
            <input
              type="text"
              value={formData.cidade}
              onChange={(e) => setFormData({ ...formData, cidade: e.target.value })}
              required
              className="input"
            />
          </div>
          <div>
            <label className="label">UF *</label>
            <select
              value={formData.uf}
              onChange={(e) => setFormData({ ...formData, uf: e.target.value })}
              required
              className="input"
            >
              {UFS.map(uf => (
                <option key={uf} value={uf}>{uf}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Endereço</label>
          <input
            type="text"
            value={formData.endereco}
            onChange={(e) => setFormData({ ...formData, endereco: e.target.value })}
            className="input"
          />
        </div>

        <div>
          <label className="label">Contratante</label>
          <input
            type="text"
            value={formData.contratante}
            onChange={(e) => setFormData({ ...formData, contratante: e.target.value })}
            className="input"
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
            Cancelar
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary flex-1">
            {loading ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
