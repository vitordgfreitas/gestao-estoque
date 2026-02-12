import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { disponibilidadeAPI, itensAPI, categoriasAPI } from '../services/api'
// ADICIONEI 'Calendar' E 'AlertTriangle' NA LISTA ABAIXO
import { Search, CheckCircle2, XCircle, ChevronDown, ChevronUp, MapPin, Package, Car, Info, Calendar, AlertTriangle } from 'lucide-react'
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

  const itensParaSelecao = itens.filter(i => {
    if (categoriaFiltro !== 'Todas as Categorias' && i.categoria !== categoriaFiltro) return false
    if (localizacaoFiltro !== 'Todas as Localizações') {
      const locStr = `${i.cidade} - ${i.uf}`
      if (locStr !== localizacaoFiltro) return false
    }
    return true
  })

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
        toast('Nenhum item encontrado', { icon: '⚠️' })
      }
    } catch (error) {
      toast.error('Erro no servidor ao consultar disponibilidade')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-dark-50">Consulta de Disponibilidade</h1>
          <p className="text-dark-400">Estoque livre para locações e uso interno</p>
        </div>
      </header>

      {/* FORMULÁRIO */}
      <motion.form 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit} 
        className="card space-y-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-bold text-dark-300 uppercase">Data do Aluguel</label>
            <input type="date" className="input" value={dataConsulta} onChange={e => setDataConsulta(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-bold text-dark-300 uppercase">Categoria</label>
            <select className="input" value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)}>
              <option>Todas as Categorias</option>
              {categorias.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-bold text-dark-300 uppercase">Base</label>
            <select className="input" value={localizacaoFiltro} onChange={e => setLocalizacaoFiltro(e.target.value)}>
              <option>Todas as Localizações</option>
              {localizacoes.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        </div>

        <div className="flex flex-wrap gap-6 p-4 bg-dark-700/30 rounded-xl border border-dark-600">
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="radio" checked={modoConsulta === 'todos'} onChange={() => setModoConsulta('todos')} className="w-5 h-5 text-primary-500 bg-dark-800 border-dark-500" />
            <span className="text-sm font-bold text-dark-200">Ver Tudo</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="radio" checked={modoConsulta === 'especifico'} onChange={() => setModoConsulta('especifico')} className="w-5 h-5 text-primary-500 bg-dark-800 border-dark-500" />
            <span className="text-sm font-bold text-dark-200">Item Específico</span>
          </label>
        </div>

        {modoConsulta === 'especifico' && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
            <label className="label">Ativo para verificar</label>
            <select className="input" value={itemSelecionado} onChange={e => setItemSelecionado(e.target.value)} required>
              <option value="">Selecione...</option>
              {itensParaSelecao.map(i => <option key={i.id} value={i.id}>{formatItemName(i)}</option>)}
            </select>
          </motion.div>
        )}

        <button type="submit" disabled={loading} className="btn btn-primary w-full py-4 text-lg font-bold flex justify-center gap-3">
          {loading ? <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div> : <><Search size={24}/> Verificar</>}
        </button>
      </motion.form>

      {/* RESULTADOS */}
      <AnimatePresence>
        {resultado && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            
            {resultado.item && (
              <div className="card border-l-8 border-primary-500">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                  <div>
                    <h3 className="text-2xl font-black text-dark-50">{resultado.item.nome}</h3>
                    <p className="text-sm text-dark-400 uppercase tracking-tighter">{resultado.item.categoria} | ID: {resultado.item.id}</p>
                  </div>
                  <div className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-sm border-2 ${resultado.quantidade_disponivel > 0 ? 'bg-green-500/10 text-green-400 border-green-500/30' : 'bg-red-500/10 text-red-400 border-red-500/30'}`}>
                    {resultado.quantidade_disponivel > 0 ? <CheckCircle2 size={20}/> : <XCircle size={20}/>}
                    {resultado.quantidade_disponivel > 0 ? 'DISPONÍVEL' : 'ESGOTADO'}
                  </div>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <StatCard label="Estoque Total" value={resultado.quantidade_total} color="text-dark-50" icon={<Package className="text-dark-500"/>} />
                  <StatCard label="Alugado" value={resultado.quantidade_comprometida} color="text-yellow-500" icon={<Calendar className="text-yellow-500/50"/>} />
                  <StatCard label="Instalado" value={resultado.quantidade_instalada} color="text-blue-500" icon={<Car className="text-blue-500/50"/>} />
                  <StatCard label="Disponível" value={resultado.quantidade_disponivel} color="text-green-500" bold icon={<CheckCircle2 className="text-green-500/50"/>} />
                </div>

                {resultado.compromissos_ativos?.length > 0 && (
                  <div className="mt-8 pt-6 border-t border-dark-700">
                    <h4 className="text-xs font-black text-dark-400 uppercase tracking-widest mb-4">Ocupação nesta data:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {resultado.compromissos_ativos.map(c => (
                        <div key={c.id} className="p-4 bg-dark-700/40 rounded-xl border border-dark-600">
                          <p className="font-bold text-dark-50">{c.contratante || 'Cliente não identificado'}</p>
                          <p className="text-xs text-dark-400 mt-1">{c.quantidade} un. até {formatDate(c.data_fim)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {resultado.resultados && (
              <div className="grid grid-cols-1 gap-3">
                {resultado.resultados.map((r, idx) => (
                  <div key={idx} className="card py-4 hover:border-primary-500/50 transition-all">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${r.item.categoria === 'Carros' ? 'bg-blue-500/10' : 'bg-primary-500/10'}`}>
                          {r.item.categoria === 'Carros' ? <Car size={22} className="text-blue-400"/> : <Package size={22} className="text-primary-400"/>}
                        </div>
                        <div>
                          <h4 className="font-bold text-dark-50">{formatItemName(r.item)}</h4>
                          <p className="text-[10px] text-dark-400 font-bold uppercase">{r.item.cidade} / {r.item.uf}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 md:gap-8 justify-between md:justify-end">
                        <div className="text-center px-4"><p className="text-[10px] text-dark-500 uppercase font-black">Total</p><p className="text-lg font-bold">{r.quantidade_total}</p></div>
                        <div className="text-center px-4 border-l border-dark-700"><p className="text-[10px] text-dark-500 uppercase font-black">Ocupado</p><p className="text-lg font-bold text-yellow-500">{(r.quantidade_comprometida || 0) + (r.quantidade_instalada || 0)}</p></div>
                        <div className={`text-center min-w-[100px] px-4 py-2 rounded-xl border ${r.quantidade_disponivel > 0 ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
                          <p className="text-[10px] text-dark-500 uppercase font-black">Livre</p>
                          <p className={`text-xl font-black ${r.quantidade_disponivel > 0 ? 'text-green-500' : 'text-red-500'}`}>{r.quantidade_disponivel}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function StatCard({ label, value, color, bold, icon }) {
  return (
    <div className="p-4 bg-dark-700/40 rounded-2xl border border-dark-600 relative overflow-hidden">
      <div className="absolute right-2 top-2 opacity-20">{icon}</div>
      <p className="text-[10px] text-dark-400 uppercase font-black tracking-widest mb-1">{label}</p>
      <p className={`text-3xl ${bold ? 'font-black' : 'font-bold'} ${color}`}>{value}</p>
    </div>
  )
}