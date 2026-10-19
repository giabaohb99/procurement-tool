import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS, type StatusTone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { CALL_STATUS, KEY_STATE, SECURITY_LEVEL, SKILL_SET_STATUS } from './ai-skill-constants'

/** Huy hiệu trạng thái của Kho skill — màu theo bảng tông dùng chung (`status-tone.ts`), nhãn lấy từ backend. */

function ToneBadge({ tone, label }: { tone: StatusTone; label: string }) {
  return (
    <Badge variant="outline" className={cn('border-transparent font-medium', TONE_CLASS[tone])}>
      {label || '—'}
    </Badge>
  )
}

const SET_STATUS_TONE: Record<number, StatusTone> = {
  [SKILL_SET_STATUS.draft]: 'neutral',
  [SKILL_SET_STATUS.active]: 'done',
  [SKILL_SET_STATUS.archived]: 'closed',
}

export function SkillStatusBadge({ status, label }: { status: number; label: string }) {
  return <ToneBadge tone={SET_STATUS_TONE[status] ?? 'neutral'} label={label} />
}

const SECURITY_TONE: Record<number, StatusTone> = {
  [SECURITY_LEVEL.open]: 'progress',
  [SECURITY_LEVEL.protected]: 'pending',
  [SECURITY_LEVEL.locked]: 'danger',
}

export function SecurityLevelBadge({ level, label }: { level: number; label: string }) {
  return <ToneBadge tone={SECURITY_TONE[level] ?? 'neutral'} label={label} />
}

const KEY_STATE_TONE: Record<number, StatusTone> = {
  [KEY_STATE.pending]: 'pending',
  [KEY_STATE.active]: 'done',
  [KEY_STATE.expired]: 'neutral',
  [KEY_STATE.revoked]: 'danger',
}

export function KeyStateBadge({ state, label }: { state: number; label: string }) {
  return <ToneBadge tone={KEY_STATE_TONE[state] ?? 'neutral'} label={label} />
}

const CALL_STATUS_TONE: Record<number, StatusTone> = {
  [CALL_STATUS.ok]: 'done',
  [CALL_STATUS.denied]: 'returned',
  [CALL_STATUS.error]: 'danger',
}

export function CallStatusBadge({ status, label }: { status: number; label: string }) {
  return <ToneBadge tone={CALL_STATUS_TONE[status] ?? 'neutral'} label={label} />
}
