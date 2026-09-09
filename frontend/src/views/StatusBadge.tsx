import React from 'react'
import { useTranslation } from '@/i18n/LanguageContext'

interface StatusBadgeProps {
  status: string
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const { t } = useTranslation()

  const getStatusInfo = (s: string) => {
    switch (s) {
      case 'accepted':
        return { label: t.statusAccepted, className: 'bg-green-100 text-green-800' }
      case 'rejected':
        return { label: t.statusRejected, className: 'bg-red-100 text-red-800' }
      default:
        return { label: t.statusPending, className: 'bg-gray-100 text-gray-700' }
    }
  }

  const info = getStatusInfo(status)

  return (
    <span className={`badge ${info.className}`}>
      {info.label}
    </span>
  )
}
