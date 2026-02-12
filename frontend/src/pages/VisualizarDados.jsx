import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Search, Edit, Trash2, Eye, Package, Calendar, Car, DollarSign, MapPin, Hash, ClipboardCheck, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import { formatItemName, formatDate } from '../utils/format'
import { getCidadesPorUF, ESTADOS } from '../utils/municipios'

const UFS = ESTADOS.map(e => e.sigla)

export default function VisualizarDados() {
  const [itens, setItens] = useState([])
  const [compromissos, setCompromissos] = useState([])
  const [pecasCarros, setPecasCarros] = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('itens')
  const [searchTerm, setSearchTerm] = useState('')

  // Estados de Modais
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
      toast.error('Erro ao sincronizar dados')
    } finally {
      setLoading(false)
    }
  }

  // --- CÁLCULOS DE KPI ---
  const stats = useMemo(() => {
    const patrimonio = itens.reduce((acc, i) => acc + (i.valor_compra * i.quantidade_total || 0), 0)
    const receitaTotal = compromissos.reduce((acc, c) => acc + (c.valor_total_contrato || 0), 0)
    return { patrimonio, receitaTotal, totalManutencao: pecasCarros.length }
  }, [itens, compromissos, pecasCarros])

  // --- FILTRO GLOBAL ---
  const filteredData = useMemo(() => {
    const term = searchTerm.toLowerCase()
    return {
      itens: itens.filter(i => i.nome?.toLowerCase().includes(term) || i.categoria?.toLowerCase().includes(term)),
      compromissos: compromissos.filter(c => c.contratante?.toLowerCase().includes(term) || c.nome_contrato?.toLowerCase().includes(term)),
      pecas: pecasCarros.filter(pc => {
        const v = itens.find(i => i.id === pc.carro_id)?.nome?.toLowerCase() || ''
        const p = itens.find(i => i.id === pc.peca_id)?.nome?.toLowerCase() || ''
        return v.includes(term) || p.includes(term)
      })
    }
  }, [searchTerm, itens, compromissos, pecasCarros])

  // --- HANDLERS DE PERSISTÊNCIA ---
  const handleDeleteItem = async () => {
    try {
      await itensAPI.deletar(deletingItem.id)
      toast.success('Ativo removido')
      loadData()
      setDeletingItem(null)
    } catch (e) { toast.error('Erro ao excluir') }
  }

  const handleDeleteCompromisso = async () => {
    try {
      await compromissosAPI.deletar(deletingCompromisso.id)
      toast.success('Contrato removido')
      loadData()
      setDeletingCompromisso(null)
    } catch (e) { toast.error('Erro ao excluir contrato') }
  }

  const handleSaveItem = async (data) => {
    try {
      await itensAPI.atualizar(editingItem.id, data)
      toast.success('Dados salvos!')
      loadData()
      setEditingItem(null)
    } catch (e) { toast.error('Erro ao salvar') }
  }

  const handleSaveCompromisso = async (data) => {
    try {
      await compromissosAPI.atualizar(editingCompromisso.id, data)
      toast.success('Contrato Master atualizado!')
      loadData()
      setEditingCompromisso(null)
    } catch (e) { toast.error('Erro ao salvar contrato') }
  }

  const handleSavePecaCarro = async (data) => {
    try {
      await api.put(`/api/pecas-carros/${editingPecaCarro.id}`, data)
      toast.success('Manutenção atualizada!')
      loadData()
      setEditingPecaCarro(null)
    } catch (e) { toast.error('Erro ao salvar manutenção') }
  }

  if (loading) return <div className="flex h-96 items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-10 px-4">
      {/* HEADER & KPIs */}
      <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter">Gestão de Ativos</h1>
          <p className="text-dark-400 font-medium">Brasília, DF • iFood Admin</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <StatCard label="Patrimônio" value={stats.patrimonio} isCurrency />
          <StatCard label="Receita" value={stats.receitaTotal} isCurrency color="text-green-400" />
          <StatCard label="Instalados" value={stats.totalManutencao} color="text-blue-400" />
        </div>
      </div>

      {/* SEARCH */}
      <div className="relative">
        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-dark-500" size={24} />
        <input 
          type="text" 
          placeholder="Busca global por ativo, cliente, placa..." 
          value={searchTerm} 
          onChange={e => setSearchTerm(e.target.value)} 
          className="input w-full pl-14 h-16 text-lg border-dark-700 bg-dark-800/40 rounded-2xl" 
        />
      </div>

      {/* TABS */}
      <div className="flex gap-2 p-1.5 bg-dark-800 rounded-2xl border border-dark-700 w-fit">
        <TabButton active={activeTab === 'itens'} label="Inventário" count={itens.length} icon={<Package size={18}/>} onClick={() => setActiveTab('itens')} />
        <TabButton active={activeTab === 'compromissos'} label="Contratos" count={compromissos.length} icon={<DollarSign size={18}/>} onClick={() => setActiveTab('compromissos')} />
        <TabButton active={activeTab === 'pecas-carros'} label="Manutenção" count={pecasCarros.length} icon={<Car size={18}/>} onClick={() => setActiveTab('pecas-carros')} />
      </div>

      {/* DATA AREA */}
      <div className="card overflow-hidden p-0 border-dark-700 bg-dark-900/40 backdrop-blur-lg shadow-2xl">
        <div className="overflow-x-auto">
          
          {/* TABELA INVENTÁRIO */}
          {activeTab === 'itens' && (
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="bg-dark-800/60 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[30%]">Ativo / Detalhes</th>
                  <th className="px-6 py-4 w-[15%]">Status</th>
                  <th className="px-6 py-4 w-[10%]">Estoque</th>
                  <th className="px-6 py-4 w-[15%] hidden md:table-cell">Aquisição</th>
                  <th className="px-6 py-4 w-[20%] hidden md:table-cell">Localização</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.itens.map(item => (
                  <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="font-bold text-dark-50 text-base">{formatItemName(item)}</div>
                      <div className="flex gap-2 mt-1">
                        <span className="text-[10px] bg-primary-500/10 text-primary-400 px-2 py-0.5 rounded font-black border border-primary-500/20">{item.categoria}</span>
                        {item.dados_categoria?.Placa && <span className="text-[10px] text-dark-500 font-mono">PLACA: {item.dados_categoria.Placa}</span>}
                      </div>
                    </td>
                    <td className="px-6 py-5"><BadgeStock qty={item.quantidade_total} /></td>
                    <td className="px-6 py-5 font-mono text-lg font-bold">{item.quantidade_total}</td>
                    <td className="px-6 py-5 text-dark-300 font-mono hidden md:table-cell">R$ {item.valor_compra?.toLocaleString('pt-BR')}</td>
                    <td className="px-6 py-5 text-xs text-dark-400 hidden md:table-cell"><MapPin size={12} className="inline mr-1"/> {item.cidade}/{item.uf}</td>
                    <td className="px-6 py-5 text-right">
                      <div className="flex justify-end gap-1">
                        <ActionButton icon={<Eye size={18}/>} onClick={() => setViewingItem(item)} />
                        <ActionButton icon={<Edit size={18}/>} onClick={() => setEditingItem(item)} hoverColor="hover:text-primary-400" />
                        <ActionButton icon={<Trash2 size={18}/>} onClick={() => setDeletingItem(item)} hoverColor="hover:text-red-400" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* TABELA CONTRATOS */}
          {activeTab === 'compromissos' && (
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="bg-dark-800/60 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[30%]">Contrato</th>
                  <th className="px-6 py-4 w-[35%] text-center">Itens</th>
                  <th className="px-6 py-4 w-[15%]">Vigência</th>
                  <th className="px-6 py-4 w-[10%]">Faturamento</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.compromissos.map(c => (
                  <tr key={c.id} className="hover:bg-green-500/[0.02] transition-colors">
                    <td className="px-6 py-5">
                      <div className="font-black text-dark-50 uppercase tracking-tight">{c.nome_contrato}</div>
                      <div className="text-[10px] text-dark-500 font-bold">{c.contratante}</div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-wrap justify-center gap-1">
                        {c.compromisso_itens?.map((ci, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-dark-700 text-dark-300 rounded text-[9px] font-black border border-dark-600">
                            {ci.quantidade}x {ci.itens?.nome}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-5 text-[11px]">
                       <div className="font-bold">{formatDate(c.data_inicio)}</div>
                       <div className="text-dark-500 italic">até {formatDate(c.data_fim)}</div>
                    </td>
                    <td className="px-6 py-5 text-green-400 font-black">R$ {c.valor_total_contrato?.toLocaleString('pt-BR')}</td>
                    <td className="px-6 py-5 text-right">
                      <div className="flex justify-end gap-1">
                        <ActionButton icon={<Edit size={18}/>} onClick={() => setEditingCompromisso(c)} />
                        <ActionButton icon={<Trash2 size={18}/>} onClick={() => setDeletingCompromisso(c)} hoverColor="hover:text-red-400" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* TABELA MANUTENÇÃO */}
          {activeTab === 'pecas-carros' && (
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="bg-dark-800/60 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr><th>Veículo / Placa</th><th>Peça Instalada</th><th>Qtd</th><th>Data</th><th className="text-right">Ações</th></tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.pecas.map(pc => {
                  const veiculo = itens.find(i => i.id === pc.carro_id)
                  const peca = itens.find(i => i.id === pc.peca_id)
                  return (
                    <tr key={pc.id} className="hover:bg-blue-500/[0.02]">
                      <td className="px-6 py-5">
                        <div className="font-bold text-dark-50">{veiculo?.nome}</div>
                        <div className="text-[10px] bg-blue-500/20 text-blue-400 px-2 rounded-full inline-block font-black mt-1">
                          {veiculo?.dados_categoria?.Placa || 'PEÇA AVULSA'}
                        </div>
                      </td>
                      <td className="px-6 py-5">
                        <div className="font-bold text-dark-200">{peca?.nome}</div>
                        <div className="text-[9px] text-dark-500 font-bold uppercase">{peca?.categoria}</div>
                      </td>
                      <td className="px-6 py-5 font-black text-blue-400 text-lg">{pc.quantidade}</td>
                      <td className="px-6 py-5 text-xs text-dark-400">{formatDate(pc.data_instalacao)}</td>
                      <td className="px-6 py-5 text-right"><ActionButton icon={<Edit size={18}/>} onClick={() => setEditingPecaCarro(pc)} /></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* MODAIS DE APOIO */}
      {viewingItem && <ViewItemModal item={viewingItem} onClose={() => setViewingItem(null)} />}
      
      {editingItem && (
        <EditItemModal 
          item={editingItem} 
          categorias={categorias} 
          onClose={() => setEditingItem(null)} 
          onSave={handleSaveItem} 
        />
      )}

      {editingCompromisso && (
        <EditCompromissoModal 
          compromisso={editingCompromisso} 
          onClose={() => setEditingCompromisso(null)} 
          onSave={handleSaveCompromisso} 
        />
      )}

      {editingPecaCarro && (
        <EditPecaCarroModal 
          pecaCarro={editingPecaCarro} 
          itens={itens} 
          onClose={() => setEditingPecaCarro(null)} 
          onSave={handleSavePecaCarro} 
        />
      )}

      <ConfirmDialog isOpen={!!deletingItem} onClose={() => setDeletingItem(null)} onConfirm={handleDeleteItem} title="Excluir Ativo" message="Remover permanentemente do inventário?" />
      <ConfirmDialog isOpen={!!deletingCompromisso} onClose={() => setDeletingCompromisso(null)} onConfirm={handleDeleteCompromisso} title="Remover Contrato" message="O estoque voltará para o inventário." />
    </div>
  )
}

// --- SUB-COMPONENTES DE INTERFACE ---

function StatCard({ label, value, isCurrency, color = "text-dark-50" }) {
  return (
    <div className="bg-dark-800/80 border border-dark-700 px-6 py-4 rounded-3xl min-w-[160px]">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-dark-500 mb-1">{label}</p>
      <p className={`text-2xl font-black ${color}`}>
        {isCurrency ? `R$ ${value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}` : value}
      </p>
    </div>
  )
}

function TabButton({ active, label, count, icon, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2.5 px-6 py-3 rounded-xl font-black text-sm transition-all ${active ? 'bg-primary-500 text-white shadow-xl' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'}`}>
      {icon} {label} <span className="text-[10px] bg-dark-700/50 px-2 py-0.5 rounded-full">{count}</span>
    </button>
  )
}

function ActionButton({ icon, onClick, hoverColor = "hover:text-white" }) {
  return (
    <button onClick={onClick} className={`p-2.5 text-dark-500 transition-all rounded-lg hover:bg-dark-700 ${hoverColor}`}>
      {icon}
    </button>
  )
}

function BadgeStock({ qty }) {
  const ok = qty > 0
  return (
    <span className={`px-2.5 py-1 rounded-full text-[9px] font-black uppercase border ${ok ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
      {ok ? 'Em Estoque' : 'Esgotado'}
    </span>
  )
}

// --- MODAIS DE EDIÇÃO ---

function EditItemModal({ item, categorias, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome: item.nome || '',
    quantidade_total: item.quantidade_total || 1,
    categoria: item.categoria || '',
    descricao: item.descricao || '',
    cidade: item.cidade || '',
    uf: item.uf || 'DF',
    valor_compra: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(item.valor_compra || 0),
    data_aquisicao: item.data_aquisicao || '',
    ...item.dados_categoria
  })
  const [camposExtras, setCamposExtras] = useState([])

  useEffect(() => {
    if (formData.categoria) categoriasAPI.obterCampos(formData.categoria).then(res => setCamposExtras(res.data || []))
  }, [formData.categoria])

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Ativo">
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
      }} className="space-y-4 max-h-[80vh] overflow-y-auto pr-2">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2"><label className="label">Nome</label><input className="input" value={formData.nome} onChange={e => setFormData({...formData, nome: e.target.value})} /></div>
          <div><label className="label">Qtd</label><input type="number" className="input" value={formData.quantidade_total} onChange={e => setFormData({...formData, quantidade_total: e.target.value})} /></div>
          <div><label className="label">Valor</label><input className="input" value={formData.valor_compra} onChange={e => setFormData({...formData, valor_compra: e.target.value})} /></div>
        </div>
        {camposExtras.length > 0 && (
          <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700 grid grid-cols-2 gap-3">
             <div className="col-span-2 text-[10px] font-black text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-1">Atributos de {formData.categoria}</div>
             {camposExtras.map(c => (
               <div key={c}><label className="label capitalize">{c}</label><input className="input bg-dark-900" value={formData[c] || ''} onChange={e => setFormData({...formData, [c]: e.target.value})} /></div>
             ))}
          </div>
        )}
        <button type="submit" className="btn btn-primary w-full py-4 font-black">SALVAR ALTERAÇÕES</button>
      </form>
    </Modal>
  )
}

function EditCompromissoModal({ compromisso, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome_contrato: compromisso.nome_contrato || '',
    contratante: compromisso.contratante || '',
    valor_total_contrato: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(compromisso.valor_total_contrato || 0),
    data_inicio: compromisso.data_inicio?.split('T')[0] || '',
    data_fim: compromisso.data_fim?.split('T')[0] || '',
    uf: compromisso.uf || 'DF',
    cidade: compromisso.cidade || ''
  })
  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Contrato">
      <form onSubmit={(e) => {
        e.preventDefault()
        onSave({...formData, valor_total_contrato: parseFloat(formData.valor_total_contrato.replace(/\./g, '').replace(',', '.')) || 0 })
      }} className="space-y-4">
        <div><label className="label">Nome do Evento</label><input className="input font-bold" value={formData.nome_contrato} onChange={e => setFormData({...formData, nome_contrato: e.target.value})} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label text-green-500">Valor Total</label><input className="input text-green-400 font-bold" value={formData.valor_total_contrato} onChange={e => setFormData({...formData, valor_total_contrato: e.target.value})} /></div>
          <div><label className="label">Início</label><input type="date" className="input" value={formData.data_inicio} onChange={e => setFormData({...formData, data_inicio: e.target.value})} /></div>
        </div>
        <button type="submit" className="btn btn-primary w-full py-4 font-black">ATUALIZAR CONTRATO</button>
      </form>
    </Modal>
  )
}

function EditPecaCarroModal({ pecaCarro, itens, onClose, onSave }) {
  const v = itens.find(i => i.id === pecaCarro.carro_id)
  const p = itens.find(i => i.id === pecaCarro.peca_id)
  const [formData, setFormData] = useState({ quantidade: pecaCarro.quantidade, data_instalacao: pecaCarro.data_instalacao?.split('T')[0] })
  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Manutenção">
      <div className="mb-4 p-3 bg-dark-800 rounded-lg text-xs">
        <p><strong>Veículo:</strong> {v?.nome}</p>
        <p><strong>Peça:</strong> {p?.nome}</p>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); onSave(formData); }} className="space-y-4">
        <div><label className="label">Qtd Aplicada</label><input type="number" className="input" value={formData.quantidade} onChange={e => setFormData({...formData, quantidade: e.target.value})} /></div>
        <div><label className="label">Data</label><input type="date" className="input" value={formData.data_instalacao} onChange={e => setFormData({...formData, data_instalacao: e.target.value})} /></div>
        <button type="submit" className="btn btn-primary w-full py-3 font-bold">SALVAR</button>
      </form>
    </Modal>
  )
}

function ViewItemModal({ item, onClose }) {
  return (
    <Modal isOpen={true} onClose={onClose} title="Ficha Técnica">
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700 text-center">
            <span className="text-[10px] font-black text-dark-500 block mb-1 uppercase">Aquisição</span>
            <span className="text-xl font-black text-green-400">R$ {item.valor_compra?.toLocaleString('pt-BR')}</span>
          </div>
          <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700 text-center">
            <span className="text-[10px] font-black text-dark-500 block mb-1 uppercase">Entrada</span>
            <span className="text-xl font-bold text-dark-100">{formatDate(item.data_aquisicao)}</span>
          </div>
        </div>
        {item.dados_categoria && (
          <div className="p-5 bg-dark-800/50 rounded-2xl border border-dark-700">
            <h4 className="text-[10px] font-black text-primary-500 uppercase tracking-widest mb-3 border-b border-dark-700 pb-1">Atributos Técnicos</h4>
            <div className="grid grid-cols-2 gap-y-2 text-sm">
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