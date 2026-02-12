import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Search, Edit, Trash2, Eye, Package, Calendar, Car, DollarSign, MapPin, ClipboardList, Settings } from 'lucide-react'
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

  // Modais
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

  const stats = useMemo(() => {
    const patrimonio = itens.reduce((acc, i) => acc + (i.valor_compra * i.quantidade_total || 0), 0)
    const receitaTotal = compromissos.reduce((acc, c) => acc + (c.valor_total_contrato || 0), 0)
    return { patrimonio, receitaTotal, totalManutencao: pecasCarros.length }
  }, [itens, compromissos, pecasCarros])

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

  // Handlers
  const handleSaveItem = async (data) => {
    try {
      await itensAPI.atualizar(editingItem.id, data)
      toast.success('Item e atributos atualizados!')
      loadData()
      setEditingItem(null)
    } catch (e) { toast.error('Erro ao salvar atributos') }
  }

  if (loading) return <div className="flex h-96 items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-20">
      {/* KPI BAR */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter">Gestão de Ativos</h1>
          <p className="text-dark-400 font-medium">Brasília, DF • iFood Senior AI Engine Admin</p>
        </div>
        <div className="flex gap-3">
          <StatBox label="Patrimônio" value={stats.patrimonio} isCurrency />
          <StatBox label="Receita" value={stats.receitaTotal} isCurrency color="text-green-400" />
          <StatBox label="Em Manutenção" value={stats.totalManutencao} color="text-blue-400" />
        </div>
      </div>

      {/* SEARCH BAR */}
      <div className="relative">
        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-dark-500" size={24} />
        <input 
          type="text" 
          placeholder="Busca inteligente por ativo, cliente, placa ou contrato..." 
          value={searchTerm} 
          onChange={e => setSearchTerm(e.target.value)} 
          className="input w-full pl-14 h-16 text-xl border-dark-700 bg-dark-800/60 backdrop-blur-md rounded-2xl focus:ring-2 focus:ring-primary-500/50 transition-all" 
        />
      </div>

      {/* TABS */}
      <div className="flex gap-2 p-1.5 bg-dark-800 rounded-2xl border border-dark-700 w-fit">
        <TabItem active={activeTab === 'itens'} label="Inventário" icon={<Package size={18}/>} onClick={() => setActiveTab('itens')} />
        <TabItem active={activeTab === 'compromissos'} label="Contratos" icon={<DollarSign size={18}/>} onClick={() => setActiveTab('compromissos')} />
        <TabItem active={activeTab === 'pecas-carros'} label="Manutenção" icon={<Car size={18}/>} onClick={() => setActiveTab('pecas-carros')} />
      </div>

      {/* TABLES */}
      <div className="card overflow-hidden p-0 border-dark-700 bg-dark-900/40 backdrop-blur-lg">
        <div className="overflow-x-auto">
          {activeTab === 'itens' && (
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[35%]">Ativo / Especificações</th>
                  <th className="px-6 py-4 w-[15%]">Status</th>
                  <th className="px-6 py-4 w-[10%]">Estoque</th>
                  <th className="px-6 py-4 w-[15%]">Valor Aquisição</th>
                  <th className="px-6 py-4 w-[15%]">Localização</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.itens.map(item => (
                  <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="font-bold text-dark-50 text-base">{formatItemName(item)}</div>
                      <div className="flex flex-wrap gap-2 mt-1.5">
                        <span className="text-[10px] bg-primary-500/10 text-primary-400 px-2 py-0.5 rounded font-black uppercase tracking-tighter border border-primary-500/20">{item.categoria}</span>
                        {item.dados_categoria && Object.entries(item.dados_categoria).slice(0, 2).map(([k, v]) => (
                          <span key={k} className="text-[10px] bg-dark-700 text-dark-400 px-2 py-0.5 rounded border border-dark-600 font-mono">{k}: {v}</span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-5"><BadgeStock qty={item.quantidade_total} /></td>
                    <td className="px-6 py-5 font-mono text-lg font-bold">{item.quantidade_total}</td>
                    <td className="px-6 py-5 text-dark-300 font-mono">R$ {item.valor_compra?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="px-6 py-5 text-xs text-dark-400 font-medium"><MapPin size={12} className="inline mr-1 text-primary-500"/> {item.cidade}/{item.uf}</td>
                    <td className="px-6 py-5 text-right">
                      <div className="flex justify-end gap-1 opacity-20 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => setViewingItem(item)} className="p-2 hover:bg-dark-700 rounded-lg transition-colors"><Eye size={18}/></button>
                        <button onClick={() => setEditingItem(item)} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><Edit size={18}/></button>
                        <button onClick={() => setDeletingItem(item)} className="p-2 hover:bg-dark-700 rounded-lg text-red-400"><Trash2 size={18}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'compromissos' && (
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[25%]">Contrato / Cliente</th>
                  <th className="px-6 py-4 w-[35%] text-center">Itens no Contrato</th>
                  <th className="px-6 py-4 w-[15%]">Vigência</th>
                  <th className="px-6 py-4 w-[15%]">Faturamento</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.compromissos.map(c => (
                  <tr key={c.id} className="hover:bg-green-500/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="font-black text-dark-50 text-base uppercase tracking-tight">{c.nome_contrato}</div>
                      <div className="text-[11px] text-dark-500 font-bold mt-1 leading-none">{c.contratante}</div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-wrap justify-center gap-1.5">
                        {c.compromisso_itens?.map((ci, idx) => (
                          <span key={idx} className="px-2.5 py-1 bg-primary-500/10 text-primary-400 rounded-lg text-[10px] font-black border border-primary-500/20">
                            {ci.quantidade}x {ci.itens?.nome}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-5 text-[11px] font-medium">
                      <div className="text-dark-100 font-bold">{formatDate(c.data_inicio)}</div>
                      <div className="text-dark-500 mt-1 italic">até {formatDate(c.data_fim)}</div>
                    </td>
                    <td className="px-6 py-5 text-green-400 font-black text-lg font-mono">R$ {c.valor_total_contrato?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="px-6 py-5 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => setEditingCompromisso(c)} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><Edit size={18}/></button>
                        <button onClick={() => setDeletingCompromisso(c)} className="p-2 hover:bg-dark-700 rounded-lg text-red-400"><Trash2 size={18}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* DYNAMIC EDIT ITEM MODAL */}
      {editingItem && (
        <EditItemModal 
          item={editingItem} 
          categorias={categorias} 
          onClose={() => setEditingItem(null)} 
          onSave={handleSaveItem} 
        />
      )}
      
      {/* OTHER MODALS (VIEW, DELETE) */}
      {viewingItem && <ViewItemModal item={viewingItem} onClose={() => setViewingItem(null)} />}
      <ConfirmDialog isOpen={!!deletingItem} onClose={() => setDeletingItem(null)} onConfirm={() => itensAPI.deletar(deletingItem.id).then(loadData)} title="Excluir Ativo" message="Remover permanentemente do inventário?" />
    </div>
  )
}

// --- SUB-COMPONENTS ---

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
    ...item.dados_categoria // Carrega campos específicos existentes
  })
  
  const [camposDinamicos, setCamposDinamicos] = useState([])

  useEffect(() => {
    if (formData.categoria) {
      categoriasAPI.obterCampos(formData.categoria).then(res => setCamposDinamicos(res.data || []))
    }
  }, [formData.categoria])

  const handleSubmit = (e) => {
    e.preventDefault()
    // Separa dados gerais de específicos
    const dadosGerais = {
      nome: formData.nome,
      quantidade_total: parseInt(formData.quantidade_total),
      categoria: formData.categoria,
      descricao: formData.descricao,
      cidade: formData.cidade,
      uf: formData.uf,
      valor_compra: parseFloat(formData.valor_compra.replace(/\./g, '').replace(',', '.')) || 0,
      data_aquisicao: formData.data_aquisicao || null
    }

    const camposExtras = {}
    camposDinamicos.forEach(campo => {
      camposExtras[campo] = formData[campo]
    })

    onSave({ ...dadosGerais, campos_categoria: camposExtras })
  }

  return (
    <Modal isOpen={true} onClose={onClose} title={`Editar Ativo: ${item.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-6 max-h-[85vh] overflow-y-auto px-1">
        {/* GERAL */}
        <div className="space-y-4">
          <div className="text-[10px] font-black text-primary-500 uppercase tracking-widest border-b border-dark-700 pb-1">Dados Gerais</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2"><label className="label">Nome do Ativo</label><input className="input" value={formData.nome} onChange={e => setFormData({...formData, nome: e.target.value})} /></div>
            <div><label className="label">Qtd Total</label><input type="number" className="input" value={formData.quantidade_total} onChange={e => setFormData({...formData, quantidade_total: e.target.value})} /></div>
            <div><label className="label">Valor Aquisição</label><input className="input" value={formData.valor_compra} onChange={e => setFormData({...formData, valor_compra: e.target.value})} /></div>
          </div>
        </div>

        {/* ESPECÍFICOS DA CATEGORIA */}
        {camposDinamicos.length > 0 && (
          <div className="space-y-4 bg-dark-800/40 p-5 rounded-2xl border border-dark-700">
            <div className="text-[10px] font-black text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-1">Atributos de {formData.categoria}</div>
            <div className="grid grid-cols-2 gap-4">
              {camposDinamicos.map(campo => (
                <div key={campo}>
                  <label className="label capitalize">{campo}</label>
                  <input className="input bg-dark-900" value={formData[campo] || ''} onChange={e => setFormData({...formData, [campo]: e.target.value})} />
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary flex-1">Cancelar</button>
          <button type="submit" className="btn btn-primary flex-1 py-4 font-black">SALVAR ALTERAÇÕES</button>
        </div>
      </form>
    </Modal>
  )
}

function StatBox({ label, value, isCurrency, color = "text-dark-50" }) {
  return (
    <div className="bg-dark-800/80 border border-dark-700 px-6 py-4 rounded-3xl min-w-[170px] shadow-xl">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-dark-500 mb-2">{label}</p>
      <p className={`text-2xl font-black ${color}`}>
        {isCurrency ? `R$ ${value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}` : value}
      </p>
    </div>
  )
}

function TabItem({ active, label, icon, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2.5 px-6 py-3.5 rounded-xl font-black text-sm transition-all ${active ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'}`}>
      {icon} {label}
    </button>
  )
}

function BadgeStock({ qty }) {
  const isOk = qty > 0
  return (
    <span className={`px-2.5 py-1 rounded-full text-[9px] font-black uppercase border ${isOk ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
      {isOk ? 'Disponível' : 'Esgotado'}
    </span>
  )
}

function ViewItemModal({ item, onClose }) {
  return (
    <Modal isOpen={true} onClose={onClose} title="Ficha do Ativo">
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700 text-center">
            <span className="text-[10px] font-black text-dark-500 uppercase block mb-1">Custo Aquisição</span>
            <span className="text-xl font-black text-green-400 font-mono">R$ {item.valor_compra?.toLocaleString('pt-BR')}</span>
          </div>
          <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700 text-center">
            <span className="text-[10px] font-black text-dark-500 uppercase block mb-1">Entrada</span>
            <span className="text-xl font-bold text-dark-50">{formatDate(item.data_aquisicao)}</span>
          </div>
        </div>
        <div className="space-y-4 p-5 bg-dark-800/50 rounded-2xl border border-dark-700">
           <h4 className="text-[10px] font-black text-primary-500 uppercase tracking-widest">Especificações Técnicas</h4>
           <div className="grid grid-cols-2 gap-y-3 gap-x-6 text-sm">
              <p className="flex justify-between border-b border-dark-700/50 pb-1"><strong>Categoria:</strong> <span className="text-dark-300">{item.categoria}</span></p>
              <p className="flex justify-between border-b border-dark-700/50 pb-1"><strong>Localização:</strong> <span className="text-dark-300">{item.cidade}/{item.uf}</span></p>
              {item.dados_categoria && Object.entries(item.dados_categoria).map(([k, v]) => (
                <p key={k} className="flex justify-between border-b border-dark-700/50 pb-1 uppercase text-[11px]"><strong className="text-dark-400">{k}:</strong> <span className="font-bold text-blue-400">{v}</span></p>
              ))}
           </div>
        </div>
      </div>
    </Modal>
  )
}