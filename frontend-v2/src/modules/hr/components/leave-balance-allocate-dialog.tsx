import { CalendarPlus } from 'lucide-react'
import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import type { LeaveBalanceAllocatePayload } from '../api/leave-api'
import { EmployeeFilterSelect } from './employee-filter-select'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { useAllocateLeaveBalance, useLeaveTypes } from '../hooks/use-leave'
import { useSingleFlight } from '../hooks/use-single-flight'
import { EMPLOYMENT_TYPE_FILTER_OPTIONS, JOB_LEVEL_FILTER_OPTIONS } from '../types/employee-codes'
import { FILTER_ANY, toFilterId } from '../utils/employee-filter-id'

interface LeaveBalanceAllocateDialogProps {
  /** Năm đang xem trên màn — hộp KHÓA theo năm này, không cho đổi trong hộp. `null` = đóng. */
  year: number | null
  onClose: () => void
}

/**
 * Hộp CẤP QUỸ NĂM có lọc (duoc-CR-717, D9a) — thay nút bấm-là-chạy cũ. Mọi ô bỏ trống = như nút
 * cũ (mọi loại có trừ quỹ × mọi nhân sự đang làm trong phạm vi). Ô lọc chỉ THU HẸP; luật "chỉ tạo
 * dòng còn thiếu" giữ nguyên nên bấm lại không nhân đôi quỹ. Kết quả (số dòng thêm, người thiếu
 * ngày vào làm) báo bằng thông báo của `useAllocateLeaveBalance` như trước.
 */
export function LeaveBalanceAllocateDialog({ year, onClose }: LeaveBalanceAllocateDialogProps) {
  return (
    <Dialog open={year !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        {/*  Thân hộp là component riêng để mỗi lần MỞ là một bộ ô mới — Radix gỡ nội dung khi
             đóng, nên lần mở sau không mang lọc của lần trước (cấp nhầm cho đúng một phòng). */}
        {year !== null && <AllocateForm year={year} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  )
}

function AllocateForm({ year, onClose }: { year: number; onClose: () => void }) {
  const { can } = usePermission()
  const canReadCompany = can('company', 'read')
  const canReadDepartment = can('department', 'read')
  const allocate = useAllocateLeaveBalance()
  const runOnce = useSingleFlight()

  const [leaveTypeIds, setLeaveTypeIds] = useState<number[]>([])
  const [companyId, setCompanyId] = useState(FILTER_ANY)
  const [departmentId, setDepartmentId] = useState(FILTER_ANY)
  const [employmentType, setEmploymentType] = useState(FILTER_ANY)
  const [jobLevel, setJobLevel] = useState(FILTER_ANY)

  const { data: typeData } = useLeaveTypes()
  //  Chỉ loại CÓ trừ quỹ mới có dòng quỹ để cấp — bày loại không trừ quỹ là mời chọn một thứ
  //  backend sẽ lặng lẽ bỏ qua.
  const typeOptions = useMemo(
    () =>
      (typeData?.items ?? [])
        .filter((t) => t.counts_balance)
        .map((t) => ({ id: t.id, label: t.name })),
    [typeData],
  )
  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: canReadCompany })
  //  ⚠️ Phòng ban KHÔNG lọc theo pháp nhân (review M5): phòng ban dùng chung (`company_id = 0`, không có dòng
  //  `tab_department_company`) nên `?company_id=` trả rỗng. Backend tự giao hai ô lọc lúc cấp.
  const { data: departments } = useDepartments({ page_size: 500, is_active: true }, { enabled: canReadDepartment })

  const submit = () =>
    runOnce((release) => {
      const payload: LeaveBalanceAllocatePayload = { year }
      if (leaveTypeIds.length) payload.leave_type_ids = leaveTypeIds
      const filters = {
        company_id: toFilterId(companyId),
        department_id: toFilterId(departmentId),
        employment_type: toFilterId(employmentType),
        job_level: toFilterId(jobLevel),
      }
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined) payload[key as keyof typeof filters] = value
      }
      allocate.mutate(payload, { onSuccess: onClose, onSettled: release })
    })

  return (
    <>
      <DialogHeader>
        <DialogTitle>Cấp quỹ phép năm {year}</DialogTitle>
        <DialogDescription>
          Chỉ tạo dòng quỹ còn thiếu — người đã có quỹ loại đó giữ nguyên, bấm lại không nhân đôi
          số ngày. Ô để trống là không lọc theo ô đó.
        </DialogDescription>
      </DialogHeader>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5 sm:col-span-2">
          <Label>Loại nghỉ</Label>
          <MultiPicker<number>
            value={leaveTypeIds}
            onChange={setLeaveTypeIds}
            options={typeOptions}
            placeholder="Mọi loại nghỉ có trừ quỹ"
            searchPlaceholder="Tìm loại nghỉ"
            emptyMessage="Không có loại nghỉ nào có trừ quỹ."
          />
        </div>
        {canReadCompany && (
          <EmployeeFilterSelect
            id="allocate-company"
            label="Pháp nhân"
            value={companyId}
            onChange={setCompanyId}
            anyLabel="Mọi pháp nhân"
            options={(companies?.items ?? []).map((c) => ({ value: c.id, label: c.name }))}
          />
        )}
        {canReadDepartment && (
          <EmployeeFilterSelect
            id="allocate-department"
            label="Phòng ban"
            value={departmentId}
            onChange={setDepartmentId}
            anyLabel="Mọi phòng ban"
            options={(departments?.items ?? []).map((d) => ({ value: d.id, label: d.name }))}
          />
        )}
        <EmployeeFilterSelect
          id="allocate-employment-type"
          label="Hình thức nhân viên"
          value={employmentType}
          onChange={setEmploymentType}
          anyLabel="Mọi hình thức"
          options={EMPLOYMENT_TYPE_FILTER_OPTIONS}
        />
        <EmployeeFilterSelect
          id="allocate-job-level"
          label="Cấp bậc"
          value={jobLevel}
          onChange={setJobLevel}
          anyLabel="Mọi cấp bậc"
          options={JOB_LEVEL_FILTER_OPTIONS}
        />
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>
          Hủy
        </Button>
        <Button type="button" onClick={submit} disabled={allocate.isPending}>
          <CalendarPlus className="size-4" />
          Cấp quỹ
        </Button>
      </DialogFooter>
    </>
  )
}
