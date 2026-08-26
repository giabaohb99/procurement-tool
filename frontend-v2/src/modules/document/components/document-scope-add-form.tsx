import { AlertTriangle, Plus } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartmentsByCompanies } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import type { DepartmentOfCompany } from '@/modules/hr/types/department'
import { appRoutes } from '@/shared/constants/app-routes'
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
import { SCOPE_DIM, SCOPE_MODE, type PendingScope } from '../types/document-scope'

/**
 * Khóa của một CẶP phòng ban × pháp nhân.
 *
 * Phải là cặp chứ không phải mỗi `department_id`: cùng một phòng có mặt ở nhiều
 * pháp nhân, chọn theo id phòng thì hai dòng "Phòng Kế toán" của hai công ty
 * khác nhau dính làm một.
 */
function capKey(cap: DepartmentOfCompany): string {
  return `${cap.department_id}:${cap.company_id}`
}

interface DocumentScopeAddFormProps {
  disabled?: boolean
  /**
   * Nhận **cả mẻ một lần**, kể cả khi chỉ có một dòng.
   *
   * ⚠️ Trước 20/08/2026 hàm này được gọi một lần cho MỖI pháp nhân, trong một
   * vòng lặp đồng bộ — và đó là lỗi. Nơi nhận dựng mảng mới từ `rows` đọc qua
   * closure; React chưa kịp dựng lại giữa các lượt gọi nên cả 13 lượt đều thấy
   * mảng cũ, lượt cuối ghi đè 12 lượt trước. Chọn 13 pháp nhân chỉ còn 1 dòng.
   *
   * Trả cả mẻ thì nơi nhận chỉ ghi state ĐÚNG MỘT LẦN, không còn chỗ cho lỗi đó.
   *
   * `label` là tên đọc được dựng sẵn ("Phòng Kế toán — Công ty A") để form TẠO
   * văn bản bày dòng ra ngay khi nó chưa lên máy chủ; màn sửa bỏ qua vì đọc tên
   * từ dữ liệu đã lưu.
   */
  onAdd: (rows: PendingScope[]) => void
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
  const { data: employeePage } = useEmployees({ page_size: 1000, is_active: true })

  const [dim, setDim] = useState(String(SCOPE_DIM.company))
  const [mode, setMode] = useState(String(SCOPE_MODE.include))
  //  Áp theo PHÁP NHÂN thì chọn nhiều một lượt: một quy chế thường ban hành cho
  //  cả chục pháp nhân, khai từng dòng một là mười lượt bấm y hệt nhau.
  const [companyIds, setCompanyIds] = useState<number[]>([])
  //  Áp theo PHÒNG BAN cũng chọn nhiều pháp nhân (21/08/2026): danh sách phòng
  //  ban bên dưới LỌC theo đúng những pháp nhân đang tick, và mỗi CẶP (phòng ban
  //  × pháp nhân) thành một dòng phạm vi riêng. Bản cũ bắt chọn đúng một pháp
  //  nhân rồi một phòng ban, nên áp cùng một phòng cho năm công ty là năm lượt
  //  bấm y hệt nhau.
  const [scopeCompanyIds, setScopeCompanyIds] = useState<number[]>([])
  //  Khóa của cặp: `"<department_id>:<company_id>"` — phải là cặp chứ không phải
  //  mỗi id phòng ban, vì cùng một phòng có mặt ở nhiều pháp nhân.
  const [departmentKeys, setDepartmentKeys] = useState<string[]>([])
  const [employeeId, setEmployeeId] = useState('')
  const [includeChildren, setIncludeChildren] = useState(false)

  const dimValue = Number(dim)
  const companies = companyPage?.items ?? []
  //  Chỉ hỏi khi đang ở chiều phòng ban VÀ đã tick pháp nhân — hook tự tắt khi
  //  danh sách rỗng, nên chiều khác không tốn vòng gọi nào.
  const { data: departmentLevel } = useDepartmentsByCompanies(
    dimValue === SCOPE_DIM.department ? scopeCompanyIds : [],
  )
  const capOptions = departmentLevel ?? []

  //  Pháp nhân nào đang tick mà KHÔNG có phòng ban nào.
  //
  //  Ô chọn rỗng mà chỉ nói "không tìm thấy mục nào" thì người dùng đọc ra là
  //  "hệ thống hỏng" — trong khi sự thật là pháp nhân đó chưa khai phòng ban.
  //  Ở dữ liệu thật 11/13 pháp nhân đang rơi vào ca này, nên phải gọi tên đích
  //  danh và chỉ luôn chỗ đi khai.
  const companyWithoutDepartment = companies.filter(
    (company) =>
      scopeCompanyIds.includes(company.id) &&
      !capOptions.some((cap) => cap.company_id === company.id),
  )

  const canAdd =
    (dimValue === SCOPE_DIM.company && companyIds.length > 0) ||
    (dimValue === SCOPE_DIM.department && departmentKeys.length > 0) ||
    (dimValue === SCOPE_DIM.employee && employeeId)

  function handleAdd() {
    if (dimValue === SCOPE_DIM.company) {
      //  Mỗi pháp nhân một dòng: tầng dữ liệu lưu `company_id` đơn, và có vậy
      //  mới bỏ riêng được một nơi sau này mà không phải khai lại cả cụm.
      //  Dựng đủ mảng rồi mới gọi MỘT lần — xem cảnh báo ở `onAdd`.
      onAdd(
        companyIds.map((id) => ({
          values: {
            dim: dimValue,
            mode: Number(mode),
            company_id: id,
            department_id: null,
            employee_id: null,
            include_children: includeChildren,
          },
          label: scopeLabel(dimValue, {
            company: companies.find((row) => row.id === id)?.name,
          }),
        })),
      )
      setCompanyIds([])
      setIncludeChildren(false)
      return
    }

    if (dimValue === SCOPE_DIM.department) {
      //  Mỗi CẶP một dòng, và dựng đủ mảng rồi mới gọi MỘT lần — xem cảnh báo ở
      //  `onAdd`. `company_id` lấy từ chính cặp, không phải từ một ô rời: cặp
      //  mới là thứ trả lời được "phòng Kế toán CỦA công ty nào".
      const chon = capOptions.filter((cap) => departmentKeys.includes(capKey(cap)))
      onAdd(
        chon.map((cap) => ({
          values: {
            dim: dimValue,
            mode: Number(mode),
            company_id: cap.company_id,
            department_id: cap.department_id,
            employee_id: null,
            include_children: false,
          },
          label: scopeLabel(dimValue, {
            company: cap.company_name,
            department: cap.department_name,
          }),
        })),
      )
      setDepartmentKeys([])
      return
    }

    onAdd([
      {
        values: {
          dim: dimValue,
          mode: Number(mode),
          company_id: null,
          department_id: null,
          employee_id: Number(employeeId),
          include_children: false,
        },
        label: scopeLabel(dimValue, {
          employee: (employeePage?.items ?? []).find((row) => String(row.id) === employeeId)
            ?.full_name,
        }),
      },
    ])
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
              setScopeCompanyIds([])
              setDepartmentKeys([])
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
        <>
          <div className="space-y-2">
            <Label>
              Pháp nhân<span className="text-destructive"> *</span>
            </Label>
            <MultiPicker
              value={scopeCompanyIds}
              onChange={(next) => {
                setScopeCompanyIds(next)
                //  Bỏ tick một pháp nhân thì các cặp thuộc pháp nhân đó phải rơi
                //  ra theo. Giữ lại là bấm Thêm xong sinh dòng cho một công ty
                //  vừa bị bỏ chọn — và người khai không thấy mình vừa làm gì.
                setDepartmentKeys((cu) =>
                  cu.filter((khoa) => next.includes(Number(khoa.split(':')[1]))),
                )
              }}
              options={companies.map((company) => ({
                id: company.id,
                label: company.name,
                hint: company.code,
              }))}
              placeholder="Chọn pháp nhân…"
            />
            <p className="text-xs text-muted-foreground">
              Bắt buộc: một phòng ban có mặt ở nhiều pháp nhân, thiếu ô này là
              văn bản lan sang tất cả. Chọn nhiều nơi thì ô dưới gom phòng ban
              của đúng những nơi đó.
            </p>
          </div>

          <div className="space-y-2">
            <Label>
              Phòng ban<span className="text-destructive"> *</span>
            </Label>
            <MultiPicker
              value={departmentKeys}
              onChange={setDepartmentKeys}
              options={capOptions.map((cap) => ({
                id: capKey(cap),
                label: cap.department_name,
                //  Tên pháp nhân là thứ PHÂN BIỆT hai dòng cùng tên phòng khi
                //  đang chọn nhiều nơi — nên nó phải nằm ngay trên dòng chọn.
                hint: cap.company_name,
              }))}
              placeholder={
                scopeCompanyIds.length === 0 ? 'Chọn pháp nhân trước…' : 'Chọn phòng ban…'
              }
              emptyMessage="Pháp nhân đang chọn chưa khai phòng ban nào."
              disabled={disabled || scopeCompanyIds.length === 0}
            />

            {/*  Gọi TÊN pháp nhân đang thiếu và chỉ luôn chỗ đi khai. Câu chung
                 chung "không tìm thấy mục nào" làm người dùng tưởng hệ hỏng,
                 rồi đứng đó không biết bước tiếp theo là gì. */}
            {companyWithoutDepartment.length > 0 ? (
              <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-amber-700" />
                <span>
                  <b>{companyWithoutDepartment.map((row) => row.name).join(', ')}</b> chưa khai
                  phòng ban nào nên không có gì để chọn. Khai ở{' '}
                  <Link
                    to={appRoutes.hr.departments}
                    className="font-medium underline"
                    target="_blank"
                    rel="noopener"
                  >
                    Nhân sự → Phòng ban
                  </Link>{' '}
                  (mở tab mới, khỏi mất phần đang nhập), hoặc áp theo <b>Pháp nhân</b> thay
                  vì phòng ban.
                </span>
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Mỗi phòng ban đã chọn thành một dòng phạm vi riêng, kèm đúng pháp
                nhân của nó.
              </p>
            )}
          </div>
        </>
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
