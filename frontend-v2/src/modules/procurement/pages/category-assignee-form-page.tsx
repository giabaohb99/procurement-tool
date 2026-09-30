import { ArrowLeft, Save, UserCheck, Users } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { httpClient } from '@/core/api/http-client'
import { usePermission } from '@/core/authorization/use-permission'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import type { CategoryAssignee, CategoryAssigneeBulkPayload } from '../types/category-assignee'
import {
  assigneeOptions,
  validateAssigneePair,
  type AssigneeEmployee,
  type AssigneeOption,
} from '../utils/category-assignee-rules'
import { DEFAULT_PURCHASING_LABEL } from '../utils/handling-dept-display'

interface Option {
  value: number
  label: string
}

/**
 * Chữ mờ của ô Phòng áp dụng khi chưa chọn — bao-CR-524: không còn mục ảo «Thu mua chung»; để
 * trống thì backend ghi phòng thu mua mặc định (phòng THẬT «Sản xuất -Thu mua» trong danh mục).
 */
const DEPARTMENT_PLACEHOLDER = 'Để trống = phòng thu mua mặc định'

export function CategoryAssigneeFormPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { can } = usePermission()

  const [itemGroups, setItemGroups] = useState<Option[]>([])
  //  bao-CR-527: giữ cả mã trạng thái + cờ hoạt động để ô chọn chỉ mời người «Chính thức».
  const [employees, setEmployees] = useState<AssigneeEmployee[]>([])
  //  Toàn bộ dòng phân công của MỌI phòng: cùng một phân loại có thể có một dòng
  //  chung và một dòng riêng cho từng phòng, nên map «phân loại → id dòng» phải
  //  tính theo phòng đang chọn chứ không gộp cả bảng.
  const [rows, setRows] = useState<CategoryAssignee[]>([])

  const [selectedCatIds, setSelectedCatIds] = useState<number[]>([])
  const [primaryId, setPrimaryId] = useState<number | 0>(0)
  const [backupId, setBackupId] = useState<number | 0>(0)
  //  bao-CR-414 GĐ2: phòng áp dụng. Đọc từ `?dept=` khi Sửa. 0 = chưa chọn → backend ghi phòng
  //  thu mua mặc định (bao-CR-524).
  const [departmentId, setDepartmentId] = useState<number>(0)

  const [saving, setSaving] = useState(false)

  //  Danh mục phòng ban cho ô chọn; thiếu quyền thì ô trống và phân công rơi về phòng thu mua
  //  mặc định (bao-CR-524) — y hệt trước GĐ2.
  const { data: departmentsData } = useDepartments(
    { page_size: 500 },
    { enabled: can('department', 'read') },
  )
  const departments = useMemo<Option[]>(
    () => (departmentsData?.items ?? []).map((d) => ({ value: d.id, label: d.name })),
    [departmentsData],
  )

  const rowByCat = useMemo<Record<number, number>>(() => {
    const map: Record<number, number> = {}
    rows
      .filter((x) => (x.department_id || 0) === departmentId)
      .forEach((x) => {
        map[x.item_group_id] = x.id
      })
    return map
  }, [rows, departmentId])

  const editCatId = Number(searchParams.get('cats')) || 0
  const editRowId = editCatId ? rowByCat[editCatId] : undefined

  // Load assignees map to resolve item_group_id -> row id (for audit log)
  const loadAssignees = async () => {
    try {
      const res = await httpClient.get<{ items: CategoryAssignee[] }>('/api/category-assignees', {
        params: { page_size: 1000 },
      })
      setRows(res.data?.items || (res.data as any)?.data?.items || [])
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    // Load item groups
    httpClient
      .get<{ items: any[] }>('/api/item-groups', { params: { page_size: 1000 } })
      .then((res) => {
        const items = res.data?.items || (res.data as any)?.data?.items || []
        const opts = items.map((x: any) => ({
          value: x.id,
          label: x.name,
        }))
        setItemGroups(opts)
      })

    // Load employees
    httpClient
      .get<{ items: AssigneeEmployee[] }>('/api/employees', { params: { page_size: 1000 } })
      .then((res) => {
        const items: AssigneeEmployee[] = res.data?.items || (res.data as any)?.data?.items || []
        setEmployees(
          items.map((x) => ({
            id: x.id,
            full_name: x.full_name,
            code: x.code,
            status: x.status,
            status_label: x.status_label,
            is_active: x.is_active,
          })),
        )
      })

    loadAssignees()
  }, [])

  // Prefill from query params when editing / copying
  useEffect(() => {
    const p = Number(searchParams.get('primary')) || 0
    const b = Number(searchParams.get('backup')) || 0
    const c = Number(searchParams.get('cats')) || 0
    const d = Number(searchParams.get('dept')) || 0

    if (p) setPrimaryId(p)
    if (b) setBackupId(b)
    if (c) setSelectedCatIds([c])
    if (d) setDepartmentId(d)
  }, [searchParams])

  const handleSave = async () => {
    if (selectedCatIds.length === 0) {
      toast.error('Vui lòng chọn ít nhất 1 phân loại')
      return
    }
    //  bao-CR-527: chính bắt buộc + «Chính thức»; dự phòng khác người chính + «Chính thức».
    const pairError = validateAssigneePair(primaryId, backupId, employees)
    if (pairError) {
      toast.error(pairError)
      return
    }

    setSaving(true)
    try {
      const payload: CategoryAssigneeBulkPayload = {
        item_group_ids: selectedCatIds,
        primary_employee_id: primaryId,
        backup_employee_id: backupId || 0,
        department_id: departmentId,
      }
      await httpClient.post('/api/category-assignees/bulk', payload)
      toast.success(`Đã lưu phân công cho ${selectedCatIds.length} phân loại`)
      await loadAssignees()

      if (!editRowId) {
        navigate(appRoutes.procurement.categoryAssignees)
      }
    } catch (e: any) {
      toast.error(e.response?.data?.message || 'Lỗi khi lưu phân công')
    } finally {
      setSaving(false)
    }
  }

  const editCatLabel = useMemo(() => {
    if (!editCatId) return ''
    return itemGroups.find((c) => c.value === editCatId)?.label || ''
  }, [editCatId, itemGroups])

  const multiPickerOptions = useMemo(() => {
    return itemGroups.map((g) => ({ id: g.value, label: g.label }))
  }, [itemGroups])

  const departmentLabel = useMemo(() => {
    if (!departmentId) return DEFAULT_PURCHASING_LABEL
    return departments.find((d) => d.value === departmentId)?.label || `#${departmentId}`
  }, [departmentId, departments])

  //  bao-CR-527: chỉ mời người «Chính thức» đang hoạt động; người đang được gán mà nay không còn
  //  đạt thì vẫn hiện kèm tình trạng để người sửa thấy phải đổi.
  const employeeOptions = useMemo(
    () => assigneeOptions(employees, [primaryId, backupId]),
    [employees, primaryId, backupId],
  )

  return (
    //  ⚠️ Dùng `PageContainer` + `PageHeader` như mọi màn khác. Bản cũ tự dựng
    //  `div.p-6` + một hàng `flex` ôm nút quay lại, khối tiêu đề và cụm nút —
    //  ở khổ điện thoại tiêu đề gãy hai dòng cộng mô tả hai dòng nữa, nút quay
    //  lại bị căn giữa theo khối bốn dòng đó nên trôi lửng lơ giữa khoảng
    //  trắng, còn cụm Hủy/Lưu rơi xuống một hàng riêng dán mép trái.
    //  `PageHeader` có sẵn khe `leading` đúng cho nút quay lại.
    <PageContainer className="mx-auto max-w-5xl">
      {/*  `sticky` — prop có sẵn của `PageHeader` cho «form dài, nút Lưu nằm
           trên đầu»: cuộn xuống chỉnh xong rồi muốn lưu mà phải cuộn ngược lên
           thì thao tác nào cũng mất hai lần cuộn.

           ⚠️ Ghi lại số đo cho người sau khỏi tưởng đây là chỗ nó phát huy:
           với bản ghi CHƯA có lịch sử, cả trang chỉ **869px trên khung 844px**
           ở 390px — cuộn được đúng 25px, nên dải ghim 109px gần như không đổi
           gì. Nó chỉ đáng khi thẻ *Lịch sử thao tác* dài ra (bản ghi bị sửa
           nhiều lần). Khách chốt bật (12/09/2026). Muốn xét lại thì mở một bản
           ghi có nhiều dòng nhật ký rồi đo, đừng đo bản ghi mới. */}
      <PageHeader
        sticky
        leading={
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate(appRoutes.procurement.categoryAssignees)}
            title="Quay lại danh sách"
            aria-label="Quay lại danh sách"
          >
            <ArrowLeft />
          </Button>
        }
        title={
          editCatLabel
            ? `Sửa phân công: ${editCatLabel} · ${departmentLabel}`
            : 'Gán phân công phụ trách'
        }
        description={
          //  Ẩn ở khổ hẹp: câu này mô tả việc của cả màn, đọc một lần rồi thôi,
          //  nhưng ngốn hai dòng ngay trên ô nhập đầu tiên ở MỌI lần mở màn.
          <span className="max-md:hidden">
            Phân công Nhân sự thu mua chịu trách nhiệm xử lý các dòng YCMH theo phân loại.
          </span>
        }
        //  Hai nút chia đôi hàng ở khổ hẹp — không có lớp này thì chúng co theo
        //  chữ và dán mép phải sau một khoảng trống dài.
        actionsClassName="max-md:[&>button]:flex-1"
        actions={
          <>
            <Button
              variant="outline"
              onClick={() => navigate(appRoutes.procurement.categoryAssignees)}
            >
              Hủy
            </Button>
            <Button onClick={handleSave} disabled={saving} className="shadow-sm">
              <Save />
              {saving ? 'Đang lưu…' : 'Lưu phân công'}
            </Button>
          </>
        }
      />

      {/* Form Content */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="space-y-4 md:col-span-2">
          <Card className="space-y-5 p-4">
            <h2 className="flex items-center gap-2 text-base font-semibold text-navy dark:text-foreground">
              <UserCheck className="size-4 text-primary" />
              Thông tin phân công NSTM
            </h2>

            {/*  Phòng áp dụng đứng TRÊN ô phân loại: đổi phòng là đổi bộ dòng
                 «đã có» bên dưới, chọn xuôi từ trên xuống thì người dùng không
                 phải quay lên sửa lại. */}
            <div className="space-y-2">
              <Label htmlFor="ca-department">Phòng áp dụng</Label>
              {/*  bao-CR-524: KHÔNG còn mục ảo «Thu mua chung». Danh sách chỉ gồm phòng thật; để
                   trống thì backend ghi phòng thu mua mặc định («Sản xuất -Thu mua»). */}
              <SearchSelect
                id="ca-department"
                value={departmentId ? String(departmentId) : ''}
                onChange={(next) => setDepartmentId(Number(next) || 0)}
                options={departments.map((d) => ({ value: String(d.value), label: d.label }))}
                placeholder={DEPARTMENT_PLACEHOLDER}
                searchPlaceholder="Tìm phòng ban…"
                emptyMessage="Không có phòng ban nào"
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Bộ của phòng thu mua mặc định (Sản xuất -Thu mua) áp cho mọi phiếu chưa có dòng
                riêng của phòng xử lý. Chọn một phòng khác thì cặp NSTM bên dưới chỉ nhận phiếu do
                phòng đó xử lý, kể cả phiếu phòng khác nhờ phòng này xử lý.
              </p>
            </div>

            {/* Item Groups Picker */}
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-x-2">
                <Label>
                  Phân loại VTBB
                  <RequiredMark />
                </Label>
                <span className="text-xs font-normal text-muted-foreground">
                  Đã chọn {selectedCatIds.length} phân loại
                </span>
              </div>

              <MultiPicker<number>
                options={multiPickerOptions}
                value={selectedCatIds}
                onChange={(ids) => setSelectedCatIds(ids)}
                placeholder="Chọn một hoặc nhiều phân loại…"
                searchPlaceholder="Tìm phân loại…"
              />
              <p className="text-xs text-muted-foreground">
                Có thể chọn nhiều phân loại để gán NSTM chính/dự phòng hàng loạt.
              </p>
            </div>

            {/*  bao-CR-530: hai ô này dùng `SearchSelect` (gõ tìm, không phân biệt dấu) cho đồng bộ
                 với ô Phòng áp dụng / Phân loại ngay trên — danh sách nhân sự dài, `Select` thường
                 bắt cuộn tay mới tìm ra người. */}
            <EmployeeSelect
              id="ca-primary"
              label="NSTM chính"
              required
              value={primaryId}
              onChange={setPrimaryId}
              placeholder="Chọn Nhân sự thu mua chính"
              employees={employeeOptions}
              hint="Bắt buộc, chỉ chọn được nhân sự «Chính thức» đang hoạt động. Nhân viên này sẽ được hệ thống ưu tiên tự động gán xử lý các dòng thuộc phân loại trên YCMH."
            />

            <EmployeeSelect
              id="ca-backup"
              clearable
              label="NSTM dự phòng (tùy chọn)"
              value={backupId}
              onChange={setBackupId}
              placeholder="Không có dự phòng"
              employees={employeeOptions.filter((e) => e.value !== primaryId)}
              hint="Tối đa một người, khác NSTM chính, cũng phải «Chính thức». Được gán xử lý khi NSTM chính không còn «Chính thức» (nghỉ thai sản, nghỉ việc…)."
            />
          </Card>
        </div>

        {/*  ⚠️ KHÔNG tự dựng tiêu đề «Lịch sử thao tác» ở đây — `AuditTimeline`
             đã tự in đúng câu đó. Bản cũ có cả hai nên khi đã cuộn tới, màn
             hình hiện **hai dòng tiêu đề giống hệt nhau chồng lên nhau**; ở bố
             cục ba cột của màn rộng nó lọt lưới vì thẻ nằm ngoài tầm mắt, xuống
             khổ điện thoại xếp dọc thì lộ ngay. */}
        <Card className="p-4">
          {editRowId ? (
            <AuditTimeline entity="category_assignee" entityId={editRowId} />
          ) : (
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-base font-semibold text-navy dark:text-foreground">
                <Users className="size-4 text-muted-foreground" />
                Lịch sử thao tác
              </h3>
              <p className="text-sm text-muted-foreground italic">
                Lịch sử thay đổi sẽ hiển thị khi xem/sửa bản ghi phân công đã lưu.
              </p>
            </div>
          )}
        </Card>
      </div>
    </PageContainer>
  )
}

/**
 * Ô chọn MỘT nhân sự thu mua — gõ tìm theo tên hoặc mã (bao-CR-530, `SearchSelect` tìm bỏ dấu).
 *
 * «Chưa chọn ai» = chuỗi rỗng ở ô, quy về `0` khi bắn ra ngoài. Ô dự phòng có nút xóa
 * (`clearable`) vì để trống là hợp lệ; ô chính thì không — bắt buộc chọn.
 */
function EmployeeSelect({
  id,
  clearable,
  label,
  required,
  value,
  onChange,
  placeholder,
  employees,
  hint,
}: {
  id: string
  clearable?: boolean
  label: string
  required?: boolean
  value: number
  onChange: (id: number) => void
  placeholder: string
  employees: AssigneeOption[]
  hint: string
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label}
        {required && <RequiredMark />}
      </Label>
      <SearchSelect
        id={id}
        value={value ? String(value) : ''}
        onChange={(next) => onChange(Number(next) || 0)}
        options={employees.map((employee) => ({ value: String(employee.value), label: employee.label }))}
        placeholder={placeholder}
        searchPlaceholder="Gõ tên hoặc mã nhân viên…"
        emptyMessage="Không có nhân sự «Chính thức» nào khớp"
        clearable={clearable}
        className="w-full"
      />
      <p className="text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}
