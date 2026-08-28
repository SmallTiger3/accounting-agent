export function formatMoney(value: number | string | null | undefined): string {
  const n = Number(value)
  const safe = Number.isFinite(n) ? n : 0
  return '¥' + safe.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function formatSignedMoney(value: number | string | null | undefined, type: string): string {
  const sign = type === 'income' ? '+' : type === 'transfer' ? '' : '-'
  return `${sign}${formatMoney(value)}`
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return dateStr
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}
