import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
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
import { useCoffeeMeta, useCreateMember, useUpdateMember } from '../hooks/use-coffee'
import type { CoffeeMember } from '../types/coffee'
import { CoffeeDialogShell } from './coffee-dialog-shell'

interface MemberFormDialogProps {
  /** Có = sửa cấp/trạng thái; không = gán người mới vào chương trình. */
  member?: CoffeeMember
  onClose: () => void
}

/** Gán cấp cho nhân sự (B-01) / đổi cấp & trạng thái hưởng. */
export function MemberFormDialog({ member, onClose }: MemberFormDialogProps) {
  const { can } = usePermission()
  const { data: meta } = useCoffeeMeta()
  //  Mượn danh bạ của phân hệ Nhân sự — tắt lời gọi khi thiếu `employee.read`
  //  để không ăn toast 403 lúc mở dialog (bài học tab Công nợ của NCC).
  const { data: employees } = useEmployees(
    { page_size: 500 },
    { enabled: !member && can('employee', 'read') },
  )
  const createMember = useCreateMember()
  const updateMember = useUpdateMember()

  const [employeeId, setEmployeeId] = useState('')
  const [levelCode, setLevelCode] = useState(member ? String(member.level_code) : '')
  const [status, setStatus] = useState(member ? String(member.status) : '')
  const [error, setError] = useState('')

  const dirty = member
    ? levelCode !== String(member.level_code) || status !== String(member.status)
    : Boolean(employeeId || levelCode)
  const pending = createMember.isPending || updateMember.isPending

  function handleConfirm() {
    if (member) {
      updateMember.mutate(
        { id: member.id, body: { level_code: Number(levelCode), status: Number(status) } },
        { onSuccess: onClose },
      )
      return
    }
    if (!employeeId || !levelCode) {
      setError('Chọn nhân sự và cấp phúc lợi.')
      return
    }
    setError('')
    createMember.mutate(
      { employee_id: Number(employeeId), level_code: Number(levelCode) },
      { onSuccess: onClose },
    )
  }

  return (
    <CoffeeDialogShell
      title={member ? `Sửa thành viên — ${member.employee_name}` : 'Thêm thành viên'}
      description={
        member
          ? 'Chuyển sang «Đã nghỉ» sẽ THU HỒI toàn bộ số dư (có dòng sổ) và khóa ví.'
          : 'Người được gán sẽ nhận điểm từ kỳ cấp phát kế tiếp.'
      }
      dirty={dirty}
      pending={pending}
      confirmLabel={member ? 'Lưu' : 'Thêm'}
      onConfirm={handleConfirm}
      onClose={onClose}
    >
      {!member && (
        <div className="flex flex-col gap-1.5">
          <Label>
            Nhân sự
            <RequiredMark />
          </Label>
          <SearchSelect
            value={employeeId}
            onChange={setEmployeeId}
            searchInTrigger
            placeholder="Tìm theo tên / mã nhân viên"
            options={(employees?.items ?? []).map((e) => ({
              value: String(e.id),
              label: `${e.code} — ${e.full_name}`,
            }))}
          />
        </div>
      )}
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
      {member && (
        <div className="flex flex-col gap-1.5">
          <Label>Trạng thái hưởng</Label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(meta?.member_statuses ?? []).map((option) => (
                <SelectItem key={option.value} value={String(option.value)}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </CoffeeDialogShell>
  )
}
