/**
 * 共用格式化工具 — 評分色彩、分類徽章、信號標籤、價格格式化
 */

export const scoreClass = (v: number) =>
  v >= 69.95 ? 'score-high' : v >= 49.95 ? 'score-mid' : 'score-low'

export const classificationBadge = (cls: string) => {
  switch (cls) {
    case 'BUY': return 'cls-buy'
    case 'WATCH': return 'cls-watch'
    case 'EARLY': return 'cls-early'
    default: return 'cls-ignore'
  }
}

export const signalLabel = (cls: string) => {
  switch (cls) {
    case 'BUY': return '買進'
    case 'WATCH': return '觀察'
    case 'EARLY': return '初期'
    case 'IGNORE': return '忽略'
    default: return '—'
  }
}

export const formatPrice = (v: number | null) =>
  v != null ? v.toFixed(2) : '-'
