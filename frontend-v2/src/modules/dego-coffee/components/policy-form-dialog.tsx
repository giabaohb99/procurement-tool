import { useState } from 'react'

import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useCoffeeMeta, useCreatePolicy, useUpdatePolicy } from '../hooks/use-coffee'
import type { CoffeePolicy } from '../types/coffee'
import { CoffeeDialogShell } from './coffee-dialog-shell'
import { PointsInput } from './points-input'

interface PolicyFormDialogProps {
  /** Có = SỬA dòng chưa qua kỳ cấp; không = thêm dòng mới. */
  policy?: CoffeePolicy
  onClose: () => void
}

/**
 * Thêm/Sửa DÒNG chính sách (A-01). Chỉ dòng CHƯA được kỳ cấp phát dùng tới mới
 * sửa được (backend chặn thật); dòng đã dùng thì đổi mức = thêm dòng hiệu lực
 * mới — để "mức của tháng trước" tra lại được.
 */
export function PolicyFormDialog({ policy, onClose }: PolicyFormDialogProps) {
  const { data: meta } = useCoffeeMeta()
  const createPolicy = useCreatePolicy()
  const updatePolicy = useUpdatePolicy()
  const [levelCode, setLevelCode] = useState(policy ? String(policy.level_code) : '')
  //  Điểm là SỐ NGUYÊN — PointsInput tự chèn dấu ngăn nghìn NGAY LÚC GÕ (200.000).
  const [points, setPoints] = useState(policy?.monthly_points ?? 0)
  const [effectiveFrom, setEffectiveFrom] = useState(policy?.effective_from ?? '')
  const [note, setNote] = useState(policy?.note ?? '')
  const [error, setError] = useState('')

  const dirty = policy
    ? levelCode !== String(policy.level_code) ||
      points !== policy.monthly_points ||
      effectiveFrom !== policy.effective_from ||
      note !== policy.note
    : Boolean(levelCode || points || effectiveFrom || note)
  const pending = createPolicy.isPending || updatePolicy.isPending

  function handleConfirm() {
    if (!levelCode || !points || !effectiveFrom) {
      setError('Điền đủ Cấp, Mức điểm và Ngày hiệu lực.')
      return
    }
    setError('')
    const body = {
      company_id: policy?.company_id ?? 0,
      level_code: Number(levelCode),
      monthly_points: points,
      effective_from: effectiveFrom,
      note,
    }
    if (policy) {
      updatePolicy.mutate({ id: policy.id, body }, { onSuccess: onClose })
    } else {
      createPolicy.mutate(body, { onSuccess: onClose })
    }
  }

  return (
    <CoffeeDialogShell
      title={policy ? `Sửa mức — ${policy.level_label}` : 'Thêm dòng chính sách'}
      description={
        policy
          ? 'Dòng này chưa được kỳ cấp phát nào dùng tới nên còn sửa được.'
          : 'Đổi mức của một cấp = thêm dòng hiệu lực mới — dòng cũ giữ nguyên để tra được mức của các kỳ trước.'
      }
      dirty={dirty}
      pending={pending}
      confirmLabel={policy ? 'Lưu' : 'Thêm dòng'}
      onConfirm={handleConfirm}
      onClose={onClose}
    >
      <div className="flex flex-col gap-1.5">
        <Label>
          Cấp phúc lợi
          <RequiredMark />
        </Label>
        <Select value={levelCode} onValueChange={setLevelCode}>
          <SelectTrigger>
            <SelectValue placeholder="Chọn cấp" />
          </SelectTrigger>
          <SelectContent>
            {(meta?.levels ?? []).map((option) => (
              <SelectItem key={option.value} value={String(option.value)}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="policy-points">
          Mức điểm mỗi tháng
          <RequiredMark />
        </Label>
        <PointsInput id="policy-points" value={points} onChange={setPoints} placeholder="vd 200.000" />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="policy-from">
          Hiệu lực từ ngày
          <RequiredMark />
        </Label>
        <Input
          id="policy-from"
          type="date"
          value={effectiveFrom}
          onChange={(e) => setEffectiveFrom(e.target.value)}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="policy-note">Ghi chú</Label>
        <Input id="policy-note" value={note} onChange={(e) => setNote(e.target.value)} />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </CoffeeDialogShell>
  )
}
