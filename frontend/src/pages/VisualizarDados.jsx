import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { itensAPI, compromissosAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Search, Edit, Trash2, Eye, Package, Calendar, Car, DollarSign, MapPin, Hash, ClipboardCheck } from 'lucide-react'
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
      toast.error('Erro ao sincronizar dados com o servidor')
    } finally {
      setLoading(false)
    }
  }

  // --- LÓGICA DE NEGÓCIO E FILTROS ---
  const stats = useMemo(() => {
    const patrimonio = itens.reduce((acc, i) => acc + (i.valor_compra * i.quantidade_total || 0), 0)
    const receitaTotal = compromissos.reduce((acc, c) => acc + (c.valor_total_contrato || 0), 0)
    const emUsoInterno = pecasCarros.length
    return { patrimonio, receitaTotal, emUsoInterno }
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

  // --- HANDLERS ---
  const handleDeleteItem = async () => {
    try {
      await itensAPI.deletar(deletingItem.id)
      toast.success('Ativo removido')
      setItens(prev => prev.filter(i => i.id !== deletingItem.id))
      setDeletingItem(null)
    } catch (e) { toast.error('Erro ao excluir') }
  }

  const handleDeleteCompromisso = async () => {
    try {
      await compromissosAPI.deletar(deletingCompromisso.id)
      toast.success('Contrato encerrado e estoque liberado')
      setCompromissos(prev => prev.filter(c => c.id !== deletingCompromisso.id))
      setDeletingCompromisso(null)
    } catch (e) { toast.error('Erro ao excluir contrato') }
  }

  const handleSaveItem = async (data) => {
    await itensAPI.atualizar(editingItem.id, data)
    toast.success('Item atualizado')
    loadData()
    setEditingItem(null)
  }

  const handleSaveCompromisso = async (data) => {
    await compromissosAPI.atualizar(editingCompromisso.id, data)
    toast.success('Contrato atualizado')
    loadData()
    setEditingCompromisso(null)
  }

  if (loading) return <div className="flex h-96 items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6">
      {/* HEADER DE KPIs */}
      <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tight">Gestão de Ativos</h1>
          <p className="text-dark-400 font-medium">Operação Integrada • Brasília, DF</p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <StatCard label="Patrimônio" value={stats.patrimonio} isCurrency />
          <StatCard label="Receita Contratos" value={stats.receitaTotal} isCurrency color="text-green-400" />
          <StatCard label="Instalados" value={stats.emUsoInterno} color="text-blue-400" />
        </div>
      </div>

      {/* BARRA DE BUSCA GLOBAL */}
      <div className="relative group">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-dark-500 group-focus-within:text-primary-400 transition-colors" size={22} />
        <input 
          type="text" 
          placeholder="Pesquisar em tudo (itens, clientes, placas, contratos...)" 
          value={searchTerm} 
          onChange={e => setSearchTerm(e.target.value)} 
          className="input w-full pl-12 h-16 text-lg border-dark-700 bg-dark-800/40 backdrop-blur-sm focus:ring-2 focus:ring-primary-500/50" 
        />
      </div>

      {/* NAVEGAÇÃO POR ABAS */}
      <div className="flex gap-1 rounded-2xl bg-dark-800 p-1.5 border border-dark-700 shadow-inner">
        <TabButton active={activeTab === 'itens'} label="Inventário" count={itens.length} icon={<Package size={18}/>} onClick={() => setActiveTab('itens')} />
        <TabButton active={activeTab === 'compromissos'} label="Contratos" count={compromissos.length} icon={<DollarSign size={18}/>} onClick={() => setActiveTab('compromissos')} />
        <TabButton active={activeTab === 'pecas-carros'} label="Manutenção" count={pecasCarros.length} icon={<Car size={18}/>} onClick={() => setActiveTab('pecas-carros')} />
      </div>

      {/* TABELAS DINÂMICAS */}
      <motion.div layout className="card overflow-hidden p-0 border-dark-700 bg-dark-900/40 shadow-2xl">
        <div className="overflow-x-auto">
          
          {/* ABA ITENS */}
          {activeTab === 'itens' && (
            <table className="table-modern">
              <thead>
                <tr><th>Ativo / Categoria</th><th>Qtd Total</th><th>Custo Aquisição</th><th>Localização</th><th className="text-right">Ações</th></tr>
              </thead>
              <tbody>
                {filteredData.itens.map(item => (
                  <tr key={item.id} className="group hover:bg-white/[0.02]">
                    <td>
                      <div className="font-bold text-dark-50 text-base">{formatItemName(item)}</div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] bg-dark-700 px-1.5 py-0.5 rounded font-black text-dark-400 uppercase tracking-widest">{item.categoria}</span>
                        <span className="text-[10px] text-dark-500 font-mono">#{item.id}</span>
                      </div>
                    </td>
                    <td>
                       <div className="font-mono text-lg font-bold">{item.quantidade_total}</div>
                       <div className="text-[10px] text-green-500 font-bold uppercase tracking-tighter">Unidades em Estoque</div>
                    </td>
                    <td className="font-mono text-dark-300">R$ {item.valor_compra?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="text-xs text-dark-400 font-medium"><MapPin size={12} className="inline mr-1 text-primary-500"/> {item.cidade}/{item.uf}</td>
                    <td className="text-right">
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

          {/* ABA CONTRATOS (MASTER) */}
          {activeTab === 'compromissos' && (
            <table className="table-modern">
              <thead>
                <tr><th>Contrato / Cliente</th><th>Equipamentos Alugados</th><th>Vigência</th><th>Faturamento</th><th className="text-right">Ações</th></tr>
              </thead>
              <tbody>
                {filteredData.compromissos.map(c => (
                  <tr key={c.id} className="group hover:bg-green-500/[0.02]">
                    <td>
                      <div className="font-black text-dark-50 text-base uppercase tracking-tight">{c.nome_contrato}</div>
                      <div className="text-[10px] text-dark-400 font-bold">{c.contratante}</div>
                    </td>
                    <td className="max-w-[280px]">
                      <div className="flex flex-wrap gap-1.5">
                        {c.compromisso_itens?.map((ci, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-primary-500/10 text-primary-400 rounded-md text-[10px] font-black border border-primary-500/20">
                            {ci.quantidade}x {ci.itens?.nome}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="text-[11px] leading-tight font-medium">
                      <div className="text-dark-200">{formatDate(c.data_inicio)}</div>
                      <div className="text-dark-500 mt-0.5 italic">até {formatDate(c.data_fim)}</div>
                    </td>
                    <td className="text-green-400 font-black text-lg">R$ {c.valor_total_contrato?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                    <td className="text-right">
                      <div className="flex justify-end gap-1">
                        <ActionButton icon={<Edit size={18}/>} onClick={() => setEditingCompromisso(c)} hoverColor="hover:text-primary-400" />
                        <ActionButton icon={<Trash2 size={18}/>} onClick={() => setDeletingCompromisso(c)} hoverColor="hover:text-red-400" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* ABA MANUTENÇÃO */}
          {activeTab === 'pecas-carros' && (
            <table className="table-modern">
              <thead>
                <tr><th>Veículo / Placa</th><th>Peça Aplicada</th><th>Qtd</th><th>Data Instalação</th><th className="text-right">Ações</th></tr>
              </thead>
              <tbody>
                {filteredData.pecas.map(pc => {
                  const veiculo = itens.find(i => i.id === pc.carro_id)
                  const peca = itens.find(i => i.id === pc.peca_id)
                  return (
                    <tr key={pc.id} className="group hover:bg-blue-500/[0.02]">
                      <td>
                        <div className="font-bold text-dark-50">{veiculo?.nome}</div>
                        <div className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded inline-block font-black mt-1">
                          {veiculo?.dados_categoria?.Placa || 'PEÇA AVULSA'}
                        </div>
                      </td>
                      <td>
                        <div className="font-bold text-dark-100">{peca?.nome}</div>
                        <div className="text-[10px] text-dark-500 uppercase font-bold">{peca?.categoria}</div>
                      </td>
                      <td className="font-black text-blue-400 text-lg">{pc.quantidade}</td>
                      <td className="text-xs text-dark-400 font-mono">{formatDate(pc.data_instalacao)}</td>
                      <td className="text-right">
                        <ActionButton icon={<Edit size={18}/>} onClick={() => setEditingPecaCarro(pc)} hoverColor="hover:text-blue-400" />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </motion.div>

      {/* --- MODAIS --- */}
      {viewingItem && (
        <Modal isOpen={true} onClose={() => setViewingItem(null)} title="Ficha do Ativo">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700">
                <label className="text-[10px] font-black text-green-500 uppercase tracking-widest block mb-1">Custo Aquisição</label>
                <span className="text-2xl font-black text-dark-50">R$ {viewingItem.valor_compra?.toLocaleString('pt-BR')}</span>
              </div>
              <div className="p-4 bg-dark-800 rounded-2xl border border-dark-700">
                <label className="text-[10px] font-black text-dark-400 uppercase tracking-widest block mb-1">Entrada no Estoque</label>
                <span className="text-xl font-bold text-dark-100">{formatDate(viewingItem.data_aquisicao)}</span>
              </div>
            </div>
            <div className="space-y-3 p-5 bg-dark-800/50 rounded-2xl border border-dark-700">
               <p className="flex justify-between border-b border-dark-700 pb-2"><strong>Categoria:</strong> <span className="text-primary-400 font-black uppercase text-xs">{viewingItem.categoria}</span></p>
               <p className="flex justify-between border-b border-dark-700 pb-2"><strong>Base Local:</strong> <span className="font-bold">{viewingItem.cidade} - {viewingItem.uf}</span></p>
               {viewingItem.descricao && <p className="text-dark-400 text-sm italic pt-2">"{viewingItem.descricao}"</p>}
            </div>
          </div>
        </Modal>
      )}

      {/* EDIÇÃO DE ITEM */}
      {editingItem && (
        <EditItemModal 
          item={editingItem} 
          categorias={categorias} 
          onClose={() => setEditingItem(null)} 
          onSave={handleSaveItem} 
        />
      )}

      {/* EDIÇÃO DE CONTRATO MASTER */}
      {editingCompromisso && (
        <EditCompromissoModal 
          compromisso={editingCompromisso} 
          onClose={() => setEditingCompromisso(null)} 
          onSave={handleSaveCompromisso} 
        />
      )}

      {/* DIÁLOGOS DE CONFIRMAÇÃO */}
      <ConfirmDialog 
        isOpen={!!deletingItem} 
        onClose={() => setDeletingItem(null)} 
        onConfirm={handleDeleteItem} 
        title="Remover Ativo?" 
        message="Esta ação é permanente e removerá o item de todos os cálculos de patrimônio." 
      />
      <ConfirmDialog 
        isOpen={!!deletingCompromisso} 
        onClose={() => setDeletingCompromisso(null)} 
        onConfirm={handleDeleteCompromisso} 
        title="Encerrar Contrato?" 
        message="O faturamento será mantido no histórico, mas os itens serão liberados no estoque imediatamente." 
      />
    </div>
  )
}

// --- COMPONENTES AUXILIARES (HELPER UI) ---

function StatCard({ label, value, isCurrency, color = "text-dark-50" }) {
  return (
    <div className="bg-dark-800/80 backdrop-blur-md border border-dark-700 px-6 py-4 rounded-3xl min-w-[160px] shadow-lg">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-dark-500 mb-1.5">{label}</p>
      <p className={`text-2xl font-black ${color}`}>
        {isCurrency ? `R$ ${value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}` : value}
      </p>
    </div>
  )
}

function TabButton({ active, label, count, icon, onClick }) {
  return (
    <button 
      onClick={onClick} 
      className={`flex-1 flex items-center justify-center gap-2.5 py-3.5 rounded-xl font-black text-sm transition-all duration-300 ${active ? 'bg-primary-500 text-white shadow-xl shadow-primary-500/30 scale-[1.02]' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700/50'}`}
    >
      {icon} {label} 
      <span className={`text-[10px] px-2 py-0.5 rounded-full ${active ? 'bg-white/20 text-white' : 'bg-dark-700 text-dark-400'}`}>
        {count}
      </span>
    </button>
  )
}

function ActionButton({ icon, onClick, hoverColor = "hover:text-white" }) {
  return (
    <button 
      onClick={onClick} 
      className={`p-2.5 text-dark-500 transition-all rounded-lg hover:bg-dark-700 ${hoverColor} active:scale-90`}
    >
      {icon}
    </button>
  )
}

// --- SUB-MODAL DE EDIÇÃO DE CONTRATO (AJUSTADO PARA MASTER) ---
function EditCompromissoModal({ compromisso, onClose, onSave }) {
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

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Contrato Master">
      <form onSubmit={(e) => {
        e.preventDefault();
        onSave({
          ...formData,
          valor_total_contrato: parseFloat(formData.valor_total_contrato.replace(/\./g, '').replace(',', '.')) || 0
        });
      }} className="space-y-4 max-h-[80vh] overflow-y-auto pr-2">
        <div className="space-y-1">
          <label className="text-[10px] font-bold text-dark-400 uppercase ml-1">Nome do Contrato / Evento</label>
          <input className="input font-bold text-lg" value={formData.nome_contrato} onChange={e => setFormData({...formData, nome_contrato: e.target.value})} required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-[10px] font-bold text-green-500 uppercase ml-1">Faturamento Bruto</label>
            <input className="input font-black text-green-400" value={formData.valor_total_contrato} onChange={e => setFormData({...formData, valor_total_contrato: handleCurrency(e.target.value)})} />
          </div>
          <div>
            <label className="text-[10px] font-bold text-dark-400 uppercase ml-1">Cliente / Contratante</label>
            <input className="input" value={formData.contratante} onChange={e => setFormData({...formData, contratante: e.target.value})} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Início</label><input type="date" className="input" value={formData.data_inicio} onChange={e => setFormData({...formData, data_inicio: e.target.value})} /></div>
          <div><label className="label">Término</label><input type="date" className="input" value={formData.data_fim} onChange={e => setFormData({...formData, data_fim: e.target.value})} /></div>
        </div>
        <button type="submit" className="btn btn-primary w-full py-4 font-black text-lg mt-4 shadow-xl shadow-primary-500/20">SALVAR ALTERAÇÕES</button>
      </form>
    </Modal>
  )
}

// --- SUB-MODAL DE EDIÇÃO DE ITEM ---
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
  })

  return (
    <Modal isOpen={true} onClose={onClose} title="Editar Ativo">
      <form onSubmit={(e) => {
        e.preventDefault();
        onSave({
          ...formData,
          valor_compra: parseFloat(formData.valor_compra.replace(/\./g, '').replace(',', '.')) || 0
        });
      }} className="space-y-4">
        <div><label className="label">Nome do Ativo</label><input className="input" value={formData.nome} onChange={e => setFormData({...formData, nome: e.target.value})} required /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label text-green-500">Valor de Aquisição</label><input className="input" value={formData.valor_compra} onChange={e => setFormData({...formData, valor_compra: new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(e.target.value.replace(/\D/g, '') / 100)})} /></div>
          <div><label className="label">Estoque Total</label><input type="number" className="input" value={formData.quantidade_total} onChange={e => setFormData({...formData, quantidade_total: e.target.value})} /></div>
        </div>
        <button type="submit" className="btn btn-primary w-full py-3 font-bold">ATUALIZAR DADOS</button>
      </form>
    </Modal>
  )
}