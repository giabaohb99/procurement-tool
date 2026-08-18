import { Plus } from 'lucide-react'
import { useState } from 'react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { scopeLabel } from '../helpers/scope-label'
import { useScopeOptions } from '../hooks/use-document-scopes'
import {
  SCOPE_DIM,
  SCOPE_MODE,
  type DocumentScopeInput,
} from '../types/document-scope'

interface DocumentScopeAddFormProps {
  disabled?: boolean
  /**
   * `label` là tên đọc được của đối tượng vừa chọn ("Phòng Kế toán — Công ty A").
   *
   * Có nó thì form TẠO văn bản bày được dòng vừa khai ra ngay, dù dòng đó chưa
   * gửi lên máy chủ nên chưa có tên do backend trả về. Màn sửa bỏ qua tham số
   * này vì đọc tên từ dữ liệu đã lưu.
   *
   * Chọn nhiều pháp nhân một lượt thì hàm này được gọi **nhiều lần**, mỗi pháp
   * nhân một dòng — tầng dữ liệu lưu mỗi dòng đúng một đối tượng.
   */
  onAdd: (values: DocumentScopeInput, label: string) => void
}

/**
 * Khai một dòng phạm vi áp dụng (F01–F04).
 *
 * Ô **pháp nhân luôn hiện** khi chọn chiều phòng ban, và không bỏ trống được:
 * một phòng ban có mặt ở 13 pháp nhân, khai trơ trọi "phòng Kế toán" là văn bản
 * lan sang cả 13 công ty. Backend chặn ở cả tầng nhập liệu lẫn tầng dữ liệu, ở
 * đây chỉ là không bày ra một lựa chọn không bao giờ lưu được.
 */
export function DocumentScopeAddForm({ disabled = false, onAdd }: DocumentScopeAddFormProps) {
  const { data: options } = useScopeOptions()
  //  Cùng tham số với ô "Pháp nhân ban hành" nên dùng chung một lượt gọi trong
  //  bộ nhớ đệm — lệch tham số là gọi lại y hệt lần thứ hai.
  const { data: companyPage } = useCompanies({ page_size: 200, is_active: true })
  const { data: departmentPage } = useDepartments({ page_size: 500 })
  const { data: employeePage } = useEmployees({ page_size: 1000, is_active: true })

  const [dim, setDim] = useState(String(SCOPE_DIM.company))
  const [mode, setMode] = useState(String(SCOPE_MODE.include))
  //  Áp theo PHÁP NHÂN thì chọn nhiều một lượt: một quy chế thường ban hành cho
  //  cả chục pháp nhân, khai từng dòng một là mười lượt bấm y hệt nhau.
  const [companyIds, setCompanyIds] = useState<number[]>([])
  //  Áp theo PHÒNG BAN thì vẫn đúng MỘT pháp nhân — nó là ô định danh phòng ban
  //  ("phòng Kế toán của công ty nào"), không phải danh sách nơi áp dụng.
  const [companyId, setCompanyId] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [employeeId, setEmployeeId] = useState('')
  const [includeChildren, setIncludeChildren] = useState(false)

  const dimValue = Number(dim)
  const companies = companyPage?.items ?? []
  const canAdd =
    (dimValue === SCOPE_DIM.company && companyIds.length > 0) ||
    (dimValue === SCOPE_DIM.department && departmentId && companyId) ||
    (dimValue === SCOPE_DIM.employee && employeeId)

  function handleAdd() {
    if (dimValue === SCOPE_DIM.company) {
      //  Mỗi pháp nhân một dòng: tầng dữ liệu lưu `company_id` đơn, và có vậy
      //  mới bỏ riêng được một nơi sau này mà không phải khai lại cả cụm.
      for (const id of companyIds) {
        onAdd(
          {
            dim: dimValue,
            mode: Number(mode),
            company_id: id,
            department_id: null,
            employee_id: null,
            include_children: includeChildren,
          },
          scopeLabel(dimValue, { company: companies.find((row) => row.id === id)?.name }),
        )
      }
      setCompanyIds([])
      setIncludeChildren(false)
      return
    }

    const label = scopeLabel(dimValue, {
      company: companies.find((row) => String(row.id) === companyId)?.name,
      department: (departmentPage?.items ?? []).find((row) => String(row.id) === departmentId)
        ?.name,
      employee: (employeePage?.items ?? []).find((row) => String(row.id) === employeeId)
        ?.full_name,
    })

    onAdd(
      {
        dim: dimValue,
        mode: Number(mode),
        company_id: dimValue === SCOPE_DIM.employee ? null : Number(companyId) || null,
        department_id: dimValue === SCOPE_DIM.department ? Number(departmentId) : null,
        employee_id: dimValue === SCOPE_DIM.employee ? Number(employeeId) : null,
        include_children: false,
      },
      label,
    )
    setCompanyId('')
    setDepartmentId('')
    setEmployeeId('')
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Cách áp</Label>
          <Select value={mode} onValueChange={setMode}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(options?.modes ?? []).map((item) => (
                <SelectItem key={item.value} value={String(item.value)}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Áp theo</Label>
          <Select
            value={dim}
            onValueChange={(next) => {
              setDim(next)
              //  Đổi chiều là đổi cả bộ ô bên dưới — giữ lại giá trị cũ thì gửi
              //  đi một dòng nửa nọ nửa kia.
              setCompanyIds([])
              setCompanyId('')
              setDepartmentId('')
              setEmployeeId('')
              setIncludeChildren(false)
            }}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(options?.dims ?? []).map((item) => (
                <SelectItem key={item.value} value={String(item.value)}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {dimValue === SCOPE_DIM.company && (
        <div className="space-y-2">
          <Label>
            Pháp nhân<span className="text-destructive"> *</span>
          </Label>
          <MultiPicker
            value={companyIds}
            onChange={setCompanyIds}
            options={companies.map((company) => ({
              id: company.id,
              label: company.name,
              hint: company.code,
            }))}
            placeholder="Chọn pháp nhân…"
          />
          <p className="text-xs text-muted-foreground">
            Chọn được nhiều nơi một lượt — mỗi nơi thành một dòng phạm vi riêng.
          </p>
        </div>
      )}

      {dimValue === SCOPE_DIM.department && (
        <div className="space-y-2">
          <Label>
            Pháp nhân<span className="text-destructive"> *</span>
          </Label>
          <Select value={companyId} onValueChange={setCompanyId}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Chọn pháp nhân…" />
            </SelectTrigger>
            <SelectContent>
              {companies.map((company) => (
                <SelectItem key={company.id} value={String(company.id)}>
                  {company.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Bắt buộc: một phòng ban có mặt ở nhiều pháp nhân, thiếu ô này là văn
            bản lan sang tất cả.
          </p>
        </div>
      )}

      {dimValue === SCOPE_DIM.department && (
        <div className="space-y-2">
          <Label>
            Phòng ban<span className="text-destructive"> *</span>
          </Label>
          <Select value={departmentId} onValueChange={setDepartmentId}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Chọn phòng ban…" />
            </SelectTrigger>
            <SelectContent>
              {(departmentPage?.items ?? []).map((department) => (
                <SelectItem key={department.id} value={String(department.id)}>
                  {department.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {dimValue === SCOPE_DIM.employee && (
        <div className="space-y-2">
          <Label>
            Nhân sự<span className="text-destructive"> *</span>
          </Label>
          <Select value={employeeId} onValueChange={setEmployeeId}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Chọn người…" />
            </SelectTrigger>
            <SelectContent>
              {(employeePage?.items ?? []).map((employee) => (
                <SelectItem key={employee.id} value={String(employee.id)}>
                  {employee.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {dimValue === SCOPE_DIM.company && (
        <div className="flex items-start gap-3">
          <Checkbox
            id="scope-include-children"
            className="mt-0.5"
            checked={includeChildren}
            onCheckedChange={(checked) => setIncludeChildren(checked === true)}
          />
          <div className="space-y-1">
            <Label htmlFor="scope-include-children">Gồm cả đơn vị con</Label>
            <p className="text-sm text-muted-foreground">
              Áp cho mọi công ty con — kể cả công ty mở sau này.
            </p>
          </div>
        </div>
      )}

      <Button type="button" variant="outline" disabled={disabled || !canAdd} onClick={handleAdd}>
        <Plus className="size-4" />
        Thêm dòng phạm vi
      </Button>
    </div>
  )
}
