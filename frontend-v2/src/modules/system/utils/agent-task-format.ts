import type { StatusTone } from '@/shared/ui/status-tone'

/**
 * Định dạng cho màn Việc của bot (ai-CR-036).
 *
 * Bộ số trạng thái khớp `ST_*` ở `backend/app/modules/agent_hub/constants.py` — gõ tay vì
 * `gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI.
 */
export const AGENT_TASK_STATUS = {
  INBOX: 1,
  TRIAGE: 2,
  PLAN: 3,
  CODE: 4,
  CI: 5,
  REVIEW: 6,
  PROD: 7,
  DONE: 8,
  CANCELLED: 9,
  FAILED: 10,
  NEEDS_INPUT: 11,
  DEPLOYING: 12,
  SCANNING: 13,
} as const

const TONE_BY_STATUS: Record<number, StatusTone> = {
  [AGENT_TASK_STATUS.INBOX]: 'neutral',
  [AGENT_TASK_STATUS.TRIAGE]: 'neutral',
  [AGENT_TASK_STATUS.SCANNING]: 'active',
  [AGENT_TASK_STATUS.PLAN]: 'pending',
  [AGENT_TASK_STATUS.NEEDS_INPUT]: 'returned',
  [AGENT_TASK_STATUS.CODE]: 'active',
  [AGENT_TASK_STATUS.CI]: 'active',
  [AGENT_TASK_STATUS.REVIEW]: 'pending',
  [AGENT_TASK_STATUS.DEPLOYING]: 'active',
  [AGENT_TASK_STATUS.PROD]: 'progress',
  [AGENT_TASK_STATUS.DONE]: 'done',
  [AGENT_TASK_STATUS.CANCELLED]: 'danger',
  [AGENT_TASK_STATUS.FAILED]: 'danger',
}

export function agentTaskTone(status: number): StatusTone {
  return TONE_BY_STATUS[status] ?? 'neutral'
}

/** `$0.031` — chi phí model rất nhỏ nên giữ 3 chữ số lẻ; 0 thì ghi «—». */
export function formatUsd(value: number | null | undefined): string {
  if (!value) return '—'
  return `$${value < 1 ? value.toFixed(3) : value.toFixed(2)}`
}

/** `45 giây` · `6,6 phút` · `33 phút` — cùng lối với dòng «Thời gian» trên thẻ Telegram. */
export function formatDurationMs(ms: number | null | undefined): string {
  const sec = Math.max(Math.floor((ms ?? 0) / 1000), 0)
  if (!sec) return '—'
  if (sec < 60) return `${sec} giây`
  const minutes = sec / 60
  return `${minutes < 10 ? minutes.toFixed(1).replace('.', ',') : Math.round(minutes)} phút`
}

/** Tin của bot là HTML Telegram (`<b>`, `<code>`, `<pre>`) — màn này hiện chữ trơn. */
export function stripTelegramHtml(html: string): string {
  return html
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
}
