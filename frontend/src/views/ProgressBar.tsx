import React from 'react'

interface ProgressBarProps {
  progress: number
  label?: string
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, label }) => {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        {label && <span className="text-sm text-gray-600">{label}</span>}
        <span className="text-sm font-semibold text-navy-700">{progress}%</span>
      </div>
      <div className="w-full h-2.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-navy-700 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
    </div>
  )
}
