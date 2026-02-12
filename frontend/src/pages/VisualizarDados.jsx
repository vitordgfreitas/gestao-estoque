import { useState, useEffect } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Search, Edit, Trash2, Eye, Package, Calendar, Car, DollarSign, ClipboardList, MapPin } from 'lucide-react'
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
  const [editingPecaCarro, setEditingPecaCarro] = useState(null)
  const [viewingItem, setViewingItem] = useState(null)
  const [deletingItem, setDeletingItem] = useState(null)
  const [deletingCompromisso, setDeletingCompromisso] = useState(null)

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [itensRes, compRes, catRes, pecasRes] = await Promise.all([
        itensAPI.listar(),
        compromissosAPI.listar(),
        categoriasAPI.listar().catch(() => ({ data: [] })),
        api.get('/api/pecas-carros').catch(() => ({ data: [] }))
      ])
      setItens(itensRes.data || [])
      setCompromissos(compRes.data || [])
      setCategorias(catRes.data || [])
      setPecasCarros(pecasRes.data || [])
    } catch (error) {
      toast.error('Erro ao carregar dados do sistema')
    } finally {
      setLoading(false)
    }
  }

  // Handlers de exclusão
  const handleDeleteItem = async () => {
    try {
      await itensAPI.deletar(deletingItem.id)
      toast.success('Item removido com sucesso')
      setItens(itens.filter(i => i.id !== deletingItem.id))
      setDeletingItem(null)
    } catch (error) { toast.error('Erro ao excluir item') }
  }

  const handleDeleteCompromisso = async () => {
    try {
      // Chama a rota DELETE /api/compromissos/{id} que você configurou no backend
      await compromissosAPI.deletar(deletingCompromisso.id)
      toast.success('Contrato e itens vinculados removidos!')
      setCompromissos(compromissos.filter(c => c.id !== deletingCompromisso.id))
      setDeletingCompromisso(null)
    } catch (error) { toast.error('Erro ao excluir contrato') }
  }

  // Handlers de salvamento
  const handleSaveItem = async (itemData) => {
    try {
      await itensAPI.atualizar(editingItem.id, itemData)
      toast.success('Item atualizado com sucesso!')
      await loadData()
      setEditingItem(null)
    } catch (error) { toast.error('Erro ao atualizar item') }
  }

  const handleSaveCompromisso = async (compData) => {
    try {
      await compromissosAPI.atualizar(editingCompromisso.id, compData)
      toast.success('Contrato Master atualizado!')
      await loadData()
      setEditingCompromisso(null)
    } catch (error) { toast.error('Erro ao atualizar contrato') }
  }

  const handleSavePecaCarro = async (data) => {
    try {
      await api.put(`/api/pecas-carros/${editingPecaCarro.id}`, data)
      toast.success('Manutenção atualizada!')
      await loadData()
      setEditingPecaCarro(null)
    } catch (error) { toast.error('Erro ao salvar alteração') }
  }

  // Filtros
  const filteredItens = itens.filter(item => (
    (item.nome?.toLowerCase().includes(searchTerm.toLowerCase()) || 
     item.categoria?.toLowerCase().includes(searchTerm.toLowerCase())) &&
    (!filtroCategoria || item.categoria === filtroCategoria)
  ))

  const itensPorCategoria = filteredItens.reduce((acc, item) => {
    const cat = item.categoria || 'Sem Categoria'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})

  const filteredCompromissos = compromissos.filter(comp =>
    comp.contratante?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    comp.nome_contrato?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50 font-black">Visualizar Dados</h1>
        <p className="text-dark-400">Controle de Ativos e Faturamento de Contratos</p>
      </div>

      <div className="flex gap-2 border-b border-dark-700">
        <button onClick={() => setActiveTab('itens')} className={`px-6 py-3 font-bold border-b-2 transition-all ${activeTab === 'itens' ? 'border-primary-500 text-primary-400' : 'border-transparent text-dark-400'}`}>Itens ({itens.length})</button>
        <button onClick={() => setActiveTab('compromissos')} className={`px-6 py-3 font-bold border-b-2 transition-all ${activeTab === 'compromissos' ? 'border-primary-500 text-primary-400' : 'border-transparent text-dark-400'}`}>Contratos ({compromissos.length})</button>
        <button onClick={() => setActiveTab('pecas-carros')} className={`px-6 py-3 font-bold border-b-2 transition-all ${activeTab === 'pecas-carros' ? 'border-primary-500 text-primary-400' : 'border-transparent text-dark-400'}`}>Manutenções ({pecasCarros.length})</button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-dark-500" size={20} />
          <input type="text" placeholder="Buscar por nome, cliente ou contrato..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="input pl-12 w-full" />
        </div>
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          {activeTab === 'itens' && (
            <table className="table">
              <thead>
                <tr><th>ID</th><th>Nome</th><th>Qtd</th><th>Valor Compra</th><th>Localização</th><th>Ações</th></tr>
              </thead>
              <tbody>
                {Object.entries(itensPorCategoria).map(([categoria, lista]) => (
                  <React.Fragment key={categoria}>
                    <tr className="bg-dark-700/50"><td colSpan="6" className="px-4 py-2 font-bold text-primary-400 uppercase text-[10px] tracking-widest">{categoria}</td></tr>
                    {lista.map(item => (
                      <tr key={item.id} className="hover:bg-dark-700/20">
                        <td className="font-mono text-[10px] text-dark-500">#{item.id}</td>
                        <td className="font-medium">{formatItemName(item)}</td>
                        <td>{item.quantidade_total}</td>
                        <td className="text-green-400 font-mono">R$ {(item.valor_compra || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
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
          )}

          {activeTab === 'compromissos' && (
            <table className="table">
              <thead>
                <tr>
                  <th>Contrato / Cliente</th>
                  <th>Equipamentos</th>
                  <th>Período</th>
                  <th>Valor (ROI)</th>
                  <th className="text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {filteredCompromissos.map(c => (
                  <tr key={c.id} className="hover:bg-dark-700/20 group">
                    <td>
                      <div className="font-bold text-dark-50">{c.nome_contrato || `Contrato #${c.id}`}</div>
                      <div className="text-[10px] text-dark-400 uppercase tracking-tighter">{c.contratante}</div>
                    </td>
                    <td className="max-w-xs">
                      <div className="flex flex-wrap gap-1">
                        {c.compromisso_itens?.map((ci, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-primary-500/10 text-primary-400 rounded text-[10px] font-bold border border-primary-500/20">
                            {ci.itens?.nome} ({ci.quantidade})
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="text-xs">
                      <div className="text-dark-200">{formatDate(c.data_inicio)}</div>
                      <div className="text-dark-500 text-[10px]">até {formatDate(c.data_fim)}</div>
                    </td>
                    <td className="text-green-400 font-black">
                      R$ {(c.valor_total_contrato || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                    </td>
                    <td className="text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => setEditingCompromisso(c)} className="p-2 text-primary-400 hover:bg-primary-500/10 rounded-lg"><Edit size={16}/></button>
                        <button onClick={() => setDeletingCompromisso(c)} className="p-2 text-red-400 hover:bg-red-400/10 rounded-lg"><Trash2 size={16}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'pecas-carros' && (
            <table className="table">
              <thead>
                <tr><th>Carro</th><th>Peça</th><th>Qtd</th><th>Data Instalação</th><th>Ações</th></tr>
              </thead>
              <tbody>
                {pecasCarros.map(pc => (
                  <tr key={pc.id}>
                    <td className="font-bold">{itens.find(i => i.id === pc.carro_id)?.nome || 'N/A'}</td>
                    <td className="text-primary-400">{itens.find(i => i.id === pc.peca_id)?.nome || 'N/A'}</td>
                    <td>{pc.quantidade}</td>
                    <td className="text-xs">{formatDate(pc.data_instalacao)}</td>
                    <td>
                      <button onClick={() => setEditingPecaCarro(pc)} className="p-2 hover:text-primary-400"><Edit size={18}/></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </motion.div>

      {/* MODAL DETALHES ITEM */}
      {viewingItem && (
        <Modal isOpen={true} onClose={() => setViewingItem(null)} title="Ficha Técnica do Ativo">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-dark-700 rounded-lg">
                <label className="text-[10px] text-dark-400 uppercase font-bold block mb-1 text-green-500">Custo de Aquisição</label>
                <span className="text-xl font-black text-dark-50">R$ {(viewingItem.valor_compra || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
              </div>
              <div className="p-3 bg-dark-700 rounded-lg">
                <label className="text-[10px] text-dark-400 uppercase font-bold block mb-1">Data de Compra</label>
                <span className="text-lg text-dark-50 font-bold">{viewingItem.data_aquisicao ? formatDate(viewingItem.data_aquisicao) : 'N/A'}</span>
              </div>
            </div>
            <div className="space-y-2 p-4 bg-dark-800 rounded-xl border border-dark-700">
               <p className="flex justify-between"><strong>Categoria:</strong> <span className="text-primary-400 font-bold">{viewingItem.categoria}</span></p>
               <p className="flex justify-between"><strong>Localização:</strong> <span>{viewingItem.cidade} - {viewingItem.uf}</span></p>
               {viewingItem.descricao && <p className="text-dark-400 text-sm mt-4 italic border-t border-dark-700 pt-2">{viewingItem.descricao}</p>}
            </div>
          </div>
        </Modal>
      )}

      {/* MODAIS DE EDIÇÃO */}
      {editingItem && <EditItemModal item={editingItem} categorias={categorias} onClose={() => setEditingItem(null)} onSave={handleSaveItem} />}
      {editingCompromisso && <EditCompromissoModal compromisso={editingCompromisso} itens={itens} onClose={() => setEditingCompromisso(null)} onSave={handleSaveCompromisso} />}
      {editingPecaCarro && <EditPecaCarroModal pecaCarro={editingPecaCarro} itens={itens} onClose={() => setEditingPecaCarro(null)} onSave={handleSavePecaCarro} />}

      <ConfirmDialog isOpen={!!deletingItem} onClose={() => setDeletingItem(null)} onConfirm={handleDeleteItem} title="Excluir Ativo?" message="Esta ação removerá o item e seu histórico. Não pode ser desfeita." />
      <ConfirmDialog isOpen={!!deletingCompromisso} onClose={() => setDeletingCompromisso(null)} onConfirm={handleDeleteCompromisso} title="Excluir Contrato?" message="Ao excluir este contrato, todos os itens vinculados voltarão ao estoque disponível." />
    </div>
  )
}

// --- MODAL EDIÇÃO ITEM ---
function EditItemModal({ item, categorias, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome: item.nome || '',
    quantidade_total: item.quantidade_total || 1,
    categoria: item.categoria || '',
    descricao: item.descricao || '',
    cidade: item.cidade || '',
    uf: item.uf || 'DF',
    endereco: item.endereco || '',
    valor_compra: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(item.valor_compra || 0),
    data_aquisicao: item.data_aquisicao || '',
    placa: item.dados_categoria?.Placa || item.dados_categoria?.placa || '',
    marca: item.dados_categoria?.Marca || item.dados_categoria?.marca || '',
    modelo: item.dados_categoria?.Modelo || item.dados_categoria?.modelo || '',
    ano: item.dados_categoria?.Ano || item.dados_categoria?.ano || '',
  })
  
  const [camposCategoria, setCamposCategoria] = useState([])
  const [camposDinamicos, setCamposDinamicos] = useState(item.dados_categoria || {})
  const [cidadesDisponiveis, setCidadesDisponiveis] = useState([])

  useEffect(() => {
    if (formData.categoria) loadCampos(formData.categoria)
    if (formData.uf) setCidadesDisponiveis(getCidadesPorUF(formData.uf))
  }, [formData.categoria, formData.uf])

  const loadCampos = async (cat) => {
    try {
      const res = await categoriasAPI.obterCampos(cat)
      setCamposCategoria(res.data || [])
    } catch (e) { setCamposCategoria([]) }
  }

  const handleMoeda = (v) => {
    const n = v.replace(/\D/g, "");
    return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(n / 100);
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    const dataFormatada = formData.data_aquisicao === "" ? null : formData.data_aquisicao;
    const payload = {
      ...formData,
      quantidade_total: parseInt(formData.quantidade_total),
      valor_compra: parseFloat(formData.valor_compra.replace(/\./g, '').replace(',', '.')) || 0,
      data_aquisicao: dataFormatada,
      campos_categoria: formData.categoria === 'Carros' ? { 
        Placa: formData.placa, Marca: formData.marca, Modelo: formData.modelo, Ano: formData.ano 
      } : camposDinamicos
    };
    onSave(payload);
  }

  return (
    <Modal isOpen={true} onClose={onClose} title={`Editar ${formData.categoria}`}>
      <form onSubmit={handleSubmit} className="space-y-4 max-h-[80vh] overflow-y-auto pr-2">
        <div className="col-span-2">
          <label className="label">Nome do Item *</label>
          <input className="input" value={formData.nome} onChange={e => setFormData({...formData, nome: e.target.value})} required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Valor de Compra</label><input className="input" value={formData.valor_compra} onChange={e => setFormData({...formData, valor_compra: handleMoeda(e.target.value)})} /></div>
          <div><label className="label">Data Compra</label><input type="date" className="input" value={formData.data_aquisicao} onChange={e => setFormData({...formData, data_aquisicao: e.target.value})} /></div>
        </div>
        <div className="flex gap-2 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary flex-1">Cancelar</button>
          <button type="submit" className="btn btn-primary flex-1">Salvar</button>
        </div>
      </form>
    </Modal>
  )
}

// --- MODAL EDIÇÃO COMPROMISSO (MASTER) ---
function EditCompromissoModal({ compromisso, itens, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome_contrato: compromisso.nome_contrato || '',
    contratante: compromisso.contratante || '',
    valor_total_contrato: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(compromisso.valor_total_contrato || 0),
    data_inicio: compromisso.data_inicio?.split('T')[0] || '',
    data_fim: compromisso.data_fim?.split('T')[0] || '',
    uf: compromisso.uf || 'DF',
    cidade: compromisso.cidade || '',
    endereco: compromisso.endereco || '',
    descricao: compromisso.descricao || ''
  })
  
  const [cidadesDisp, setCidadesDisp] = useState([])

  useEffect(() => { if (formData.uf) setCidadesDisp(getCidadesPorUF(formData.uf)) }, [formData.uf])

  const handleCurrency = (v) => {
    const n = v.replace(/\D/g, "");
    return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(n / 100);
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      valor_total_contrato: parseFloat(formData.valor_total_contrato.replace(/\./g, '').replace(',', '.')) || 0
    };
    onSave(payload);
  }

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Contrato Master">
      <form onSubmit={handleSubmit} className="space-y-4 max-h-[80vh] overflow-y-auto pr-2">
        <div><label className="label">Nome do Contrato / Evento *</label><input className="input font-bold" value={formData.nome_contrato} onChange={e => setFormData({...formData, nome_contrato: e.target.value})} required /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label text-green-500">Valor do Contrato</label><input className="input font-black text-green-400" value={formData.valor_total_contrato} onChange={e => setFormData({...formData, valor_total_contrato: handleCurrency(e.target.value)})} /></div>
          <div><label className="label">Contratante</label><input className="input" value={formData.contratante} onChange={e => setFormData({...formData, contratante: e.target.value})} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Data Início</label><input type="date" className="input" value={formData.data_inicio} onChange={e => setFormData({...formData, data_inicio: e.target.value})} /></div>
          <div><label className="label">Data Fim</label><input type="date" className="input" value={formData.data_fim} onChange={e => setFormData({...formData, data_fim: e.target.value})} /></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">UF</label><select className="input" value={formData.uf} onChange={e => setFormData({...formData, uf: e.target.value})}>{UFS.map(u => <option key={u} value={u}>{u}</option>)}</select></div>
          <div><label className="label">Cidade</label><select className="input" value={formData.cidade} onChange={e => setFormData({...formData, cidade: e.target.value})}>{cidadesDisp.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
        </div>
        <button type="submit" className="btn btn-primary w-full py-4 font-black mt-4">SALVAR ALTERAÇÕES NO CONTRATO</button>
      </form>
    </Modal>
  )
}

// --- MODAL EDIÇÃO PEÇA ---
function EditPecaCarroModal({ pecaCarro, itens, onClose, onSave }) {
  const carro = itens.find(i => i.id === pecaCarro.carro_id)
  const peca = itens.find(i => i.id === pecaCarro.peca_id)
  const [formData, setFormData] = useState({
    quantidade: pecaCarro.quantidade,
    data_instalacao: pecaCarro.data_instalacao?.split('T')[0],
    observacoes: pecaCarro.observacoes || ''
  })

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Manutenção">
      <div className="mb-4 p-3 bg-dark-700 rounded-lg text-xs border border-dark-600">
        <p className="flex justify-between"><strong>Veículo:</strong> <span>{carro?.nome || 'N/A'}</span></p>
        <p className="flex justify-between mt-1 font-bold text-primary-400"><strong>Peça:</strong> <span>{peca?.nome || 'N/A'}</span></p>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); onSave(formData); }} className="space-y-4">
        <div><label className="label">Quantidade Utilizada</label><input type="number" className="input" value={formData.quantidade} onChange={e => setFormData({...formData, quantidade: e.target.value})} /></div>
        <div><label className="label">Data</label><input type="date" className="input" value={formData.data_instalacao} onChange={e => setFormData({...formData, data_instalacao: e.target.value})} /></div>
        <textarea className="input h-20" value={formData.observacoes} onChange={e => setFormData({...formData, observacoes: e.target.value})} placeholder="Notas da manutenção..." />
        <button type="submit" className="btn btn-primary w-full py-3">Atualizar Registro</button>
      </form>
    </Modal>
  )
}