import { useMemo, useRef, useState } from 'react'

import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { useIssueKeys } from '../hooks/use-ai-usage'
import type { KeyAdminMeta } from '../types/ai-skill'

const DEFAULT_DAYS = 90

interface KeyIssueDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  meta: KeyAdminMeta
}

/**
 * Hộp «Phát khóa» (G5, K4 ai-CR-212): phát hộ khóa kết nối AI CHỈ ĐỌC cho một nhóm người hoặc cả một phòng. Khóa ở
 * trạng thái Chờ nhận; mỗi người nhận thông báo, vào Trang cá nhân bấm Nhận khóa mới thấy khóa (đúng một lần) — người
 * phát không bao giờ thấy khóa của người khác. Khóa được ghi chỉ người dùng tự tạo (Q5), nên ở đây không có ô Mức.
 */
export function KeyIssueDialog({ open, onOpenChange, meta }: KeyIssueDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Phát khóa kết nối AI</DialogTitle>
          <DialogDescription>
            Khóa chỉ đọc. Mỗi người sẽ nhận thông báo, vào Trang cá nhân bấm Nhận khóa để lấy — bạn không thấy khóa của họ.
          </DialogDescription>
        </DialogHeader>
        {open && <IssueForm meta={meta} onDone={onOpenChange} />}
      </DialogContent>
    </Dialog>
  )
}

function IssueForm({ meta, onDone }: { meta: KeyAdminMeta; onDone: (open: boolean) => void }) {
  const issue = useIssueKeys()
  //  Chọn theo HỒ SƠ nhân sự (`employee_ids`, ai-CR-215) — không cần quyền quản trị tài khoản như khi chọn theo
  //  `/api/users`. Nhân sự chưa có tài khoản đăng nhập thì máy chủ bỏ qua và báo trong `skipped`.
  const employees = useEmployees({ page_size: 1000, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })
  const [mode, setMode] = useState<'people' | 'department'>('people')
  const [employeeIds, setEmployeeIds] = useState<number[]>([])
  const [departmentId, setDepartmentId] = useState('')
  const [days, setDays] = useState(String(meta.days.includes(DEFAULT_DAYS) ? DEFAULT_DAYS : (meta.days[0] ?? DEFAULT_DAYS)))
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const busy = useRef(false)

  const peopleOptions = useMemo(
    () => (employees.data?.items ?? []).map((e) => ({ id: e.id, label: e.full_name, hint: e.code })),
    [employees.data],
  )

  async function handleIssue() {
    if (busy.current) return
    if (mode === 'people' && employeeIds.length === 0) return setError('Chọn ít nhất một người.')
    if (mode === 'people' && employeeIds.length > meta.batch_max) return setError(`Tối đa ${meta.batch_max} người một lượt.`)
    if (mode === 'department' && !Number(departmentId)) return setError('Chọn phòng ban.')
    setError('')
    busy.current = true
    try {
      await issue.mutateAsync({
        ...(mode === 'people' ? { employee_ids: employeeIds } : { department_id: Number(departmentId) }),
        days: Number(days),
        name: name.trim(),
      })
      onDone(false)
    } catch {
      //  Toast lỗi tự động (người ngoài phạm vi, phòng quá 50 người…) — giữ hộp mở để chọn lại.
    } finally {
      busy.current = false
    }
  }

  return (
    <>
      <div className="space-y-4 text-sm">
        <RadioGroup value={mode} onValueChange={(v) => setMode(v === 'department' ? 'department' : 'people')} className="flex gap-4">
          <label className="flex items-center gap-2">
            <RadioGroupItem value="people" />
            Chọn người
          </label>
          <label className="flex items-center gap-2">
            <RadioGroupItem value="department" />
            Cả phòng
          </label>
        </RadioGroup>

        {mode === 'people' ? (
          <div className="space-y-1.5">
            <Label>Người nhận (tối đa {meta.batch_max})</Label>
            <MultiPicker
              value={employeeIds}
              onChange={setEmployeeIds}
              options={peopleOptions}
              placeholder={employees.isLoading ? 'Đang tải nhân sự…' : 'Chọn người nhận'}
              searchPlaceholder="Tìm theo tên hoặc mã…"
              emptyMessage="Không tìm thấy nhân sự nào."
            />
          </div>
        ) : (
          <div className="space-y-1.5">
            <Label>Phòng ban</Label>
            <Select value={departmentId} onValueChange={setDepartmentId}>
              <SelectTrigger className="w-full" aria-label="Phòng ban nhận khóa">
                <SelectValue placeholder="Chọn phòng ban" />
              </SelectTrigger>
              <SelectContent>
                {(departments?.items ?? [])
                  .filter((d) => d.is_active)
                  .map((d) => (
                    <SelectItem key={d.id} value={String(d.id)}>
                      {d.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">Phòng quá {meta.batch_max} người thì phát theo từng nhóm người.</p>
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Hạn dùng</Label>
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="w-full" aria-label="Hạn dùng">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {meta.days.map((d) => (
                  <SelectItem key={d} value={String(d)}>
                    {d} ngày
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="key-issue-name">Tên khóa</Label>
            <Input
              id="key-issue-name"
              value={name}
              maxLength={80}
              onChange={(e) => setName(e.target.value)}
              placeholder="Khóa phòng Thu mua"
            />
          </div>
        </div>

        {error && <p className="text-destructive">{error}</p>}
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={() => onDone(false)}>
          Hủy
        </Button>
        <Button type="button" onClick={() => void handleIssue()} disabled={issue.isPending}>
          Phát khóa{mode === 'people' && employeeIds.length > 0 ? ` (${employeeIds.length})` : ''}
        </Button>
      </DialogFooter>
    </>
  )
}
