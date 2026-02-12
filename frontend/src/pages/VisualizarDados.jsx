import { useState, useEffect } from 'react'
import React from 'react'
import { motion } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Search, Edit, Trash2, Eye, DollarSign, Calendar } from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import { formatItemName, formatDate } from '../utils/format'
import { getCidadesPorUF, ESTADOS } from '../utils/municipios'

const UFS = ESTADOS.map(e => e.sigla)
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
  const [pecasCarros, setPecasCarros] = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('itens')
  const [searchTerm, setSearchTerm] = useState('')
  const [filtroCategoria, setFiltroCategoria] = useState('')
  
  const [editingItem, setEditingItem] = useState(null)
  const [editingCompromisso, setEditingCompromisso] = useState(null)
  const [deletingItem, setDeletingItem] = useState(null)
  const [deletingCompromisso, setDeletingCompromisso] = useState(null)
  const [viewingItem, setViewingItem] = useState(null)
  const [viewingCompromisso, setViewingCompromisso] = useState(null)
  const [editingPecaCarro, setEditingPecaCarro] = useState(null)

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
      
      try {
        const pecasRes = await api.get('/api/pecas-carros')
        setPecasCarros(pecasRes.data || [])
      } catch (error) {
        setPecasCarros([])
      }
    } catch (error) {
      toast.error('Erro ao carregar dados')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteItem = async () => {
    if (!deletingItem) return
    try {
      await itensAPI.deletar(deletingItem.id)
      toast.success('Item deletado!')
      setItens(itens.filter(i => i.id !== deletingItem.id))
      setDeletingItem(null)
    } catch (error) {
      toast.error('Erro ao deletar item')
    }
  }

  const handleSaveItem = async (itemData) => {
    try {
      await itensAPI.atualizar(editingItem.id, itemData)
      toast.success('Item atualizado!')
      await loadData()
      setEditingItem(null)
    } catch (error) {
      toast.error('Erro ao atualizar item')
    }
  }

  // Filtros
  const filteredItens = itens.filter(item => {
    const matchSearch = item.nome?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.categoria?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchCategoria = !filtroCategoria || item.categoria === filtroCategoria
    return matchSearch && matchCategoria
  })

  const itensPorCategoria = filteredItens.reduce((acc, item) => {
    const cat = item.categoria || 'Sem Categoria'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-dark-50 mb-2">Visualizar Dados</h1>
          <p className="text-dark-400">Gerencie seu patrimônio e centro de custos</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-700">
        <button onClick={() => setActiveTab('itens')} className={`px-6 py-3 border-b-2 ${activeTab === 'itens' ? 'border-primary-500 text-primary-400' : 'border-transparent text-dark-400'}`}>
          Itens ({itens.length})
        </button>
        <button onClick={() => setActiveTab('compromissos')} className={`px-6 py-3 border-b-2 ${activeTab === 'compromissos' ? 'border-primary-500 text-primary-400' : 'border-transparent text-dark-400'}`}>
          Aluguéis ({compromissos.length})
        </button>
      </div>

      {/* Busca */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-dark-400" size={20} />
          <input type="text" placeholder="Buscar..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="input pl-12 w-full" />
        </div>
        <select value={filtroCategoria} onChange={(e) => setFiltroCategoria(e.target.value)} className="input w-64">
          <option value="">Todas Categorias</option>
          {categorias.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {activeTab === 'itens' && (
        <div className="card p-0 overflow-hidden">
          <table className="table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Categoria</th>
                <th>Qtd</th>
                <th>Valor Compra</th>
                <th>Localização</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(itensPorCategoria).map(([cat, lista]) => (
                <React.Fragment key={cat}>
                  <tr className="bg-dark-700/30"><td colSpan="6" className="font-bold text-primary-400 py-2 px-4">{cat}</td></tr>
                  {lista.map(item => (
                    <tr key={item.id} className="hover:bg-dark-700/20">
                      <td>{formatItemName(item)}</td>
                      <td><span className="text-xs bg-dark-600 px-2 py-1 rounded">{item.categoria}</span></td>
                      <td>{item.quantidade_total}</td>
                      <td className="text-green-400 font-mono">
                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.valor_compra || 0)}
                      </td>
                      <td className="text-dark-400 text-sm">{item.cidade}/{item.uf}</td>
                      <td>
                        <div className="flex gap-2">
                          <button onClick={() => setViewingItem(item)} className="p-1 hover:text-white"><Eye size={18}/></button>
                          <button onClick={() => setEditingItem(item)} className="p-1 hover:text-primary-400"><Edit size={18}/></button>
                          <button onClick={() => setDeletingItem(item)} className="p-1 hover:text-red-400"><Trash2 size={18}/></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Visualizar Detalhes */}
      {viewingItem && (
        <Modal isOpen={true} onClose={() => setViewingItem(null)} title="Ficha do Ativo">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-dark-700 rounded-lg">
                <p className="text-xs text-dark-400 uppercase">Valor de Aquisição</p>
                <p className="text-xl font-bold text-green-400">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(viewingItem.valor_compra || 0)}
                </p>
              </div>
              <div className="p-4 bg-dark-700 rounded-lg">
                <p className="text-xs text-dark-400 uppercase">Data Compra</p>
                <p className="text-lg text-dark-50">{viewingItem.data_aquisicao ? formatDate(viewingItem.data_aquisicao) : 'Não informada'}</p>
              </div>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-bold border-b border-dark-600 pb-1">Informações Gerais</h4>
              <p><strong>Nome:</strong> {viewingItem.nome}</p>
              <p><strong>Local:</strong> {viewingItem.endereco || 'Apenas cidade'}, {viewingItem.cidade}-{viewingItem.uf}</p>
              {viewingItem.descricao && <p><strong>Descrição:</strong> {viewingItem.descricao}</p>}
            </div>

            {viewingItem.dados_categoria && (
              <div className="space-y-2">
                <h4 className="font-bold border-b border-dark-600 pb-1">Atributos de {viewingItem.categoria}</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(viewingItem.dados_categoria).map(([k, v]) => (
                    <p key={k}><span className="text-dark-400">{k}:</span> {v}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Modal Editar Item */}
      {editingItem && (
        <EditItemModal 
          item={editingItem} 
          categorias={categorias} 
          onClose={() => setEditingItem(null)} 
          onSave={handleSaveItem} 
        />
      )}

      <ConfirmDialog isOpen={!!deletingItem} onClose={() => setDeletingItem(null)} onConfirm={handleDeleteItem} title="Excluir Item?" message="Isso removerá o item e seu histórico financeiro permanentemente." />
    </div>
  )
}

function EditItemModal({ item, categorias, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome: item.nome || '',
    quantidade_total: item.quantidade_total || 1,
    categoria: item.categoria || '',
    descricao: item.descricao || '',
    cidade: item.cidade || '',
    uf: item.uf || 'DF',
    endereco: item.endereco || '',
    // Formata o valor inicial para a máscara
    valor_compra: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(item.valor_compra || 0),
    data_aquisicao: item.data_aquisicao || ''
  })
  const [camposDinamicos, setCamposDinamicos] = useState(item.dados_categoria || {})
  const [loading, setLoading] = useState(false)

  const formatarMoeda = (valor) => {
    const apenasNumeros = String(valor).replace(/\D/g, "");
    const valorDecimal = (Number(apenasNumeros) / 100).toFixed(2);
    return new Intl.NumberFormat('pt-BR', { style: 'decimal', minimumFractionDigits: 2 }).format(valorDecimal);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'valor_compra') {
      setFormData(prev => ({ ...prev, [name]: formatarMoeda(value) }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const payload = {
      ...formData,
      quantidade_total: parseInt(formData.quantidade_total),
      valor_compra: parseFloat(formData.valor_compra.replace(/\./g, '').replace(',', '.')) || 0,
      campos_categoria: camposDinamicos
    };
    await onSave(payload);
    setLoading(false);
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Ativo">
      <form onSubmit={handleSubmit} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="label">Nome do Item</label>
            <input name="nome" value={formData.nome} onChange={handleChange} className="input" required />
          </div>
          <div>
            <label className="label">Valor de Compra (R$)</label>
            <input name="valor_compra" value={formData.valor_compra} onChange={handleChange} className="input text-green-400 font-bold" />
          </div>
          <div>
            <label className="label">Data de Aquisição</label>
            <input type="date" name="data_aquisicao" value={formData.data_aquisicao} onChange={handleChange} className="input" />
          </div>
          <div>
            <label className="label">Quantidade Total</label>
            <input type="number" name="quantidade_total" value={formData.quantidade_total} onChange={handleChange} className="input" />
          </div>
          <div>
            <label className="label">UF</label>
            <select name="uf" value={formData.uf} onChange={handleChange} className="input">
              {ESTADOS.map(e => <option key={e.sigla} value={e.sigla}>{e.sigla}</option>)}
            </select>
          </div>
        </div>
        
        <div>
          <label className="label">Descrição</label>
          <textarea name="descricao" value={formData.descricao} onChange={handleChange} className="input h-20" />
        </div>

        <div className="flex gap-2 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary flex-1">Cancelar</button>
          <button type="submit" disabled={loading} className="btn btn-primary flex-1">
            {loading ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </form>
    </Modal>
  )
}