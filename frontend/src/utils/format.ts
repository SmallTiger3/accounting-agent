export function formatMoney(value: number | null | undefined): string {
  const n = Number(value || 0)
  return '¥' + n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function formatSignedMoney(value: number | null | undefined, type: string): string {
  const sign = type === 'income' ? '+' : '-'
  return `${sign}${formatMoney(value)}`
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return dateStr
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}
