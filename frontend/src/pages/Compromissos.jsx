import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI, disponibilidadeAPI } from '../services/api'
import api from '../services/api'
import { Calendar, Plus, Info, X, Trash2, Package, Car, ClipboardList, User, MapPin, DollarSign } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatItemName } from '../utils/format'
import { getCidadesPorUF, ESTADOS } from '../utils/municipios'

const UFS = ESTADOS.map(e => e.sigla)

export default function Compromissos() {
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [cidadesDisponiveis, setCidadesDisponiveis] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingItens, setLoadingItens] = useState(true)

  // Dados do Cabeçalho
  const [formData, setFormData] = useState({
    tipo_compromisso: 'itens_alugados',
    nome_contrato: '', // Novo campo para o Master Contract
    contratante: '',
    data_inicio: new Date().toISOString().split('T')[0],
    data_fim: new Date().toISOString().split('T')[0],
    valor_total_contrato: '', // Novo campo para ROI
    descricao: '',
    cidade: '',
    uf: 'DF',
    endereco: '',
    carro_id: '', // Usado no modo Peças de Carro
  })

  // Carrinho de Itens (Para Aluguel)
  const [itensContrato, setItensContrato] = useState([]) // [{item_id, nome, quantidade}]
  const [selecaoAluguel, setSelecaoAluguel] = useState({ id: '', qtd: 1 })

  // Carrinho de Peças (Para Manutenção de Carro)
  const [pecasSelecionadas, setPecasSelecionadas] = useState([]) // [{peca_id, nome, quantidade}]
  const [selecaoPeca, setSelecaoPeca] = useState({ id: '', qtd: 1 })

  useEffect(() => {
    loadCategorias()
    loadItens()
  }, [])

  useEffect(() => {
    if (formData.uf) setCidadesDisponiveis(getCidadesPorUF(formData.uf))
  }, [formData.uf])

  const loadCategorias = async () => {
    try {
      const response = await categoriasAPI.listar()
      setCategorias(response.data || [])
    } catch (error) { console.error(error) }
  }

  const loadItens = async () => {
    try {
      setLoadingItens(true)
      const response = await itensAPI.listar()
      setItens(response.data || [])
    } catch (error) { toast.error('Erro ao carregar itens') }
    finally { setLoadingItens(false) }
  }

  // --- LÓGICA DO "CARRINHO" DE ALUGUEL ---
  const adicionarAoContrato = () => {
    if (!selecaoAluguel.id) return toast.error("Selecione um item")
    const itemInfo = itens.find(i => i.id === parseInt(selecaoAluguel.id))
    
    const existente = itensContrato.find(i => i.item_id === itemInfo.id)
    if (existente) {
      setItensContrato(itensContrato.map(i => i.item_id === itemInfo.id 
        ? { ...i, quantidade: i.quantidade + parseInt(selecaoAluguel.qtd) } : i))
    } else {
      setItensContrato([...itensContrato, { 
        item_id: itemInfo.id, 
        nome: formatItemName(itemInfo), 
        quantidade: parseInt(selecaoAluguel.qtd) 
      }])
    }
    setSelecaoAluguel({ id: '', qtd: 1 })
    toast.success("Item adicionado ao contrato")
  }

  // --- LÓGICA DO "CARRINHO" DE PEÇAS ---
  const adicionarPecaLista = () => {
    if (!selecaoPeca.id) return toast.error("Selecione uma peça")
    const pecaInfo = itens.find(i => i.id === parseInt(selecaoPeca.id))
    
    setPecasSelecionadas([...pecasSelecionadas, {
      peca_id: pecaInfo.id,
      nome: pecaInfo.nome,
      quantidade: parseInt(selecaoPeca.qtd)
    }])
    setSelecaoPeca({ id: '', qtd: 1 })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (formData.tipo_compromisso === 'pecas_carro') {
        if (!formData.carro_id || pecasSelecionadas.length === 0) {
          throw new Error("Selecione o carro e pelo menos uma peça")
        }
        const promises = pecasSelecionadas.map(p =>
          api.post('/api/pecas-carros', {
            peca_id: p.peca_id,
            carro_id: parseInt(formData.carro_id),
            quantidade: p.quantidade,
            data_instalacao: formData.data_inicio,
            observacoes: formData.descricao
          })
        )
        await Promise.all(promises)
        toast.success('Peças vinculadas ao veículo com sucesso!')
      } else {
        // MODO ALUGUEL (CONTRATO MASTER)
        if (itensContrato.length === 0) throw new Error("Adicione itens ao contrato")
        
        const payload = {
          nome_contrato: formData.nome_contrato,
          contratante: formData.contratante,
          data_inicio: formData.data_inicio,
          data_fim: formData.data_fim,
          valor_total_contrato: parseFloat(formData.valor_total_contrato) || 0,
          cidade: formData.cidade,
          uf: formData.uf,
          endereco: formData.endereco,
          descricao: formData.descricao,
          itens: itensContrato.map(i => ({ item_id: i.item_id, quantidade: i.quantidade }))
        }

        await compromissosAPI.criar(payload)
        toast.success('Contrato Master registrado!')
      }

      // Reset total
      setFormData({ ...formData, nome_contrato: '', contratante: '', valor_total_contrato: '', descricao: '', item_id: '', carro_id: '' })
      setItensContrato([])
      setPecasSelecionadas([])
    } catch (error) {
      toast.error(error.message || error.response?.data?.detail || 'Erro ao processar')
    } finally { setLoading(false) }
  }

  if (loadingItens) return <div className="flex justify-center p-20"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary-500"></div></div>

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-dark-50">Registrar Compromisso</h1>
        <p className="text-dark-400">Gerencie novos contratos de aluguel ou manutenções internas</p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* SELETOR DE MODO */}
        <div className="card grid grid-cols-2 gap-4 p-2 bg-dark-800">
          <button type="button" onClick={() => setFormData({...formData, tipo_compromisso: 'itens_alugados'})}
            className={`py-3 rounded-xl font-bold transition-all ${formData.tipo_compromisso === 'itens_alugados' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/20' : 'text-dark-400 hover:text-dark-200'}`}>
            <div className="flex items-center justify-center gap-2"><ClipboardList size={18}/> Aluguel (Contrato)</div>
          </button>
          <button type="button" onClick={() => setFormData({...formData, tipo_compromisso: 'pecas_carro'})}
            className={`py-3 rounded-xl font-bold transition-all ${formData.tipo_compromisso === 'pecas_carro' ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/20' : 'text-dark-400 hover:text-dark-200'}`}>
            <div className="flex items-center justify-center gap-2"><Car size={18}/> Manutenção (Carro)</div>
          </button>
        </div>

        {/* MODO ALUGUEL: CABEÇALHO DO CONTRATO */}
        {formData.tipo_compromisso === 'itens_alugados' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="label">Nome/Evento do Contrato *</label>
                <input className="input" placeholder="Ex: Feira de Agronegócio 2026" value={formData.nome_contrato} onChange={e => setFormData({...formData, nome_contrato: e.target.value})} required />
              </div>
              <div>
                <label className="label">Cliente / Contratante</label>
                <div className="relative"><User className="absolute left-3 top-3 text-dark-500" size={18}/><input className="input pl-10" value={formData.contratante} onChange={e => setFormData({...formData, contratante: e.target.value})} /></div>
              </div>
              <div>
                <label className="label">Valor Total (R$)</label>
                <div className="relative"><DollarSign className="absolute left-3 top-3 text-green-500" size={18}/><input type="number" step="0.01" className="input pl-10 text-green-400 font-bold" value={formData.valor_total_contrato} onChange={e => setFormData({...formData, valor_total_contrato: e.target.value})} /></div>
              </div>
              <div><label className="label">Data Início</label><input type="date" className="input" value={formData.data_inicio} onChange={e => setFormData({...formData, data_inicio: e.target.value})} /></div>
              <div><label className="label">Data Fim</label><input type="date" className="input" value={formData.data_fim} onChange={e => setFormData({...formData, data_fim: e.target.value})} /></div>
            </div>
          </motion.div>
        )}

        {/* MODO MANUTENÇÃO: SELEÇÃO DO CARRO */}
        {formData.tipo_compromisso === 'pecas_carro' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
            <label className="label">Selecione o Veículo *</label>
            <select className="input" value={formData.carro_id} onChange={e => setFormData({...formData, carro_id: e.target.value})} required>
              <option value="">Escolha o carro...</option>
              {itens.filter(i => i.categoria === 'Carros').map(c => <option key={c.id} value={c.id}>{formatItemName(c)}</option>)}
            </select>
          </motion.div>
        )}

        {/* SEÇÃO DE "CARRINHO" DE ITENS/PEÇAS */}
        <div className="card space-y-4 border-2 border-primary-500/10">
          <h3 className="font-bold text-dark-200 flex items-center gap-2">
            <Package size={18} className="text-primary-400"/> 
            {formData.tipo_compromisso === 'itens_alugados' ? 'Itens do Aluguel' : 'Peças Instaladas'}
          </h3>
          
          <div className="flex flex-col md:flex-row gap-3 items-end bg-dark-700/30 p-4 rounded-xl">
            <div className="flex-1">
              <label className="label">Equipamento/Peça</label>
              <select className="input" 
                value={formData.tipo_compromisso === 'itens_alugados' ? selecaoAluguel.id : selecaoPeca.id}
                onChange={e => formData.tipo_compromisso === 'itens_alugados' 
                  ? setSelecaoAluguel({...selecaoAluguel, id: e.target.value}) 
                  : setSelecaoPeca({...selecaoPeca, id: e.target.value})}>
                <option value="">Selecionar...</option>
                {itens.filter(i => formData.tipo_compromisso === 'itens_alugados' ? i.categoria !== 'Peças de Carro' : i.categoria === 'Peças de Carro')
                  .map(i => <option key={i.id} value={i.id}>{formatItemName(i)} (Qtd: {i.quantidade_total})</option>)}
              </select>
            </div>
            <div className="w-24">
              <label className="label">Qtd</label>
              <input type="number" className="input" 
                value={formData.tipo_compromisso === 'itens_alugados' ? selecaoAluguel.qtd : selecaoPeca.qtd}
                onChange={e => formData.tipo_compromisso === 'itens_alugados'
                  ? setSelecaoAluguel({...selecaoAluguel, qtd: e.target.value})
                  : setSelecaoPeca({...selecaoPeca, qtd: e.target.value})} />
            </div>
            <button type="button" onClick={formData.tipo_compromisso === 'itens_alugados' ? adicionarAoContrato : adicionarPecaLista} className="btn btn-secondary px-6"><Plus size={20}/></button>
          </div>

          <div className="space-y-2">
            <AnimatePresence>
              {(formData.tipo_compromisso === 'itens_alugados' ? itensContrato : pecasSelecionadas).map((item, idx) => (
                <motion.div key={idx} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}
                  className="flex items-center justify-between p-3 bg-dark-700/50 rounded-lg border border-dark-600">
                  <div><span className="text-dark-50 font-medium">{item.nome}</span><span className="ml-3 text-primary-400 font-bold">x{item.quantidade}</span></div>
                  <button type="button" onClick={() => formData.tipo_compromisso === 'itens_alugados' 
                    ? setItensContrato(itensContrato.filter((_, i) => i !== idx))
                    : setPecasSelecionadas(pecasSelecionadas.filter((_, i) => i !== idx))} 
                    className="text-red-400 hover:bg-red-400/10 p-1 rounded"><Trash2 size={16}/></button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

        {/* LOCALIZAÇÃO E DESCRIÇÃO */}
        <div className="card space-y-4">
          <h3 className="font-bold text-dark-200 flex items-center gap-2"><MapPin size={18} className="text-primary-400"/> Destino / Localização</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><label className="label">UF</label><select className="input" value={formData.uf} onChange={e => setFormData({...formData, uf: e.target.value})}>{UFS.map(u => <option key={u} value={u}>{u}</option>)}</select></div>
            <div className="md:col-span-3"><label className="label">Cidade</label><select className="input" value={formData.cidade} onChange={e => setFormData({...formData, cidade: e.target.value})}><option value="">Selecione...</option>{cidadesDisponiveis.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
          </div>
          <input className="input" placeholder="Endereço Completo" value={formData.endereco} onChange={e => setFormData({...formData, endereco: e.target.value})} />
          <textarea className="input h-24" placeholder="Observações adicionais..." value={formData.descricao} onChange={e => setFormData({...formData, descricao: e.target.value})} />
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-4 text-lg font-bold shadow-xl shadow-primary-500/20">
          {loading ? 'Processando Registro...' : 'Salvar Compromisso'}
        </button>
      </form>
    </div>
  )
}