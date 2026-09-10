import { useState } from 'react'

import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { useCoffeeMembers, useResolvePosOrder } from '../hooks/use-coffee'
import type { PosOrderRow } from '../types/coffee'
import { formatPoints } from '../utils/format-points'
import { CoffeeDialogShell } from './coffee-dialog-shell'

interface ResolveOrderDialogProps {
  order: PosOrderRow
  onClose: () => void
}

/**
 * Xử lý đơn CHƯA KHỚP (D-02): gán người (sinh dòng tiêu) hoặc bỏ qua có lý do.
 * Hệ không đoán người — quyết định là của người xử lý, có nhật ký.
 */
export function ResolveOrderDialog({ order, onClose }: ResolveOrderDialogProps) {
  const { data: members } = useCoffeeMembers({ page_size: '500' })
  const resolve = useResolvePosOrder()
  const [mode, setMode] = useState<'assign' | 'ignore'>('assign')
  const [employeeId, setEmployeeId] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  const dirty = Boolean(employeeId || reason)

  function handleConfirm() {
    if (mode === 'assign' && !employeeId) {
      setError('Chọn nhân sự để gán đơn.')
      return
    }
    if (mode === 'ignore' && !reason.trim()) {
      setError('Bỏ qua đơn phải có lý do.')
      return
    }
    setError('')
    resolve.mutate(
      {
        id: order.id,
        employee_id: mode === 'assign' ? Number(employeeId) : 0,
        reason: reason.trim(),
      },
      { onSuccess: onClose },
    )
  }

  return (
    <CoffeeDialogShell
      title={`Xử lý đơn ${order.pos_code}`}
      description={`${order.purchase_date} — trả bằng điểm: ${formatPoints(order.points_paid)}. Đơn không khớp được ai vì khách trên bill chưa ghép với nhân sự nào.`}
      dirty={dirty}
      pending={resolve.isPending}
      confirmLabel={mode === 'assign' ? 'Gán và trừ điểm' : 'Bỏ qua đơn'}
      onConfirm={handleConfirm}
      onClose={onClose}
    >
      <div className="flex flex-col gap-1.5">
        <Label>Cách xử lý</Label>
        <Select value={mode} onValueChange={(v) => setMode(v as 'assign' | 'ignore')}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="assign">Gán cho một nhân sự (sinh dòng tiêu)</SelectItem>
            <SelectItem value="ignore">Bỏ qua — không trừ ai (cần lý do)</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {mode === 'assign' && (
        <div className="flex flex-col gap-1.5">
          <Label>Nhân sự</Label>
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
      )}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="resolve-reason">{mode === 'ignore' ? 'Lý do' : 'Ghi chú (tùy chọn)'}</Label>
        <Textarea
          id="resolve-reason"
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </CoffeeDialogShell>
  )
}
