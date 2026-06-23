import { CheckCircle, Clock, XCircle } from 'lucide-react'

export default function StatusBadge({ status }) {
  const badges = {
    'Pago': { 
      icon: CheckCircle, 
      color: 'text-green-400 bg-green-400/10 border-green-400/20', 
      label: 'Pago' 
    },
    'Pendente': { 
      icon: Clock, 
      color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20', 
      label: 'Pendente' 
    },
    'Vencido': { 
      icon: XCircle, 
      color: 'text-red-400 bg-red-400/10 border-red-400/20', 
      label: 'Vencido' 
    }
  }
  
  const badge = badges[status] || badges['Pendente']
  const Icon = badge.icon
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
      <Icon size={12} />
      {badge.label}
    </span>
  )
}
