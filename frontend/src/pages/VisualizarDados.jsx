import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Search, Edit, Trash2, Eye, Package, Calendar, Car, DollarSign, MapPin, Hash, Coins, Plus, Minus, X } from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import { formatItemName, formatDate } from '../utils/format'

export default function VisualizarDados() {
  const [itens, setItens] = useState([])
  const [compromissos, setCompromissos] = useState([])
  const [pecasCarros, setPecasCarros] = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('itens')
  const [searchTerm, setSearchTerm] = useState('')

  // Modais de Controle
  const [editingItem, setEditingItem] = useState(null)
  const [editingCompromisso, setEditingCompromisso] = useState(null)
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
      toast.error('Erro de sincronização. Verifique o servidor Railway.')
    } finally {
      setLoading(false)
    }
  }

  // --- KPIs (image_7a87d9.png) ---
  const stats = useMemo(() => {
    const patrimonio = itens.reduce((acc, i) => acc + (Number(i.valor_compra || 0) * (i.quantidade_total || 0)), 0)
    const receitaTotal = compromissos.reduce((acc, c) => acc + (Number(c.valor_total_contrato) || 0), 0)
    return { patrimonio, receitaTotal }
  }, [itens, compromissos])

  const filteredData = useMemo(() => {
    const term = searchTerm.toLowerCase()
    return {
      itens: itens.filter(i => i.nome?.toLowerCase().includes(term) || i.categoria?.toLowerCase().includes(term)),
      compromissos: compromissos.filter(c => c.contratante?.toLowerCase().includes(term) || (c.nome_contrato || '').toLowerCase().includes(term)),
      pecas: pecasCarros.filter(pc => {
        const v = itens.find(i => i.id === pc.carro_id)?.nome?.toLowerCase() || ''
        const p = itens.find(i => i.id === pc.peca_id)?.nome?.toLowerCase() || ''
        return v.includes(term) || p.includes(term)
      })
    }
  }, [searchTerm, itens, compromissos, pecasCarros])

  // --- PERSISTÊNCIA ---
  const handleSaveItem = async (data) => {
    try {
      await itensAPI.atualizar(editingItem.id, data)
      toast.success('Ativo atualizado!')
      loadData(); setEditingItem(null)
    } catch (e) { toast.error('Erro ao salvar item') }
  }

  const handleDeleteCompromisso = async () => {
    const loadId = toast.loading('Removendo contrato e vínculos...')
    try {
      await api.delete(`/api/compromissos/${deletingCompromisso.id}`)
      toast.success('Contrato excluído permanentemente!', { id: loadId })
      setDeletingCompromisso(null)
      loadData()
    } catch (e) {
      const msg = e.response?.data?.detail || 'Erro ao excluir contrato (verifique Foreign Keys)'
      toast.error(msg, { id: loadId })
    }
  }

  const handleSaveCompromisso = async (data) => {
    try {
      await compromissosAPI.atualizar(editingCompromisso.id, data)
      toast.success('Contrato e Itens sincronizados!')
      loadData(); setEditingCompromisso(null)
    } catch (e) { toast.error('Erro ao atualizar contrato') }
  }

  if (loading) return <div className="flex h-96 items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto px-4 pb-20">
      {/* KPIs HEADER */}
      <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase">Visualizar Dados</h1>
          <p className="text-dark-400 font-medium italic">Star Gestão • Operação Brasília, DF</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <StatMini label="Patrimônio Total" value={stats.patrimonio} isCurrency />
          <StatMini label="Receita Master" value={stats.receitaTotal} isCurrency color="text-green-400" />
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-dark-500" size={24} />
        <input type="text" placeholder="Pesquisar em tudo..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="input w-full pl-14 h-16 text-xl border-dark-700 bg-dark-800/60 backdrop-blur-md rounded-2xl" />
      </div>

      <div className="flex gap-2 p-1.5 bg-dark-800 rounded-2xl border border-dark-700 w-fit">
        <TabItem active={activeTab === 'itens'} label="Inventário" count={itens.length} icon={<Package size={18}/>} onClick={() => setActiveTab('itens')} />
        <TabItem active={activeTab === 'compromissos'} label="Contratos" count={compromissos.length} icon={<DollarSign size={18}/>} onClick={() => setActiveTab('compromissos')} />
        <TabItem active={activeTab === 'pecas-carros'} label="Manutenção" count={pecasCarros.length} icon={<Car size={18}/>} onClick={() => setActiveTab('pecas-carros')} />
      </div>

      {/* ÁREA DE TABELAS (GRID TRAVADO) */}
      <div className="card overflow-hidden p-0 border-dark-700 bg-dark-900/40 backdrop-blur-lg shadow-2xl">
        <div className="overflow-x-auto">
          
          {/* TABELA INVENTÁRIO (image_7aecd4.png) */}
          {activeTab === 'itens' && (
            <table className="w-full text-left border-collapse min-w-[1200px] table-fixed">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[25%]">Ativo / Especificações</th>
                  <th className="px-6 py-4 w-[10%] text-center">Estoque</th>
                  <th className="px-6 py-4 w-[12%]">Custo Unit.</th>
                  <th className="px-6 py-4 w-[15%] text-green-500 font-black">Valor em Estoque</th>
                  <th className="px-6 py-4 w-[13%]">Aquisição</th>
                  <th className="px-6 py-4 w-[15%] hidden lg:table-cell">Base</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.itens.map(item => (
                  <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="font-bold text-dark-50 text-base">{item.nome}</div>
                      <div className="flex gap-2 mt-1">
                        <span className="text-[9px] bg-primary-500/10 text-primary-400 px-1.5 py-0.5 rounded font-black border border-primary-500/20">{item.categoria}</span>
                        {item.dados_categoria?.Placa && <span className="text-[9px] bg-dark-700 px-1.5 py-0.5 rounded font-mono text-dark-400 border border-dark-600 uppercase font-black tracking-tighter">{item.dados_categoria.Placa}</span>}
                      </div>
                    </td>
                    <td className="px-6 py-5 font-mono text-lg font-bold text-center">{item.quantidade_total}</td>
                    <td className="px-6 py-5 text-dark-300 font-mono">R$ {parseFloat(item.valor_compra || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="px-6 py-5 text-green-400 font-black font-mono">R$ {(Number(item.valor_compra || 0) * (item.quantidade_total || 0)).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="px-6 py-5 text-xs text-dark-400 font-mono">{formatDate(item.data_aquisicao)}</td>
                    <td className="px-6 py-5 text-xs text-dark-400 hidden lg:table-cell uppercase font-bold">{item.cidade}/{item.uf}</td>
                    <td className="px-6 py-5 text-right flex gap-1 justify-end opacity-20 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => setViewingItem(item)} className="p-2 hover:bg-dark-700 rounded-lg"><Eye size={18}/></button>
                      <button onClick={() => setEditingItem(item)} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><Edit size={18}/></button>
                      <button onClick={() => setDeletingItem(item)} className="p-2 hover:bg-dark-700 rounded-lg text-red-400"><Trash2 size={18}/></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* TABELA CONTRATOS (image_85d57b.png) */}
          {activeTab === 'compromissos' && (
            <table className="w-full text-left border-collapse min-w-[1000px] table-fixed">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[25%]">Contrato / Cliente</th>
                  <th className="px-6 py-4 w-[35%] text-center">Itens Reservados</th>
                  <th className="px-6 py-4 w-[15%]">Vigência</th>
                  <th className="px-6 py-4 w-[15%] text-right">Faturamento</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.compromissos.map(c => (
                  <tr key={c.id} className="hover:bg-green-500/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="font-black text-dark-50 text-base uppercase tracking-tight">{c.nome_contrato}</div>
                      <div className="text-[10px] text-dark-500 font-bold uppercase mt-1">{c.contratante}</div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-wrap justify-center gap-1.5">
                        {c.compromisso_itens?.map((ci, idx) => (
                          <span key={idx} className="px-2.5 py-1 bg-primary-500/10 text-primary-400 rounded-lg text-[9px] font-black border border-primary-500/20 shadow-sm">
                            {ci.quantidade}x {ci.itens?.nome || 'Equipamento'}
                          </span>
                        )) || <span className="text-dark-600 text-[10px] italic">Sem equipamentos</span>}
                      </div>
                    </td>
                    <td className="px-6 py-5 text-[11px] font-medium leading-tight">
                       <div className="text-dark-100 font-bold">{formatDate(c.data_inicio)}</div>
                       <div className="text-dark-500 mt-1 italic uppercase font-black text-[9px]">até {formatDate(c.data_fim)}</div>
                    </td>
                    <td className="px-6 py-5 text-green-400 font-black text-lg font-mono text-right">
                      R$ {(Number(c.valor_total_contrato) || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                    </td>
                    <td className="px-6 py-5 text-right flex gap-2 justify-end opacity-20 group-hover:opacity-100 transition-opacity">
                       <button onClick={() => setEditingCompromisso(c)} className="p-2 text-primary-400 hover:bg-dark-700 rounded-lg"><Edit size={18}/></button>
                       <button onClick={() => setDeletingCompromisso(c)} className="p-2 text-red-400 hover:bg-dark-700 rounded-lg"><Trash2 size={18}/></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* TABELA MANUTENÇÃO */}
          {activeTab === 'pecas-carros' && (
            <table className="w-full text-left border-collapse min-w-[1000px] table-fixed">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr><th className="px-6 py-4 w-[30%]">Veículo Alvo</th><th className="px-6 py-4 w-[30%]">Peça Instalada</th><th className="px-6 py-4 w-[10%] text-center">Qtd</th><th className="px-6 py-4 w-[20%]">Data Instalação</th><th className="px-6 py-4 w-[10%] text-right">Ações</th></tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {pecasCarros.map(pc => {
                  const v = itens.find(i => i.id === pc.carro_id);
                  const p = itens.find(i => i.id === pc.peca_id);
                  return (
                    <tr key={pc.id} className="hover:bg-blue-500/[0.02] transition-colors group">
                      <td className="px-6 py-5 font-bold text-dark-50">{v?.nome} <span className="text-[10px] text-blue-400 block uppercase font-black">{v?.dados_categoria?.Placa}</span></td>
                      <td className="px-6 py-5 font-bold text-primary-400 uppercase text-xs">{p?.nome}</td>
                      <td className="px-6 py-5 font-black text-lg text-blue-400 text-center">{pc.quantidade}</td>
                      <td className="px-6 py-5 text-xs text-dark-400 font-mono font-bold tracking-widest">{formatDate(pc.data_instalacao)}</td>
                      <td className="px-6 py-5 text-right"><button className="p-2 hover:bg-dark-700 rounded-lg opacity-20 group-hover:opacity-100 transition-opacity"><Edit size={18}/></button></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* --- MODAL EDITAR CONTRATO MASTER (DATAS E ITENS) --- */}
      {editingCompromisso && (
        <EditCompromissoModal 
          compromisso={editingCompromisso} 
          itensDisponiveis={itens} 
          onClose={() => setEditingCompromisso(null)} 
          onSave={handleSaveCompromisso} 
        />
      )}

      {/* --- MODAL EDITAR ITEM (PATRIMÔNIO E JSONB) --- */}
      {editingItem && (
        <EditItemModal 
          item={editingItem} 
          categorias={categorias} 
          onClose={() => setEditingItem(null)} 
          onSave={handleSaveItem} 
        />
      )}

      {viewingItem && <ViewItemModal item={viewingItem} onClose={() => setViewingItem(null)} />}
      
      <ConfirmDialog isOpen={!!deletingItem} onClose={() => setDeletingItem(null)} onConfirm={() => itensAPI.deletar(deletingItem.id).then(loadData)} title="Excluir Ativo" />
      <ConfirmDialog isOpen={!!deletingCompromisso} onClose={() => setDeletingCompromisso(null)} onConfirm={handleDeleteCompromisso} title="Remover Contrato" message="Atenção: Isso removerá o contrato, os itens vinculados e o registro financeiro associado." />

    </div>
  )
}

// --- SUB-COMPONENTES DE INTERFACE ---

function StatMini({ label, value, isCurrency, color = "text-dark-50" }) {
  return (
    <div className="bg-dark-800/80 border border-dark-700 px-6 py-4 rounded-3xl min-w-[170px] shadow-xl">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-dark-500 mb-2">{label}</p>
      <p className={`text-2xl font-black ${color}`}>
        {isCurrency ? `R$ ${value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}` : value}
      </p>
    </div>
  )
}

function TabItem({ active, label, count, icon, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-6 py-3.5 rounded-xl font-black text-sm transition-all ${active ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'}`}>
      {icon} {label} <span className="text-[10px] bg-dark-700/50 px-2 py-0.5 rounded-full font-bold">{count}</span>
    </button>
  )
}

// --- MODAL EDITAR COMPROMISSO (O MAIS COMPLEXO) ---

function EditCompromissoModal({ compromisso, itensDisponiveis, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome_contrato: compromisso.nome_contrato || '',
    contratante: compromisso.contratante || '',
    valor_total_contrato: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(compromisso.valor_total_contrato || 0),
    data_inicio: compromisso.data_inicio?.split('T')[0] || '',
    data_fim: compromisso.data_fim?.split('T')[0] || '',
    itens: compromisso.compromisso_itens?.map(ci => ({ 
      id: ci.item_id, 
      nome: ci.itens?.nome, 
      quantidade: ci.quantidade 
    })) || []
  })

  const addItem = (item) => {
    if (formData.itens.find(i => i.id === item.id)) return
    setFormData({ ...formData, itens: [...formData.itens, { id: item.id, nome: item.nome, quantidade: 1 }] })
  }

  const removeItem = (id) => setFormData({ ...formData, itens: formData.itens.filter(i => i.id !== id) })

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Contrato Master">
      <form onSubmit={(e) => { 
        e.preventDefault(); 
        onSave({ 
          ...formData, 
          valor_total_contrato: parseFloat(formData.valor_total_contrato.replace(/\./g, '').replace(',', '.')) || 0 
        }); 
      }} className="space-y-6 max-h-[85vh] overflow-y-auto pr-2">
        
        {/* DADOS DO CONTRATO */}
        <div className="space-y-4">
          <div className="text-[10px] font-black text-primary-500 uppercase tracking-widest border-b border-dark-700 pb-1">Cabeçalho e Período</div>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2"><label className="label">Nome do Contrato</label><input className="input font-bold" value={formData.nome_contrato} onChange={e => setFormData({...formData, nome_contrato: e.target.value})} /></div>
            <div><label className="label uppercase text-[10px] font-black">Data Início</label><input type="date" className="input" value={formData.data_inicio} onChange={e => setFormData({...formData, data_inicio: e.target.value})} /></div>
            <div><label className="label uppercase text-[10px] font-black">Data Término</label><input type="date" className="input" value={formData.data_fim} onChange={e => setFormData({...formData, data_fim: e.target.value})} /></div>
            <div className="col-span-2"><label className="label text-green-500 font-bold">Faturamento Total do Evento</label><input className="input text-green-400 font-black text-xl" value={formData.valor_total_contrato} onChange={e => setFormData({...formData, valor_total_contrato: e.target.value})} /></div>
          </div>
        </div>

        {/* GESTÃO DE EQUIPAMENTOS */}
        <div className="space-y-4 p-5 bg-dark-800 rounded-3xl border border-dark-700 shadow-inner">
          <div className="flex justify-between items-center border-b border-dark-700 pb-2">
            <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Equipamentos no Contrato</span>
            <select className="bg-dark-900 text-[10px] rounded px-2 border border-dark-600" onChange={(e) => addItem(itensDisponiveis.find(i => i.id === parseInt(e.target.value)))}>
              <option value="">+ Adicionar Item</option>
              {itensDisponiveis.map(i => <option key={i.id} value={i.id}>{i.nome}</option>)}
            </select>
          </div>
          
          <div className="space-y-2">
            {formData.itens.map(item => (
              <div key={item.id} className="flex justify-between items-center bg-dark-900 p-3 rounded-xl border border-dark-700">
                <span className="font-bold text-dark-100 text-xs">{item.nome}</span>
                <div className="flex items-center gap-3">
                  <div className="flex items-center bg-dark-800 rounded-lg px-2 border border-dark-700">
                    <button type="button" onClick={() => {
                      const newItens = [...formData.itens]
                      const idx = newItens.findIndex(i => i.id === item.id)
                      newItens[idx].quantidade = Math.max(1, newItens[idx].quantidade - 1)
                      setFormData({...formData, itens: newItens})
                    }}><Minus size={14}/></button>
                    <span className="px-3 font-black text-primary-400">{item.quantidade}</span>
                    <button type="button" onClick={() => {
                      const newItens = [...formData.itens]
                      const idx = newItens.findIndex(i => i.id === item.id)
                      newItens[idx].quantidade += 1
                      setFormData({...formData, itens: newItens})
                    }}><Plus size={14}/></button>
                  </div>
                  <button type="button" onClick={() => removeItem(item.id)} className="text-red-500 hover:bg-red-500/10 p-1 rounded-lg"><X size={16}/></button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button type="submit" className="btn btn-primary w-full py-4 font-black uppercase shadow-xl shadow-primary-500/20 text-lg">Atualizar Contrato Master</button>
      </form>
    </Modal>
  )
}

// --- MODAL EDITAR ITEM ---

function EditItemModal({ item, categorias, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome: item.nome || '',
    quantidade_total: item.quantidade_total || 1,
    categoria: item.categoria || '',
    valor_compra: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(item.valor_compra || 0),
    data_aquisicao: item.data_aquisicao?.split('T')[0] || '',
    ...item.dados_categoria
  })
  const [camposExtras, setCamposExtras] = useState([])

  useEffect(() => {
    if (formData.categoria) categoriasAPI.obterCampos(formData.categoria).then(res => setCamposExtras(res.data || []))
  }, [formData.categoria])

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Patrimônio">
      <form onSubmit={(e) => {
        e.preventDefault()
        const c_extras = {}
        camposExtras.forEach(c => c_extras[c] = formData[c])
        onSave({
          ...formData,
          quantidade_total: parseInt(formData.quantidade_total),
          valor_compra: parseFloat(formData.valor_compra.replace(/\./g, '').replace(',', '.')) || 0,
          campos_categoria: c_extras
        })
      }} className="space-y-6 max-h-[85vh] overflow-y-auto pr-2">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2"><label className="label">Nome</label><input className="input" value={formData.nome} onChange={e => setFormData({...formData, nome: e.target.value})} /></div>
          <div><label className="label">Quantidade</label><input type="number" className="input" value={formData.quantidade_total} onChange={e => setFormData({...formData, quantidade_total: e.target.value})} /></div>
          <div><label className="label">Valor Aquisição</label><input className="input" value={formData.valor_compra} onChange={e => setFormData({...formData, valor_compra: e.target.value})} /></div>
          <div className="md:col-span-2"><label className="label">Data de Entrada no Estoque</label><input type="date" className="input" value={formData.data_aquisicao} onChange={e => setFormData({...formData, data_aquisicao: e.target.value})} /></div>
        </div>
        {camposExtras.length > 0 && (
          <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700 grid grid-cols-2 gap-3 shadow-inner">
             <div className="col-span-2 text-[10px] font-black text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-1">Atributos JSONB</div>
             {camposExtras.map(c => (
               <div key={c}><label className="label capitalize text-[10px]">{c}</label><input className="input bg-dark-900 border-blue-500/10" value={formData[c] || ''} onChange={e => setFormData({...formData, [c]: e.target.value})} /></div>
             ))}
          </div>
        )}
        <button type="submit" className="btn btn-primary w-full py-4 font-black uppercase shadow-xl shadow-primary-500/30">Salvar Alterações</button>
      </form>
    </Modal>
  )
}

function ViewItemModal({ item, onClose }) {
  return (
    <Modal isOpen={true} onClose={onClose} title="Ficha Técnica Completa">
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-5 bg-dark-800 rounded-3xl border border-dark-700 text-center shadow-xl">
            <span className="text-[10px] font-black text-dark-500 block mb-1 uppercase tracking-widest">Patrimônio Líquido</span>
            <span className="text-xl font-black text-green-400 font-mono">R$ {(item.valor_compra * item.quantidade_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
          </div>
          <div className="p-5 bg-dark-800 rounded-3xl border border-dark-700 text-center shadow-xl">
            <span className="text-[10px] font-black text-dark-500 block mb-1 uppercase tracking-widest font-mono">Entrada</span>
            <span className="text-xl font-bold text-dark-50 font-mono tracking-tighter">{formatDate(item.data_aquisicao)}</span>
          </div>
        </div>
        {item.dados_categoria && (
          <div className="p-6 bg-dark-800/50 rounded-3xl border border-dark-700 shadow-2xl">
            <h4 className="text-[10px] font-black text-primary-500 uppercase tracking-widest mb-4 border-b border-dark-700 pb-2">Atributos Técnicos</h4>
            <div className="grid grid-cols-2 gap-y-3 text-sm">
               {Object.entries(item.dados_categoria).map(([k,v]) => (
                 <p key={k} className="flex justify-between border-b border-dark-700/30 pb-1 pr-4 uppercase text-[11px]"><strong className="text-dark-400">{k}:</strong> <span className="font-bold text-blue-400">{v}</span></p>
               ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}