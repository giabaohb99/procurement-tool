import { ArrowLeft, Save, UserCheck, Users } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { httpClient } from '@/core/api/http-client'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

interface Option {
  value: number
  label: string
}

/** Mục «chưa chọn ai» của ô chọn nhân sự — `SelectItem` không nhận value rỗng. */
const NONE = 'none'

export function CategoryAssigneeFormPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [itemGroups, setItemGroups] = useState<Option[]>([])
  const [employees, setEmployees] = useState<Option[]>([])
  const [rowByCat, setRowByCat] = useState<Record<number, number>>({})

  const [selectedCatIds, setSelectedCatIds] = useState<number[]>([])
  const [primaryId, setPrimaryId] = useState<number | 0>(0)
  const [backupId, setBackupId] = useState<number | 0>(0)

  const [saving, setSaving] = useState(false)

  const editCatId = Number(searchParams.get('cats')) || 0
  const editRowId = editCatId ? rowByCat[editCatId] : undefined

  // Load assignees map to resolve item_group_id -> row id (for audit log)
  const loadAssignees = async () => {
    try {
      const res = await httpClient.get<{ items: any[] }>('/api/category-assignees', {
        params: { page_size: 1000 },
      })
      const items = res.data?.items || (res.data as any)?.data?.items || []
      const map: Record<number, number> = {}
      items.forEach((x: any) => {
        map[x.item_group_id] = x.id
      })
      setRowByCat(map)
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
      .get<{ items: any[] }>('/api/employees', { params: { page_size: 1000 } })
      .then((res) => {
        const items = res.data?.items || (res.data as any)?.data?.items || []
        const opts = items.map((x: any) => ({
          value: x.id,
          label: `${x.full_name}${x.code ? ` · ${x.code}` : ''}`,
        }))
        setEmployees(opts)
      })

    loadAssignees()
  }, [])

  // Prefill from query params when editing / copying
  useEffect(() => {
    const p = Number(searchParams.get('primary')) || 0
    const b = Number(searchParams.get('backup')) || 0
    const c = Number(searchParams.get('cats')) || 0

    if (p) setPrimaryId(p)
    if (b) setBackupId(b)
    if (c) setSelectedCatIds([c])
  }, [searchParams])

  const handleSave = async () => {
    if (selectedCatIds.length === 0) {
      toast.error('Vui lòng chọn ít nhất 1 phân loại')
      return
    }
    if (!primaryId) {
      toast.error('Vui lòng chọn NSTM chính')
      return
    }

    setSaving(true)
    try {
      await httpClient.post('/api/category-assignees/bulk', {
        item_group_ids: selectedCatIds,
        primary_employee_id: primaryId,
        backup_employee_id: backupId || 0,
      })
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
        title={editCatLabel ? `Sửa phân công: ${editCatLabel}` : 'Gán phân công phụ trách'}
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

            {/*  ⚠️ Hai ô này dùng `Select` dùng chung, bản cũ là `<select>` thô
                 khai tay `h-10`: cao hơn 4px so với mọi ô nhập khác của hệ, mũi
                 tên và cỡ chữ cũng khác — đứng cạnh `MultiPicker` ngay trên nó
                 là thấy ngay ba kiểu ô trong cùng một thẻ. */}
            <EmployeeSelect
              label="NSTM chính"
              required
              value={primaryId}
              onChange={setPrimaryId}
              placeholder="Chọn Nhân sự thu mua chính"
              employees={employees}
              hint="Nhân viên này sẽ được hệ thống ưu tiên tự động gán xử lý các dòng thuộc phân loại trên YCMH."
            />

            <EmployeeSelect
              label="NSTM dự phòng (tùy chọn)"
              value={backupId}
              onChange={setBackupId}
              placeholder="Không có dự phòng"
              employees={employees}
              hint="Được gán xử lý khi NSTM chính vắng mặt hoặc được ủy quyền."
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
 * Ô chọn MỘT nhân sự thu mua.
 *
 * ⚠️ `Select` của Radix không nhận `value=""`, mà "chưa chọn ai" là trạng thái
 * hợp lệ ở đây (ô dự phòng để trống là bình thường). Nên dùng chuỗi sentinel
 * `NONE` cho mục trống rồi quy về `0` khi bắn ra ngoài — đúng cách các màn khác
 * làm với `all` / `none`.
 */
function EmployeeSelect({
  label,
  required,
  value,
  onChange,
  placeholder,
  employees,
  hint,
}: {
  label: string
  required?: boolean
  value: number
  onChange: (id: number) => void
  placeholder: string
  employees: Option[]
  hint: string
}) {
  return (
    <div className="space-y-2">
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      <Select
        value={value ? String(value) : NONE}
        onValueChange={(next) => onChange(next === NONE ? 0 : Number(next))}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE}>{placeholder}</SelectItem>
          {employees.map((employee) => (
            <SelectItem key={employee.value} value={String(employee.value)}>
              {employee.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}
