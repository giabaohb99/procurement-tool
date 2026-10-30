import { Ban, Trash2 } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'

import { useAccessSubjectOptions } from '@/modules/hr/hooks/use-access-subject-options'
import { useJobPositions } from '@/modules/hr/hooks/use-job-positions'
import { AccessSubjectAvatar } from '@/shared/access-subject/access-subject-avatar'
import { AccessSubjectPicker } from '@/shared/access-subject/access-subject-picker'
import { EFFECT, type MixedSubject, type SubjectOption } from '@/shared/access-subject/subject-kind'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import {
  AI_SKILL_SUBJECT_KIND,
  AI_SKILL_SUBJECT_LABELS,
  AI_SKILL_SUBJECT_ORDER,
  JOB_LEVEL_SUBJECT_OPTIONS,
  NOTE_MAX,
} from '../config/ai-skill-constants'
import { useGrantSkillAccess, useRevokeSkillAccess, useSkillAccess } from '../hooks/use-ai-skill'
import type { SkillAccess } from '../types/ai-skill'

interface SkillAccessTabProps {
  targetKind: number
  targetId: number
  canWrite: boolean
}

/**
 * Tab "Ai được đọc" (G3, doc 21 §6.2): dòng quyền của một BỘ (hoặc một skill lẻ). Sáu loại đối tượng — người · phòng
 * ban (kể cả phòng con) · pháp nhân · vai trò · chức vụ · cấp bậc. Dòng CẤM tô đỏ và thắng mọi dòng cho phép.
 *
 * Cùng khuôn hộp quyền xem báo cáo (`report-access-dialog.tsx`): khối trên liệt kê + thu hồi, khối dưới gán thêm một
 * lượt nhiều đối tượng cùng chiều tác động.
 */
export function SkillAccessTab({ targetKind, targetId, canWrite }: SkillAccessTabProps) {
  const { data, isLoading } = useSkillAccess(targetKind, targetId)
  const items = data?.items ?? []
  const deny = items.filter((g) => g.effect === EFFECT.deny)
  const allow = items.filter((g) => g.effect !== EFFECT.deny)

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)]">
      <Card className="min-w-0">
        <CardHeader>
          <SectionHeading>Đang được gán</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          {isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : items.length === 0 ? (
            <p className="rounded-md border border-dashed px-3 py-6 text-center text-muted-foreground">
              Chưa gán cho ai — AI của không ai đọc được bộ này. Gán theo phòng ban hay chức vụ ở khối bên cạnh.
            </p>
          ) : (
            <>
              <GrantGroup title="Không cho phép" grants={deny} targetKind={targetKind} targetId={targetId} canWrite={canWrite} />
              <GrantGroup title="Cho phép" grants={allow} targetKind={targetKind} targetId={targetId} canWrite={canWrite} />
            </>
          )}
          <p className="text-xs text-muted-foreground">
            Không cho phép thắng tất cả. Gán theo phòng ban có đánh dấu kể cả phòng con thì người ở các phòng bên dưới
            cũng đọc được.
          </p>
        </CardContent>
      </Card>

      {canWrite && <AddGrantCard targetKind={targetKind} targetId={targetId} />}
    </div>
  )
}

function GrantGroup({
  title,
  grants,
  targetKind,
  targetId,
  canWrite,
}: {
  title: string
  grants: SkillAccess[]
  targetKind: number
  targetId: number
  canWrite: boolean
}) {
  const revoke = useRevokeSkillAccess(targetKind, targetId)
  if (grants.length === 0) return null
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground">
        {title} · {grants.length}
      </p>
      <ul className="divide-y rounded-md border">
        {grants.map((grant) => {
          const name = grant.subject_name || '(đã xóa)'
          const denied = grant.effect === EFFECT.deny
          const details = [
            grant.subject_kind_label || AI_SKILL_SUBJECT_LABELS[grant.subject_kind],
            grant.subject_kind === AI_SKILL_SUBJECT_KIND.department && grant.include_children && 'kể cả phòng con',
            grant.valid_to && `hết hạn ${formatDate(grant.valid_to)}`,
            grant.reason,
          ].filter(Boolean)
          return (
            <li key={grant.id} className={cn('flex items-center gap-3 px-3 py-2', denied && 'bg-destructive/5')}>
              <AccessSubjectAvatar subjectKind={grant.subject_kind} subjectName={name} />
              <div className="min-w-0 flex-1">
                <p className={cn('truncate font-medium', denied && 'text-destructive')} title={name}>
                  {name}
                </p>
                <p className="truncate text-xs text-muted-foreground">{details.join(' · ')}</p>
              </div>
              {denied ? (
                <Badge variant="destructive" className="shrink-0">
                  <Ban className="size-3" />
                  Cấm
                </Badge>
              ) : (
                <Badge variant="outline" className="shrink-0">
                  Cho phép
                </Badge>
              )}
              {canWrite && (
                <ConfirmIconButton
                  icon={Trash2}
                  title={`Thu hồi quyền của ${name}`}
                  confirmTitle={`Thu hồi quyền của ${name}?`}
                  confirmDescription="Thu hồi có hiệu lực trong khoảng một phút; gán lại được bất cứ lúc nào."
                  confirmLabel="Thu hồi"
                  destructive
                  disabled={revoke.isPending}
                  onConfirm={() => revoke.mutate({ id: grant.id })}
                />
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function AddGrantCard({ targetKind, targetId }: { targetKind: number; targetId: number }) {
  const grant = useGrantSkillAccess(targetKind, targetId)
  const base = useAccessSubjectOptions()
  const positions = useJobPositions()
  const [subjects, setSubjects] = useState<MixedSubject[]>([])
  const [effect, setEffect] = useState(String(EFFECT.allow))
  const [includeChildren, setIncludeChildren] = useState(true)
  const [validTo, setValidTo] = useState('')
  const [reason, setReason] = useState('')
  const busy = useRef(false)

  //  Bốn loại chung (hr sở hữu) + chức vụ + cấp bậc — hai loại riêng của Kho skill (SUBJECT_POSITION / JOB_LEVEL).
  const options = useMemo<SubjectOption[]>(
    () => [
      ...base.options,
      ...(positions.data?.items ?? []).map((p) => ({
        subject_kind: AI_SKILL_SUBJECT_KIND.position,
        subject_id: p.id,
        label: p.name,
      })),
      ...JOB_LEVEL_SUBJECT_OPTIONS,
    ],
    [base.options, positions.data],
  )
  const hasDepartment = subjects.some((s) => s.subject_kind === AI_SKILL_SUBJECT_KIND.department)

  async function handleAdd() {
    if (busy.current || subjects.length === 0) return
    busy.current = true
    try {
      await grant.mutateAsync({
        subjects,
        effect: Number(effect),
        include_children: includeChildren,
        reason: reason.trim(),
        valid_to: validTo || null,
      })
      setSubjects([])
      setReason('')
      setValidTo('')
    } catch {
      //  Toast lỗi tự động (vd ngày hết hạn đã qua).
    } finally {
      busy.current = false
    }
  }

  return (
    <Card className="min-w-0">
      <CardHeader>
        <SectionHeading>Gán thêm</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="space-y-1.5">
          <Label>Ai được đọc</Label>
          <AccessSubjectPicker
            value={subjects}
            onChange={setSubjects}
            options={options}
            loading={base.loading || positions.isLoading}
            kindLabels={AI_SKILL_SUBJECT_LABELS}
            kindOrder={AI_SKILL_SUBJECT_ORDER}
            placeholder="Thêm phòng ban · chức vụ · cấp bậc · người…"
          />
        </div>

        {hasDepartment && (
          <label className="flex items-center gap-2">
            <Checkbox checked={includeChildren} onCheckedChange={(v) => setIncludeChildren(v === true)} />
            Kể cả phòng con của phòng đã chọn
          </label>
        )}

        <div className="space-y-1.5">
          <Label>Chiều tác động</Label>
          <RadioGroup value={effect} onValueChange={setEffect} className="flex gap-4">
            <label className="flex items-center gap-2">
              <RadioGroupItem value={String(EFFECT.allow)} />
              Cho phép
            </label>
            <label className="flex items-center gap-2">
              <RadioGroupItem value={String(EFFECT.deny)} />
              Không cho phép
            </label>
          </RadioGroup>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="skill-access-valid-to">Hết hạn (không bắt buộc)</Label>
          <DatePicker id="skill-access-valid-to" value={validTo} onChange={setValidTo} placeholder="Không hết hạn" />
        </div>

        <div className="space-y-1">
          <Label htmlFor="skill-access-reason">Lý do</Label>
          <Textarea
            id="skill-access-reason"
            rows={2}
            value={reason}
            onChange={(e) => setReason(e.target.value.slice(0, NOTE_MAX))}
            placeholder="Không bắt buộc"
          />
          <p className="text-right text-xs text-muted-foreground">
            {reason.length}/{NOTE_MAX}
          </p>
        </div>

        <Button type="button" onClick={() => void handleAdd()} disabled={subjects.length === 0 || grant.isPending}>
          Gán{subjects.length > 0 ? ` (${subjects.length})` : ''}
        </Button>
      </CardContent>
    </Card>
  )
}
