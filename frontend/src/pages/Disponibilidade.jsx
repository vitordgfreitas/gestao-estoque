import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { disponibilidadeAPI, itensAPI, categoriasAPI } from '../services/api'
import { Search, CheckCircle2, XCircle, ChevronDown, ChevronUp, MapPin, Package, Car, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatItemName, formatDate } from '../utils/format'

export default function Disponibilidade() {
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [localizacoes, setLocalizacoes] = useState([])
  const [dataConsulta, setDataConsulta] = useState(new Date().toISOString().split('T')[0])
  const [modoConsulta, setModoConsulta] = useState('todos')
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas as Categorias')
  const [localizacaoFiltro, setLocalizacaoFiltro] = useState('Todas as Localizações')
  const [itemSelecionado, setItemSelecionado] = useState('')
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading] = useState(false)

  // --- CARREGAMENTO DE DADOS INICIAIS ---
  useEffect(() => {
    async function fetchData() {
      try {
        const [resItens, resCats] = await Promise.all([
          itensAPI.listar(),
          categoriasAPI.listar()
        ])
        setItens(resItens.data || [])
        setCategorias(resCats.data || [])
        
        // Extração de bases logísticas únicas
        const locs = new Set()
        resItens.data.forEach(i => {
          if (i.cidade && i.uf) locs.add(`${i.cidade} - ${i.uf}`)
        })
        setLocalizacoes(Array.from(locs).sort())
      } catch (error) {
        toast.error('Erro ao carregar inventário')
      }
    }
    fetchData()
  }, [])

  // --- LÓGICA DE FILTRO DO SELECT ---
  const itensParaSelecao = itens.filter(i => {
    if (categoriaFiltro !== 'Todas as Categorias' && i.categoria !== categoriaFiltro) return false
    if (localizacaoFiltro !== 'Todas as Localizações') {
      const locStr = `${i.cidade} - ${i.uf}`
      if (locStr !== localizacaoFiltro) return false
    }
    return true
  })

  // --- SUBMISSÃO DA CONSULTA ---
  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResultado(null)

    try {
      const payload = {
        item_id: modoConsulta === 'especifico' && itemSelecionado ? parseInt(itemSelecionado) : null,
        data_consulta: dataConsulta,
        filtro_categoria: categoriaFiltro !== 'Todas as Categorias' ? categoriaFiltro : null,
        filtro_localizacao: localizacaoFiltro !== 'Todas as Localizações' ? localizacaoFiltro : null,
      }
      
      const response = await disponibilidadeAPI.verificar(payload)
      setResultado(response.data)
      
      if (response.data.resultados?.length === 0) {
        toast('Nenhum item encontrado nos filtros selecionados', { icon: '⚠️' })
      }
    } catch (error) {
      console.error(error)
      toast.error('Erro ao processar consulta no servidor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-dark-50">Consulta de Disponibilidade</h1>
          <p className="text-dark-400">Verifique o estoque livre para locações futuras</p>
        </div>
        <div className="px-4 py-2 bg-primary-600/10 border border-primary-500/20 rounded-lg">
          <span className="text-sm text-primary-400 font-medium">Hoje: {formatDate(new Date())}</span>
        </div>
      </header>

      {/* PAINEL DE FILTROS */}
      <motion.form 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit} 
        className="card space-y-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-bold text-dark-300 uppercase tracking-wider">Data do Aluguel</label>
            <input 
              type="date" 
              className="input border-primary-500/30 focus:border-primary-500" 
              value={dataConsulta} 
              onChange={e => setDataConsulta(e.target.value)} 
              required 
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-bold text-dark-300 uppercase tracking-wider">Categoria</label>
            <select className="input" value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)}>
              <option>Todas as Categorias</option>
              {categorias.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-bold text-dark-300 uppercase tracking-wider">Filtrar por Base</label>
            <select className="input" value={localizacaoFiltro} onChange={e => setLocalizacaoFiltro(e.target.value)}>
              <option>Todas as Localizações</option>
              {localizacoes.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        </div>

        <div className="flex flex-wrap gap-6 p-4 bg-dark-700/30 rounded-xl border border-dark-600">
          <label className="flex items-center gap-3 cursor-pointer group">
            <input 
              type="radio" 
              checked={modoConsulta === 'todos'} 
              onChange={() => setModoConsulta('todos')} 
              className="w-5 h-5 text-primary-500 bg-dark-800 border-dark-500 focus:ring-primary-500" 
            />
            <span className="text-sm font-bold text-dark-200 group-hover:text-primary-400 transition-colors">Ver Todo o Inventário</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer group">
            <input 
              type="radio" 
              checked={modoConsulta === 'especifico'} 
              onChange={() => setModoConsulta('especifico')} 
              className="w-5 h-5 text-primary-500 bg-dark-800 border-dark-500 focus:ring-primary-500" 
            />
            <span className="text-sm font-bold text-dark-200 group-hover:text-primary-400 transition-colors">Consultar Item Específico</span>
          </label>
        </div>

        {modoConsulta === 'especifico' && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-2">
            <label className="label">Qual ativo deseja verificar?</label>
            <select className="input" value={itemSelecionado} onChange={e => setItemSelecionado(e.target.value)} required>
              <option value="">Selecione na lista...</option>
              {itensParaSelecao.map(i => <option key={i.id} value={i.id}>{formatItemName(i)}</option>)}
            </select>
          </motion.div>
        )}

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-4 text-lg font-bold shadow-lg shadow-primary-500/20 flex justify-center gap-3">
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
              <span>Processando...</span>
            </>
          ) : (
            <>
              <Search size={24}/>
              <span>Verificar Disponibilidade</span>
            </>
          )}
        </button>
      </form>

      {/* EXIBIÇÃO DOS RESULTADOS */}
      <AnimatePresence>
        {resultado && (
          <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
            
            {/* TIPO 1: RESULTADO DE ITEM ÚNICO */}
            {resultado.item && (
              <div className="card border-l-8 border-primary-500">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                  <div>
                    <h3 className="text-2xl font-black text-dark-50">{resultado.item.nome}</h3>
                    <div className="flex gap-2 mt-1">
                      <span className="px-2 py-0.5 bg-dark-700 text-dark-400 text-[10px] font-bold rounded uppercase tracking-tighter">
                        {resultado.item.categoria}
                      </span>
                      <span className="px-2 py-0.5 bg-dark-700 text-dark-400 text-[10px] font-bold rounded">
                        ID: {resultado.item.id}
                      </span>
                    </div>
                  </div>
                  <div className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-sm border-2 ${
                    resultado.quantidade_disponivel > 0 
                    ? 'bg-green-500/10 text-green-400 border-green-500/30' 
                    : 'bg-red-500/10 text-red-400 border-red-500/30'
                  }`}>
                    {resultado.quantidade_disponivel > 0 ? <CheckCircle2 size={20}/> : <XCircle size={20}/>}
                    {resultado.quantidade_disponivel > 0 ? 'DISPONÍVEL PARA LOCAÇÃO' : 'ESTOQUE ESGOTADO'}
                  </div>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <StatCard label="Estoque Total" value={resultado.quantidade_total} color="text-dark-50" icon={<Package className="text-dark-500"/>} />
                  <StatCard label="Alugado (Saída)" value={resultado.quantidade_comprometida} color="text-yellow-500" icon={<Calendar className="text-yellow-500/50"/>} />
                  <StatCard label="Uso Interno (Peças)" value={resultado.quantidade_instalada} color="text-blue-500" icon={<Car className="text-blue-500/50"/>} />
                  <StatCard label="Livre Agora" value={resultado.quantidade_disponivel} color="text-green-500" bold icon={<CheckCircle2 className="text-green-500/50"/>} />
                </div>

                {resultado.compromissos_ativos?.length > 0 && (
                  <div className="mt-8">
                    <h4 className="flex items-center gap-2 text-sm font-black text-dark-300 uppercase tracking-widest mb-4">
                      <Info size={16}/> Cronograma para esta data
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {resultado.compromissos_ativos.map(c => (
                        <div key={c.id} className="p-4 bg-dark-700/40 border border-dark-600 rounded-xl flex flex-col justify-between">
                          <p className="font-bold text-dark-50">{c.contratante || 'Cliente Final'}</p>
                          <p className="text-xs text-dark-400 mt-1">
                            {c.quantidade} unidade(s) até {formatDate(c.data_fim)}
                          </p>
                          <div className="flex items-center gap-1 mt-3 text-[10px] text-primary-400 font-bold">
                            <MapPin size={10}/> {c.cidade} - {c.uf}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TIPO 2: LISTAGEM COMPLETA DE RESULTADOS */}
            {resultado.resultados && (
              <div className="grid grid-cols-1 gap-3">
                <div className="flex items-center justify-between px-4 mb-2">
                  <span className="text-xs font-bold text-dark-500 uppercase tracking-widest">Ativo / Localização</span>
                  <span className="text-xs font-bold text-dark-500 uppercase tracking-widest">Status de Estoque</span>
                </div>
                {resultado.resultados.map((r, idx) => (
                  <motion.div 
                    key={idx} 
                    initial={{ opacity: 0, x: -10 }} 
                    animate={{ opacity: 1, x: 0 }} 
                    transition={{ delay: idx * 0.03 }}
                    className="card hover:border-primary-500/50 transition-all cursor-default py-4"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${r.item.categoria === 'Carros' ? 'bg-blue-500/10' : 'bg-primary-500/10'}`}>
                          {r.item.categoria === 'Carros' ? <Car size={22} className="text-blue-400"/> : <Package size={22} className="text-primary-400"/>}
                        </div>
                        <div>
                          <h4 className="font-bold text-dark-50 leading-tight">{formatItemName(r.item)}</h4>
                          <div className="flex items-center gap-1 text-[10px] text-dark-400 font-bold uppercase mt-1">
                            <MapPin size={10}/> {r.item.cidade || 'Base Central'} / {r.item.uf || 'DF'}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 md:gap-8 justify-between md:justify-end">
                        <div className="text-center px-4">
                          <p className="text-[10px] text-dark-500 uppercase font-black">Total</p>
                          <p className="text-lg font-bold text-dark-100">{r.quantidade_total}</p>
                        </div>
                        <div className="text-center px-4 border-l border-dark-700">
                          <p className="text-[10px] text-dark-500 uppercase font-black">Ocupado</p>
                          <p className="text-lg font-bold text-yellow-500">{(r.quantidade_comprometida || 0) + (r.quantidade_instalada || 0)}</p>
                        </div>
                        <div className={`text-center min-w-[100px] px-4 py-2 rounded-xl border ${
                          r.quantidade_disponivel > 0 
                          ? 'bg-green-500/5 border-green-500/20' 
                          : 'bg-red-500/5 border-red-500/20'
                        }`}>
                          <p className="text-[10px] text-dark-500 uppercase font-black">Livre</p>
                          <p className={`text-xl font-black ${r.quantidade_disponivel > 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {r.quantidade_disponivel}
                          </p>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// --- SUB-COMPONENTE DE CARTÃO DE MÉTRICA ---
function StatCard({ label, value, color, bold, icon }) {
  return (
    <div className="p-4 bg-dark-700/40 rounded-2xl border border-dark-600 relative overflow-hidden group">
      <div className="absolute right-2 top-2 opacity-20 group-hover:opacity-40 transition-opacity">
        {icon}
      </div>
      <p className="text-[10px] text-dark-400 uppercase font-black tracking-widest mb-1">{label}</p>
      <p className={`text-3xl ${bold ? 'font-black' : 'font-bold'} ${color}`}>{value}</p>
    </div>
  )
}