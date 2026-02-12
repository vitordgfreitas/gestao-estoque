import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Search, Edit, Trash2, Eye, Package, Calendar, Car, DollarSign, MapPin, Hash, Coins, ClipboardList, PenTool, Settings } from 'lucide-react'
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

  // Estados de Controle de Modais
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
      toast.error('Erro de sincronização com o banco de dados')
    } finally {
      setLoading(false)
    }
  }

  // --- LÓGICA DE NEGÓCIO (KPIs BASEADOS NO SEU SCHEMA) ---
  const stats = useMemo(() => {
    // Patrimônio = Itens.valor_compra * Itens.quantidade_total
    const patrimonio = itens.reduce((acc, i) => acc + (Number(i.valor_compra) * i.quantidade_total || 0), 0)
    // Receita = Compromissos.valor_total_contrato
    const receitaTotal = compromissos.reduce((acc, c) => acc + (Number(c.valor_total_contrato) || 0), 0)
    const emManutencao = pecasCarros.length
    return { patrimonio, receitaTotal, emManutencao }
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

  // --- HANDLERS DE PERSISTÊNCIA ---
  const handleDeleteItem = async () => {
    try {
      await itensAPI.deletar(deletingItem.id)
      toast.success('Ativo removido com sucesso')
      loadData(); setDeletingItem(null)
    } catch (e) { toast.error('Erro ao excluir item') }
  }

  const handleDeleteCompromisso = async () => {
    try {
      await compromissosAPI.deletar(deletingCompromisso.id)
      toast.success('Contrato e itens vinculados excluídos')
      loadData(); setDeletingCompromisso(null)
    } catch (e) { toast.error('Erro ao excluir contrato') }
  }

  const handleSaveItem = async (data) => {
    try {
      await itensAPI.atualizar(editingItem.id, data)
      toast.success('Ativo e JSONB de categoria salvos!')
      loadData(); setEditingItem(null)
    } catch (e) { toast.error('Erro ao salvar item') }
  }

  const handleSaveCompromisso = async (data) => {
    try {
      await compromissosAPI.atualizar(editingCompromisso.id, data)
      toast.success('Faturamento e cabeçalho atualizados!')
      loadData(); setEditingCompromisso(null)
    } catch (e) { toast.error('Erro ao salvar contrato') }
  }

  const handleSavePecaCarro = async (data) => {
    try {
      await api.put(`/api/pecas-carros/${editingPecaCarro.id}`, data)
      toast.success('Registro de manutenção atualizado!')
      loadData(); setEditingPecaCarro(null)
    } catch (e) { toast.error('Erro ao salvar manutenção') }
  }

  if (loading) return <div className="flex h-96 items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto px-4 pb-10">
      {/* HEADER & KPIs REALISTAS */}
      <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase">Visualizar Dados</h1>
          <p className="text-dark-400 font-medium tracking-widest">Brasília, DF • Operação Estrela</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <StatBox label="Patrimônio Total" value={stats.patrimonio} isCurrency />
          <StatBox label="Receita Bruta" value={stats.receitaTotal} isCurrency color="text-green-400" />
          <StatBox label="Em Manutenção" value={stats.emManutencao} color="text-blue-400" />
        </div>
      </div>

      {/* SEARCH BAR */}
      <div className="relative group">
        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-dark-500 group-focus-within:text-primary-400" size={24} />
        <input 
          type="text" 
          placeholder="Pesquisar por item, cliente, placa, chassi ou contrato..." 
          value={searchTerm} 
          onChange={e => setSearchTerm(e.target.value)} 
          className="input w-full pl-14 h-16 text-xl border-dark-700 bg-dark-800/40 rounded-2xl focus:ring-2 focus:ring-primary-500/50" 
        />
      </div>

      {/* TABS NAVEGAÇÃO */}
      <div className="flex gap-2 p-1.5 bg-dark-800 rounded-2xl border border-dark-700 w-fit">
        <TabItem active={activeTab === 'itens'} label="Inventário" count={itens.length} icon={<Package size={18}/>} onClick={() => setActiveTab('itens')} />
        <TabItem active={activeTab === 'compromissos'} label="Contratos" count={compromissos.length} icon={<DollarSign size={18}/>} onClick={() => setActiveTab('compromissos')} />
        <TabItem active={activeTab === 'pecas-carros'} label="Manutenção" count={pecasCarros.length} icon={<Car size={18}/>} onClick={() => setActiveTab('pecas-carros')} />
      </div>

      {/* ÁREA DE DADOS - LARGURAS TRAVADAS NO GRID */}
      <div className="card overflow-hidden p-0 border-dark-700 bg-dark-900/40 backdrop-blur-lg shadow-2xl">
        <div className="overflow-x-auto">
          
          {/* ABA INVENTÁRIO (Patrimônio Total + Data Aquisição) */}
          {activeTab === 'itens' && (
            <table className="w-full text-left border-collapse min-w-[1200px]">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[25%]">Ativo / Especificações</th>
                  <th className="px-6 py-4 w-[10%] text-center">Estoque</th>
                  <th className="px-6 py-4 w-[12%]">Custo Unit.</th>
                  <th className="px-6 py-4 w-[15%]">Patrimônio Total</th>
                  <th className="px-6 py-4 w-[13%]">Data Aquisição</th>
                  <th className="px-6 py-4 w-[15%] hidden lg:table-cell">Localização</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.itens.map(item => (
                  <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="font-bold text-dark-50 text-base">{item.nome}</div>
                      <div className="flex gap-2 mt-1.5">
                        <span className="text-[10px] bg-primary-500/10 text-primary-400 px-2 py-0.5 rounded font-black border border-primary-500/20 uppercase tracking-tighter">{item.categoria}</span>
                        {item.dados_categoria?.Placa && <span className="text-[10px] bg-dark-700 px-2 py-0.5 rounded font-mono text-dark-400 border border-dark-600 uppercase">PLACA: {item.dados_categoria.Placa}</span>}
                      </div>
                    </td>
                    <td className="px-6 py-5 font-mono text-lg font-bold text-center">{item.quantidade_total}</td>
                    <td className="px-6 py-5 text-dark-300 font-mono">R$ {Number(item.valor_compra).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="px-6 py-5 text-green-400 font-black font-mono text-lg">R$ {(item.valor_compra * item.quantidade_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="px-6 py-5 text-xs text-dark-300 font-medium font-mono">{formatDate(item.data_aquisicao)}</td>
                    <td className="px-6 py-5 text-xs text-dark-400 hidden lg:table-cell font-bold"><MapPin size={12} className="inline mr-1 text-primary-500"/> {item.cidade}/{item.uf}</td>
                    <td className="px-6 py-5 text-right flex gap-1 justify-end opacity-20 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => setViewingItem(item)} title="Ver Ficha" className="p-2 hover:bg-dark-700 rounded-lg"><Eye size={18}/></button>
                      <button onClick={() => setEditingItem(item)} title="Editar Ativo" className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><Edit size={18}/></button>
                      <button onClick={() => setDeletingItem(item)} title="Excluir" className="p-2 hover:bg-dark-700 rounded-lg text-red-400"><Trash2 size={18}/></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* ABA CONTRATOS (Equipamentos e Faturamento) */}
          {activeTab === 'compromissos' && (
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr>
                  <th className="px-6 py-4 w-[25%]">Contrato / Cliente</th>
                  <th className="px-6 py-4 w-[35%] text-center">Equipamentos no Contrato</th>
                  <th className="px-6 py-4 w-[15%]">Vigência</th>
                  <th className="px-6 py-4 w-[15%]">Faturamento</th>
                  <th className="px-6 py-4 w-[10%] text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {filteredData.compromissos.map(c => (
                  <tr key={c.id} className="hover:bg-green-500/[0.02] transition-colors group">
                    <td className="px-6 py-5">
                      <div className="font-black text-dark-50 text-base uppercase tracking-tight">{c.nome_contrato || `Contrato #${c.id}`}</div>
                      <div className="text-[10px] text-dark-400 font-bold uppercase mt-1 tracking-tighter">{c.contratante}</div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-wrap justify-center gap-1.5">
                        {/* MAPEAMENTO SEGUINDO SEU SCHEMA: compromisso_itens -> itens */}
                        {c.compromisso_itens?.map((ci, idx) => (
                          <span key={idx} className="px-2.5 py-1 bg-primary-500/10 text-primary-400 rounded-lg text-[10px] font-black border border-primary-500/20">
                            {ci.quantidade}x {ci.itens?.nome || 'Item'}
                          </span>
                        )) || <span className="text-dark-600 text-[10px] italic">Nenhum equipamento vinculado</span>}
                      </div>
                    </td>
                    <td className="px-6 py-5 text-[11px] font-medium">
                       <div className="text-dark-100 font-bold">{formatDate(c.data_inicio)}</div>
                       <div className="text-dark-500 mt-1 italic uppercase font-bold">até {formatDate(c.data_fim)}</div>
                    </td>
                    <td className="px-6 py-5 text-green-400 font-black text-lg font-mono">
                      R$ {(Number(c.valor_total_contrato) || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                    </td>
                    <td className="px-6 py-5 text-right flex gap-2 justify-end opacity-20 group-hover:opacity-100 transition-opacity">
                       <button onClick={() => setEditingCompromisso(c)} className="p-2 text-primary-400 hover:bg-dark-700 rounded-lg transition-colors"><Edit size={18}/></button>
                       <button onClick={() => setDeletingCompromisso(c)} className="p-2 text-red-400 hover:bg-dark-700 rounded-lg transition-colors"><Trash2 size={18}/></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* ABA MANUTENÇÃO (Pecas_Carros) */}
          {activeTab === 'pecas-carros' && (
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="bg-dark-800/50 text-dark-400 text-[11px] uppercase font-black tracking-widest">
                <tr><th className="px-6 py-4 w-[30%]">Veículo Alvo</th><th className="px-6 py-4 w-[30%]">Peça Aplicada</th><th className="px-6 py-4 w-[10%] text-center">Qtd</th><th className="px-6 py-4 w-[20%]">Data Instalação</th><th className="px-6 py-4 w-[10%] text-right">Ações</th></tr>
              </thead>
              <tbody className="divide-y divide-dark-800">
                {pecasCarros.map(pc => {
                  const veiculo = itens.find(i => i.id === pc.carro_id);
                  const peca = itens.find(i => i.id === pc.peca_id);
                  return (
                    <tr key={pc.id} className="hover:bg-blue-500/[0.02] transition-colors group">
                      <td className="px-6 py-5">
                        <div className="font-bold text-dark-50">{veiculo?.nome}</div>
                        <div className="text-[10px] bg-blue-500/20 text-blue-400 px-2 rounded font-black mt-1 inline-block uppercase tracking-tighter">
                          {veiculo?.dados_categoria?.Placa || 'SEM PLACA'}
                        </div>
                      </td>
                      <td className="px-6 py-5 font-bold text-primary-400 uppercase text-sm">{peca?.nome}</td>
                      <td className="px-6 py-5 font-black text-lg text-blue-400 text-center">{pc.quantidade}</td>
                      <td className="px-6 py-5 text-xs text-dark-400 font-mono font-bold tracking-widest">{formatDate(pc.data_instalacao)}</td>
                      <td className="px-6 py-5 text-right"><button onClick={() => setEditingPecaCarro(pc)} className="p-2 hover:bg-dark-700 rounded-lg"><Edit size={18}/></button></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* --- MODAIS DE SUPORTE (O CORAÇÃO DO SCRIPT) --- */}

      {/* Ficha do Ativo (Eye) */}
      {viewingItem && <ViewItemModal item={viewingItem} onClose={() => setViewingItem(null)} />}

      {/* Editar Ativo (Inventário) */}
      {editingItem && (
        <EditItemModal 
          item={editingItem} 
          categorias={categorias} 
          onClose={() => setEditingItem(null)} 
          onSave={handleSaveItem} 
        />
      )}

      {/* Editar Contrato Master */}
      {editingCompromisso && (
        <EditCompromissoModal 
          compromisso={editingCompromisso} 
          onClose={() => setEditingCompromisso(null)} 
          onSave={handleSaveCompromisso} 
        />
      )}

      {/* Editar Manutenção */}
      {editingPecaCarro && (
        <EditPecaCarroModal 
          pecaCarro={editingPecaCarro} 
          itens={itens} 
          onClose={() => setEditingPecaCarro(null)} 
          onSave={handleSavePecaCarro} 
        />
      )}

      <ConfirmDialog isOpen={!!deletingItem} onClose={() => setDeletingItem(null)} onConfirm={handleDeleteItem} title="Excluir Ativo permanentemente?" />
      <ConfirmDialog isOpen={!!deletingCompromisso} onClose={() => setDeletingCompromisso(null)} onConfirm={handleDeleteCompromisso} title="Excluir Contrato e Faturamento?" />
    </div>
  )
}

// --- COMPONENTES AUXILIARES DE UI ---

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

function TabItem({ active, label, count, icon, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2.5 px-6 py-3.5 rounded-xl font-black text-sm transition-all ${active ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-400 hover:text-dark-100'}`}>
      {icon} {label} <span className="text-[10px] bg-dark-700/50 px-2 py-0.5 rounded-full font-bold">{count}</span>
    </button>
  )
}

// --- COMPONENTES DE MODAL (LOGICA DE NEGOCIO E JSONB) ---

function EditItemModal({ item, categorias, onClose, onSave }) {
  const [formData, setFormData] = useState({
    nome: item.nome || '',
    quantidade_total: item.quantidade_total || 1,
    categoria: item.categoria || '',
    valor_compra: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(item.valor_compra || 0),
    data_aquisicao: item.data_aquisicao?.split('T')[0] || '',
    ...item.dados_categoria // Carrega campos do JSONB como Placa, Marca, etc.
  })
  
  const [camposExtras, setCamposExtras] = useState([])
  useEffect(() => {
    if (formData.categoria) categoriasAPI.obterCampos(formData.categoria).then(res => setCamposExtras(res.data || []))
  }, [formData.categoria])

  const handleMoeda = (v) => {
    const n = v.replace(/\D/g, "");
    return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(n / 100);
  }

  return (
    <Modal isOpen={true} onClose={onClose} title={`Editar ${formData.categoria}: ${item.nome}`}>
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
        <div className="space-y-4">
          <div className="text-[10px] font-black text-primary-500 uppercase tracking-widest border-b border-dark-700 pb-1">Patrimônio Geral</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2"><label className="label text-xs uppercase font-bold">Nome do Ativo</label><input className="input" value={formData.nome} onChange={e => setFormData({...formData, nome: e.target.value})} /></div>
            <div><label className="label text-xs uppercase font-bold">Qtd no Estoque</label><input type="number" className="input" value={formData.quantidade_total} onChange={e => setFormData({...formData, quantidade_total: e.target.value})} /></div>
            <div><label className="label text-xs uppercase font-bold text-green-500">Valor Unitário</label><input className="input text-green-400 font-bold" value={formData.valor_compra} onChange={e => setFormData({...formData, valor_compra: handleMoeda(e.target.value)})} /></div>
            <div className="md:col-span-2"><label className="label text-xs uppercase font-bold">Data de Entrada</label><input type="date" className="input" value={formData.data_aquisicao} onChange={e => setFormData({...formData, data_aquisicao: e.target.value})} /></div>
          </div>
        </div>

        {camposExtras.length > 0 && (
          <div className="space-y-4 p-5 bg-dark-800 rounded-2xl border border-dark-700 grid grid-cols-2 gap-4 shadow-inner">
             <div className="col-span-2 text-[10px] font-black text-blue-400 uppercase tracking-widest border-b border-blue-500/20 pb-1">Atributos de {formData.categoria} (JSONB)</div>
             {camposExtras.map(c => (
               <div key={c}><label className="label capitalize text-[10px] font-bold">{c}</label><input className="input bg-dark-900 border-blue-500/20" value={formData[c] || ''} onChange={e => setFormData({...formData, [c]: e.target.value})} /></div>
             ))}
          </div>
        )}
        <button type="submit" className="btn btn-primary w-full py-4 font-black uppercase text-lg shadow-xl">SALVAR ALTERAÇÕES</button>
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
    data_fim: compromisso.data_fim?.split('T')[0] || ''
  })
  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Contrato Master">
      <form onSubmit={(e) => {
        e.preventDefault()
        onSave({ ...formData, valor_total_contrato: parseFloat(formData.valor_total_contrato.replace(/\./g, '').replace(',', '.')) || 0 })
      }} className="space-y-4">
        <div><label className="label">Nome do Evento / Contrato</label><input className="input font-bold" value={formData.nome_contrato} onChange={e => setFormData({...formData, nome_contrato: e.target.value})} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label text-green-500 font-bold uppercase text-[10px]">Faturamento Bruto</label><input className="input text-green-400 font-black" value={formData.valor_total_contrato} onChange={e => setFormData({...formData, valor_total_contrato: e.target.value})} /></div>
          <div><label className="label uppercase text-[10px]">Cliente</label><input className="input" value={formData.contratante} onChange={e => setFormData({...formData, contratante: e.target.value})} /></div>
        </div>
        <button type="submit" className="btn btn-primary w-full py-4 font-black">SALVAR</button>
      </form>
    </Modal>
  )
}

function EditPecaCarroModal({ pecaCarro, itens, onClose, onSave }) {
  const v = itens.find(i => i.id === pecaCarro.carro_id);
  const p = itens.find(i => i.id === pecaCarro.peca_id);
  const [formData, setFormData] = useState({ quantidade: pecaCarro.quantidade, data_instalacao: pecaCarro.data_instalacao?.split('T')[0] })
  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Manutenção">
      <div className="mb-4 p-4 bg-dark-800 rounded-2xl border border-dark-700 text-xs shadow-inner">
        <p className="flex justify-between uppercase"><strong>Veículo Alvo:</strong> <span>{v?.nome}</span></p>
        <p className="flex justify-between mt-1 text-blue-400 font-black uppercase"><strong>Peça Instalada:</strong> <span>{p?.nome}</span></p>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); onSave(formData); }} className="space-y-4">
        <div><label className="label uppercase text-[10px]">Quantidade Aplicada</label><input type="number" className="input" value={formData.quantidade} onChange={e => setFormData({...formData, quantidade: e.target.value})} /></div>
        <div><label className="label uppercase text-[10px]">Data da Instalação</label><input type="date" className="input" value={formData.data_instalacao} onChange={e => setFormData({...formData, data_instalacao: e.target.value})} /></div>
        <button type="submit" className="btn btn-primary w-full py-3 font-bold uppercase">SALVAR REGISTRO</button>
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
            <span className="text-[10px] font-black text-dark-500 block mb-1 uppercase tracking-widest">Patrimônio Líquido do Item</span>
            <span className="text-xl font-black text-green-400 font-mono">R$ {(item.valor_compra * item.quantidade_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
          </div>
          <div className="p-5 bg-dark-800 rounded-3xl border border-dark-700 text-center shadow-xl">
            <span className="text-[10px] font-black text-dark-500 block mb-1 uppercase tracking-widest">Aquisição em</span>
            <span className="text-xl font-bold text-dark-50 font-mono">{formatDate(item.data_aquisicao)}</span>
          </div>
        </div>
        {item.dados_categoria && (
          <div className="p-6 bg-dark-800/50 rounded-3xl border border-dark-700 shadow-2xl">
            <h4 className="text-[10px] font-black text-primary-500 uppercase tracking-widest mb-4 border-b border-dark-700 pb-2">Atributos Técnicos (JSONB)</h4>
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