import { useState } from 'react'

import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useAdjustLedger, useCoffeeMembers } from '../hooks/use-coffee'
import { CoffeeDialogShell } from './coffee-dialog-shell'
import { PointsInput } from './points-input'

interface AdjustDialogProps {
  onClose: () => void
}

/**
 * Điều chỉnh tay (A-07): ±điểm, LÝ DO BẮT BUỘC — thành một dòng sổ có người ghi,
 * không có đường sửa số dư nào không để lại dấu vết.
 */
export function AdjustDialog({ onClose }: AdjustDialogProps) {
  const { data: members } = useCoffeeMembers({ page_size: '500' })
  const adjust = useAdjustLedger()
  const [employeeId, setEmployeeId] = useState('')
  //  Cộng/Trừ chọn bằng ô riêng — khỏi bắt người dùng gõ dấu âm.
  const [direction, setDirection] = useState<'add' | 'subtract'>('add')
  const [points, setPoints] = useState(0)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  const dirty = Boolean(employeeId || points || reason)

  function handleConfirm() {
    if (!employeeId || !points || !reason.trim()) {
      setError('Chọn người, nhập số điểm và lý do.')
      return
    }
    setError('')
    adjust.mutate(
      {
        employee_id: Number(employeeId),
        points: direction === 'subtract' ? -points : points,
        reason: reason.trim(),
      },
      { onSuccess: onClose },
    )
  }

  return (
    <CoffeeDialogShell
      title="Điều chỉnh điểm"
      description="Ghi một dòng ĐIỀU CHỈNH vào sổ (cộng bù / trừ nhầm) — dòng cũ không sửa được."
      dirty={dirty}
      pending={adjust.isPending}
      confirmLabel="Ghi dòng điều chỉnh"
      onConfirm={handleConfirm}
      onClose={onClose}
    >
      <div className="flex flex-col gap-1.5">
        <Label>
          Nhân sự
          <RequiredMark />
        </Label>
        <SearchSelect
          value={employeeId}
          onChange={setEmployeeId}
          searchInTrigger
          placeholder="Tìm thành viên"
          options={(members?.items ?? []).map((m) => ({
            value: String(m.employee_id),
            label: `${m.employee_code} — ${m.employee_name}`,
          }))}
        />
      </div>
      <div className="grid grid-cols-[140px_minmax(0,1fr)] gap-2">
        <div className="flex flex-col gap-1.5">
          <Label>Chiều</Label>
          <Select value={direction} onValueChange={(v) => setDirection(v as 'add' | 'subtract')}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="add">Cộng thêm</SelectItem>
              <SelectItem value="subtract">Trừ bớt</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="adjust-points">
            Số điểm
            <RequiredMark />
          </Label>
          <PointsInput id="adjust-points" value={points} onChange={setPoints} placeholder="vd 10.000" />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="adjust-reason">
          Lý do
          <RequiredMark />
        </Label>
        <Textarea
          id="adjust-reason"
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Vì sao phải điều chỉnh — người sau đọc sổ phải hiểu"
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </CoffeeDialogShell>
  )
}
