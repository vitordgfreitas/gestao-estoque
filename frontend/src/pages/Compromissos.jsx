import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI, disponibilidadeAPI } from '../services/api'
import api from '../services/api'
import { Calendar, Plus, Info, X, Trash2, Package, Car, ClipboardList, User, MapPin, DollarSign, Filter } from 'lucide-react'
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

  // Estados de Filtro do Carrinho
  const [categoriaFiltroCarrinho, setCategoriaFiltroCarrinho] = useState('')
  const [itensFiltradosCarrinho, setItensFiltradosCarrinho] = useState([])

  const [formData, setFormData] = useState({
    tipo_compromisso: 'itens_alugados',
    nome_contrato: '',
    contratante: '',
    data_inicio: new Date().toISOString().split('T')[0],
    data_fim: new Date().toISOString().split('T')[0],
    valor_total_contrato: '0.00', // Inicializado como string para a máscara
    descricao: '',
    cidade: '',
    uf: 'DF',
    endereco: '',
    carro_id: '', 
  })

  const [itensContrato, setItensContrato] = useState([])
  const [selecaoItem, setSelecaoItem] = useState({ id: '', qtd: 1 })

  useEffect(() => {
    loadCategorias()
    loadItens()
  }, [])

  useEffect(() => {
    if (formData.uf) {
      setCidadesDisponiveis(getCidadesPorUF(formData.uf))
    }
  }, [formData.uf])

  // Filtra itens disponíveis para o carrinho conforme a categoria selecionada
  useEffect(() => {
    let filtrados = itens;
    
    if (formData.tipo_compromisso === 'pecas_carro') {
      filtrados = itens.filter(i => i.categoria === 'Peças de Carro' || i.categoria === 'Pecas');
    } else if (categoriaFiltroCarrinho && categoriaFiltroCarrinho !== 'Todas as Categorias') {
      filtrados = itens.filter(i => (i.categoria || '').trim() === categoriaFiltroCarrinho.trim());
    } else {
      filtrados = itens.filter(i => i.categoria !== 'Peças de Carro');
    }
    
    setItensFiltradosCarrinho(filtrados);
    setSelecaoItem(prev => ({ ...prev, id: '' }));
  }, [categoriaFiltroCarrinho, itens, formData.tipo_compromisso])

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

  // MÁSCARA DE CENTAVOS (Responsiva ao digitar)
  const handleCurrencyChange = (e) => {
    let value = e.target.value.replace(/\D/g, "");
    if (!value) value = "0";
    value = (parseInt(value) / 100).toFixed(2);
    setFormData({ ...formData, valor_total_contrato: value });
  };

  // ADICIONAR ITEM COM TRAVA DE ESTOQUE TOTAL
  const handleAddItem = () => {
    if (!selecaoItem.id) return toast.error("Selecione um item");
    
    const itemInfo = itens.find(i => i.id === parseInt(selecaoItem.id));
    const quantidadeDigitada = parseInt(selecaoItem.qtd);

    if (quantidadeDigitada > itemInfo.quantidade_total) {
      return toast.error(
        `Estoque insuficiente! Você possui apenas ${itemInfo.quantidade_total} unidades de "${itemInfo.nome}" no total.`
      );
    }

    const existente = itensContrato.find(i => i.item_id === itemInfo.id);
    const quantidadeJaNoCarrinho = existente ? existente.quantidade : 0;

    if (quantidadeJaNoCarrinho + quantidadeDigitada > itemInfo.quantidade_total) {
      return toast.error(
        `Limite atingido! Já existem ${quantidadeJaNoCarrinho} unidades na lista e você tem apenas ${itemInfo.quantidade_total} no acervo.`
      );
    }

    if (existente) {
      setItensContrato(itensContrato.map(i => i.item_id === itemInfo.id 
        ? { ...i, quantidade: i.quantidade + quantidadeDigitada } : i));
    } else {
      setItensContrato([...itensContrato, { 
        item_id: itemInfo.id, 
        nome: formatItemName(itemInfo), 
        quantidade: quantidadeDigitada 
      }]);
    }
    
    setSelecaoItem({ id: '', qtd: 1 });
    toast.success("Item validado e adicionado.");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (formData.tipo_compromisso === 'pecas_carro') {
        if (!formData.carro_id || itensContrato.length === 0) {
          throw new Error("Selecione o veículo e as peças")
        }
        const promises = itensContrato.map(p =>
          api.post('/api/pecas-carros', {
            peca_id: p.item_id,
            carro_id: parseInt(formData.carro_id),
            quantidade: p.quantidade,
            data_instalacao: formData.data_inicio,
            observacoes: formData.descricao
          })
        )
        await Promise.all(promises)
        toast.success('Manutenção/Instalação registrada com sucesso!')
      } else {
        if (itensContrato.length === 0) throw new Error("Adicione pelo menos um item ao contrato")
        
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

        await api.post('/api/compromissos', payload)
        toast.success('Contrato Master registrado com sucesso!')
      }

      // Resetar formulário
      setFormData({ 
        ...formData, 
        nome_contrato: '', 
        contratante: '', 
        valor_total_contrato: '0.00', 
        descricao: '', 
        carro_id: '',
        endereco: ''
      })
      setItensContrato([])
      setCategoriaFiltroCarrinho('')
    } catch (error) {
      toast.error(error.message || error.response?.data?.detail || 'Erro ao processar operação')
    } finally { setLoading(false) }
  }

  if (loadingItens) return (
    <div className="flex justify-center p-20">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary-500"></div>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-dark-50">Registrar Compromisso</h1>
        <p className="text-dark-400">Gestão de Contratos Master e Manutenção de Veículos</p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* SELETOR DE MODO */}
        <div className="card grid grid-cols-2 gap-4 p-2 bg-dark-800">
          <button 
            type="button" 
            onClick={() => { setFormData({...formData, tipo_compromisso: 'itens_alugados'}); setItensContrato([]); }}
            className={`py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-2 ${formData.tipo_compromisso === 'itens_alugados' ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-400'}`}
          >
            <ClipboardList size={18}/> Aluguel / Contrato
          </button>
          <button 
            type="button" 
            onClick={() => { setFormData({...formData, tipo_compromisso: 'pecas_carro'}); setItensContrato([]); }}
            className={`py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-2 ${formData.tipo_compromisso === 'pecas_carro' ? 'bg-blue-500 text-white shadow-lg' : 'text-dark-400'}`}
          >
            <Car size={18}/> Manutenção / Peças
          </button>
        </div>

        {/* CABEÇALHO DINÂMICO */}
        <AnimatePresence mode="wait">
          {formData.tipo_compromisso === 'itens_alugados' ? (
            <motion.div 
              key="aluguel"
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}
              className="card space-y-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="label">Nome do Evento / Contrato *</label>
                  <input className="input" placeholder="Ex: Casamento ou Feira Industrial" value={formData.nome_contrato} onChange={e => setFormData({...formData, nome_contrato: e.target.value})} required />
                </div>
                <div>
                  <label className="label">Cliente / Contratante</label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 text-dark-500" size={18}/>
                    <input className="input pl-10" value={formData.contratante} onChange={e => setFormData({...formData, contratante: e.target.value})} />
                  </div>
                </div>
                <div>
                  <label className="label text-dark-300 font-bold uppercase tracking-wider text-[10px]">Valor Total do Contrato (R$)</label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-3 text-green-500" size={18}/>
                    <input 
                      type="text" inputMode="numeric"
                      className="input pl-10 text-green-400 font-black text-lg focus:ring-green-500/30" 
                      placeholder="0,00"
                      value={formData.valor_total_contrato}
                      onChange={handleCurrencyChange}
                    />
                  </div>
                </div>
                <div><label className="label">Início do Aluguel</label><input type="date" className="input" value={formData.data_inicio} onChange={e => setFormData({...formData, data_inicio: e.target.value})} /></div>
                <div><label className="label">Fim do Aluguel</label><input type="date" className="input" value={formData.data_fim} onChange={e => setFormData({...formData, data_fim: e.target.value})} /></div>
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="carro"
              initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              className="card space-y-4"
            >
              <label className="label">Veículo Destinatário *</label>
              <select className="input" value={formData.carro_id} onChange={e => setFormData({...formData, carro_id: e.target.value})} required>
                <option value="">Escolha o carro...</option>
                {itens.filter(i => i.categoria === 'Carros').map(c => <option key={c.id} value={c.id}>{formatItemName(c)}</option>)}
              </select>
              <div><label className="label">Data da Instalação/Manutenção</label><input type="date" className="input" value={formData.data_inicio} onChange={e => setFormData({...formData, data_inicio: e.target.value})} /></div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* SEÇÃO DO CARRINHO DE ITENS */}
        <div className="card space-y-4 border-2 border-primary-500/10">
          <h3 className="font-bold text-dark-200 flex items-center gap-2">
            <Package size={18} className="text-primary-400"/> 
            {formData.tipo_compromisso === 'itens_alugados' ? 'Equipamentos Selecionados' : 'Peças a Instalar'}
          </h3>
          
          <div className="bg-dark-700/30 p-4 rounded-xl space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {formData.tipo_compromisso === 'itens_alugados' && (
                <div>
                  <label className="label flex items-center gap-2"><Filter size={14}/> Filtrar por Categoria</label>
                  <select className="input" value={categoriaFiltroCarrinho} onChange={e => setCategoriaFiltroCarrinho(e.target.value)}>
                    <option value="Todas as Categorias">Todas as Categorias</option>
                    {categorias.filter(c => c !== 'Peças de Carro').map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              )}
              <div className={formData.tipo_compromisso === 'pecas_carro' ? 'col-span-2' : ''}>
                <label className="label">Selecionar Ativo</label>
                <select className="input" value={selecaoItem.id} onChange={e => setSelecaoItem({...selecaoItem, id: e.target.value})}>
                  <option value="">Escolha um item...</option>
                  {itensFiltradosCarrinho.map(i => (
                    <option key={i.id} value={i.id}>{formatItemName(i)} (Acervo: {i.quantidade_total})</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="label">Quantidade Desejada</label>
                <input 
                  type="number" 
                  className={`input transition-all ${selecaoItem.id && parseInt(selecaoItem.qtd) > (itens.find(i => i.id === parseInt(selecaoItem.id))?.quantidade_total || 0) ? 'border-red-500 text-red-500 ring-1 ring-red-500/50' : ''}`}
                  value={selecaoItem.qtd} 
                  onChange={e => setSelecaoItem({...selecaoItem, qtd: e.target.value})} 
                  min="1"
                  max={itens.find(i => i.id === parseInt(selecaoItem.id))?.quantidade_total || 999}
                />
                {selecaoItem.id && (
                  <p className="text-[10px] mt-1 text-dark-400 italic">
                    Limite físico em estoque: <span className="font-bold text-primary-400">{itens.find(i => i.id === parseInt(selecaoItem.id))?.quantidade_total} un.</span>
                  </p>
                )}
              </div>
              <button type="button" onClick={handleAddItem} className="btn btn-secondary px-8 py-3 flex items-center gap-2">
                <Plus size={20}/> Adicionar
              </button>
            </div>
          </div>

          {/* LISTA DE ITENS NO CONTRATO ATUAL */}
          <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
            <AnimatePresence>
              {itensContrato.map((item, idx) => (
                <motion.div 
                  key={idx} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, x: 20 }}
                  className="flex items-center justify-between p-3 bg-dark-700/50 rounded-lg border border-dark-600 group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-dark-800 flex items-center justify-center text-xs font-bold text-primary-400">
                      {idx + 1}
                    </div>
                    <div>
                      <span className="text-dark-50 font-medium">{item.nome}</span>
                      <span className="ml-3 px-2 py-0.5 bg-primary-500/20 text-primary-400 rounded text-xs font-bold border border-primary-500/20">x{item.quantidade}</span>
                    </div>
                  </div>
                  <button 
                    type="button" 
                    onClick={() => setItensContrato(itensContrato.filter((_, i) => i !== idx))} 
                    className="text-dark-400 hover:text-red-400 hover:bg-red-400/10 p-2 rounded-lg transition-all"
                  >
                    <Trash2 size={18}/>
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
            {itensContrato.length === 0 && (
              <div className="text-center py-6 text-dark-500 text-sm italic border border-dashed border-dark-700 rounded-lg bg-dark-800/20">
                Nenhum equipamento adicionado à lista.
              </div>
            )}
          </div>
        </div>

        {/* LOCALIZAÇÃO E DETALHES FINAL */}
        <div className="card space-y-4">
          <h3 className="font-bold text-dark-200 flex items-center gap-2"><MapPin size={18} className="text-primary-400"/> Localização e Notas</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="label">UF</label>
              <select className="input" value={formData.uf} onChange={e => setFormData({...formData, uf: e.target.value})}>
                {UFS.map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
            <div className="md:col-span-3">
              <label className="label">Cidade</label>
              <select className="input" value={formData.cidade} onChange={e => setFormData({...formData, cidade: e.target.value})} required>
                <option value="">Selecione...</option>
                {cidadesDisponiveis.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <input className="input" placeholder="Endereço exato ou ponto de referência" value={formData.endereco} onChange={e => setFormData({...formData, endereco: e.target.value})} />
          <textarea className="input h-24" placeholder="Observações, detalhes técnicos ou notas de entrega..." value={formData.descricao} onChange={e => setFormData({...formData, descricao: e.target.value})} />
        </div>

        <button 
          type="submit" 
          disabled={loading} 
          className="btn btn-primary w-full py-4 text-lg font-black shadow-xl shadow-primary-500/30 flex items-center justify-center gap-3 transition-all hover:scale-[1.01] active:scale-[0.99]"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-white"></div>
              <span>Sincronizando com Supabase...</span>
            </>
          ) : (
            <>
              <Calendar size={22}/>
              <span>CONCLUIR E REGISTRAR</span>
            </>
          )}
        </button>
      </form>
    </div>
  )
}