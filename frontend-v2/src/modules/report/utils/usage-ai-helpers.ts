import { AI_CHANNEL, AI_CLIENT, USAGE_UNMEASURED_REASON_CODE } from '@/shared/constants/statuses'

import type { UsageSnapshot } from '../types/usage-profile'

/** Tên nhóm công cụ AI (khóa theo `mcp_settings.GROUPS` của dịch vụ AI) — khóa lạ hiện nguyên mã. */
export const AI_TOOL_GROUP_LABELS: Record<string, string> = {
  mine: 'Việc và phiếu của mình',
  leave: 'Nghỉ phép',
  directory: 'Danh bạ, hướng dẫn',
  reports: 'Báo cáo',
  skills: 'Kho skill AI',
  purchase: 'Thu mua',
  finance: 'Công nợ, thanh toán',
  document: 'Văn thư',
  work: 'Công việc, dự án',
  customs: 'Thị trường',
  google: 'Lịch, Drive',
  personal: 'Sổ nhớ, ghi chú',
  ticket: 'Phiếu hỗ trợ',
  research: 'Nghiên cứu sâu',
  export: 'Xuất tệp',
  admin: 'Quản trị bằng lời',
  khac: 'Khác',
}

export interface UsageAiBar {
  label: string
  value: number
}

const byValueDesc = (a: UsageAiBar, b: UsageAiBar) => b.value - a.value

/** `{mã: lượt}` → cột có nhãn từ bộ mã sinh; mã lạ hiện nguyên số. Bỏ mục 0 lượt. */
export function codeCountsToBars(counts: Record<string, number> | undefined, options: readonly { value: string; label: string }[]): UsageAiBar[] {
  return Object.entries(counts ?? {})
    .filter(([, n]) => n > 0)
    .map(([code, value]) => ({ label: options.find((o) => o.value === code)?.label ?? `Mã ${code}`, value }))
    .sort(byValueDesc)
}

export const channelBars = (s: UsageSnapshot) => codeCountsToBars(s.lists?.ai_channels, AI_CHANNEL)
export const clientBars = (s: UsageSnapshot) => codeCountsToBars(s.lists?.ai_clients, AI_CLIENT)
export const toolGroupBars = (s: UsageSnapshot): UsageAiBar[] =>
  (s.lists?.ai_tool_groups ?? []).map(([key, value]) => ({ label: AI_TOOL_GROUP_LABELS[key] ?? key, value }))

/** Chưa thu số dùng AI: khóa lượt dùng nằm ở `unmeasured` với lý do «chưa thu thập» (hoặc không có giá trị). */
export function isAiNotCollected(s: UsageSnapshot): boolean {
  const reason = s.unmeasured?.ai_uses
  return reason === USAGE_UNMEASURED_REASON_CODE.NOT_COLLECTED || (s.metrics.ai_uses?.v == null && reason === undefined)
}
