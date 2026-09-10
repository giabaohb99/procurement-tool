import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Save, Stamp } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { companyApi } from '@/modules/hr/api/company-api'
import { employeeApi } from '@/modules/hr/api/employee-api'
import { queryKeys } from '@/shared/constants/query-keys'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Switch } from '@/shared/ui/switch'
import { useSaveSealClerks } from '../hooks/use-seal-clerks'

export function SealClerkFormPage() {
  const navigate = useNavigate()
  const save = useSaveSealClerks()

  const [employeeId, setEmployeeId] = useState(0)
  const [companyIds, setCompanyIds] = useState<number[]>([])
  const [isHead, setIsHead] = useState(false)

  const { data: employees } = useQuery({
    queryKey: queryKeys.hr.employees({ page_size: 1000, is_active: true }),
    queryFn: () => employeeApi.list({ page_size: 1000, is_active: true }),
  })
  const { data: companies } = useQuery({
    queryKey: queryKeys.hr.companies({ page_size: 500, is_active: true }),
    queryFn: () => companyApi.list({ page_size: 500, is_active: true }),
  })

  const companyOptions = useMemo(
    () => (companies?.items ?? []).map((c) => ({
      id: c.id, label: c.name, hint: c.tax_code, avatar: c.logo,
    })),
    [companies],
  )

  const back = () => navigate(appRoutes.approvalSeal.clerks)

  const handleSave = () => {
    if (!employeeId) {
      toast.error('Vui lòng chọn văn thư')
      return
    }
    if (companyIds.length === 0 && !isHead) {
      toast.error('Chọn ít nhất một công ty, hoặc bật "Văn thư tổng"')
      return
    }
    save.mutate(
      { employee_id: employeeId, company_ids: companyIds, is_head: isHead },
      { onSuccess: back },
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={back} title="Quay lại">
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Phân công văn thư</h1>
            <p className="text-sm text-muted-foreground">
              Chọn văn thư và các công ty họ phụ trách đóng dấu.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={back}>
            Hủy
          </Button>
          <Button onClick={handleSave} disabled={save.isPending}>
            <Save className="mr-1.5 size-4" />
            {save.isPending ? 'Đang lưu…' : 'Lưu'}
          </Button>
        </div>
      </div>

      <Card className="space-y-6 p-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <Stamp className="size-5 text-primary" />
          Thông tin phân công
        </h2>

        <div className="space-y-2">
          <label className="text-sm font-medium leading-none">
            Văn thư
            <RequiredMark />
          </label>
          <select
            value={employeeId ? String(employeeId) : ''}
            onChange={(e) => setEmployeeId(Number(e.target.value) || 0)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs focus-visible:ring-1 focus-visible:ring-ring focus-visible:outline-none"
          >
            <option value="">-- Chọn nhân sự làm văn thư --</option>
            {(employees?.items ?? []).map((emp) => (
              <option key={emp.id} value={String(emp.id)}>
                {emp.full_name}
                {emp.code ? ` · ${emp.code}` : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label className="flex items-center justify-between text-sm font-medium leading-none">
            <span>Công ty phụ trách</span>
            <span className="text-xs font-normal text-muted-foreground">
              Đã chọn {companyIds.length} công ty
            </span>
          </label>
          <MultiPicker<number>
            options={companyOptions}
            value={companyIds}
            onChange={setCompanyIds}
            placeholder="Chọn công ty phụ trách"
            searchPlaceholder="Tìm theo tên hoặc mã số thuế…"
            emptyMessage="Không tìm thấy công ty nào."
            contentClassName="w-[min(34rem,92vw)]"
            chipsInTrigger
            clearInTrigger
          />
          <p className="text-xs text-muted-foreground">
            Văn thư sẽ nhận các phiếu đóng dấu MỘT công ty của những công ty này (sau khi TBP duyệt).
          </p>
        </div>

        <div className="flex items-start justify-between gap-4 rounded-lg border p-4">
          <div>
            <div className="text-sm font-medium">Văn thư tổng</div>
            <p className="text-xs text-muted-foreground">
              Phụ trách các phiếu cần dấu của NHIỀU công ty (đa công ty). Có thể bật kèm phụ trách công ty riêng ở trên.
            </p>
          </div>
          <Switch checked={isHead} onCheckedChange={setIsHead} />
        </div>
      </Card>
    </div>
  )
}
