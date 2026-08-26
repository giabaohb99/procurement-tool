import { Building2, CalendarRange, Network } from 'lucide-react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import {
  useDepartments,
  useDepartmentsByCompanies,
} from '@/modules/hr/hooks/use-departments'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { DATE_RANGES, type DateRangeKey } from '../helpers/dashboard-date-range'

/** Giá trị ô select khi không lọc gì — Radix không nhận chuỗi rỗng làm value. */
const ALL = 'all'

interface DocumentDashboardFiltersProps {
  companyId?: number
  departmentId?: number
  rangeKey: DateRangeKey
  /** Khoảng ngày tự chọn — chỉ có nghĩa khi `rangeKey === 'custom'`. */
  fromDate?: string
  toDate?: string
  onChange: (next: {
    companyId?: number
    departmentId?: number
    rangeKey: DateRangeKey
    fromDate?: string
    toDate?: string
  }) => void
}

/**
 * Thanh lọc của trang tổng quan Văn thư: pháp nhân · phòng ban · khoảng thời gian.
 *
 * Ba ô này lọc **toàn bộ trang** — cả năm thẻ KPI lẫn ba biểu đồ — chứ không
 * phải riêng một khối. Lọc một phần thì trang đọc ra hai kỳ khác nhau cùng lúc,
 * và không có gì trên màn hình nói cho người xem biết điều đó.
 *
 * Khoảng thời gian bày sẵn mấy mức thay vì hai ô chọn ngày: câu hỏi thật của
 * người dùng là *"tuần này thế nào"*, không phải *"từ 11/08 tới 18/08"*.
 * Riêng biểu đồ 12 tháng KHÔNG chịu ảnh hưởng của ô này (nó tự khai cửa sổ của
 * nó) — mô tả dưới tiêu đề biểu đồ đó đã nói rõ "12 tháng gần nhất".
 */
export function DocumentDashboardFilters({
  companyId,
  departmentId,
  rangeKey,
  fromDate,
  toDate,
  onChange,
}: DocumentDashboardFiltersProps) {
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })
  //  ⚠️ HỎI BACKEND, đừng lọc `company_id` ở client. Một phòng có mặt ở NHIỀU
  //  pháp nhân (`tab_department_company`), còn `Department.company_id` chỉ là
  //  pháp nhân GỐC — lọc theo mình nó thì phòng phục vụ pháp nhân khác biến mất
  //  khỏi ô chọn. `by-companies` gộp cả hai nguồn (xem
  //  `department/service.phong_ban_cua_cac_phap_nhan`).
  const { data: capPhongBan } = useDepartmentsByCompanies(companyId ? [companyId] : [])

  const departmentOptions = companyId
    ? (capPhongBan ?? []).map((cap) => ({ id: cap.department_id, name: cap.department_name }))
    : (departments?.items ?? [])
        .filter((item) => item.is_active)
        .map((item) => ({ id: item.id, name: item.name }))

  //  Pháp nhân CHƯA khai phòng ban nào là chuyện có thật trên dữ liệu đang chạy
  //  (13 pháp nhân, phòng ban mới khai cho 2). Ô chọn bung ra rỗng trơn mà không
  //  nói gì thì người dùng tưởng hệ hỏng — nói thẳng ra là thiếu khai báo.
  const noDepartmentDeclared = Boolean(companyId) && departmentOptions.length === 0

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <Select
        value={companyId ? String(companyId) : ALL}
        onValueChange={(next) =>
          //  Đổi pháp nhân thì BỎ luôn phòng ban đang chọn: phòng đó thuộc pháp
          //  nhân cũ, giữ lại là lọc ra rỗng mà người dùng không hiểu vì sao.
          onChange({
            companyId: next === ALL ? undefined : Number(next),
            departmentId: undefined,
            rangeKey,
            fromDate,
            toDate,
          })
        }
      >
        <SelectTrigger className="w-auto min-w-52 gap-2">
          <Building2 className="size-4 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Toàn đơn vị</SelectItem>
          {(companies?.items ?? []).map((company) => (
            <SelectItem key={company.id} value={String(company.id)}>
              {company.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={departmentId ? String(departmentId) : ALL}
        onValueChange={(next) =>
          onChange({
            companyId,
            departmentId: next === ALL ? undefined : Number(next),
            rangeKey,
            fromDate,
            toDate,
          })
        }
      >
        <SelectTrigger className="w-auto min-w-52 gap-2">
          <Network className="size-4 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Tất cả phòng ban</SelectItem>
          {noDepartmentDeclared && (
            <p className="px-2 py-3 text-xs text-muted-foreground">
              Pháp nhân này chưa khai phòng ban nào. Khai ở <strong>Nhân sự ▸ Phòng ban</strong>.
            </p>
          )}
          {departmentOptions.map((department) => (
            <SelectItem key={department.id} value={String(department.id)}>
              {department.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={rangeKey}
        onValueChange={(next) =>
          onChange({
            companyId,
            departmentId,
            rangeKey: next as DateRangeKey,
            fromDate,
            toDate,
          })
        }
      >
        <SelectTrigger className="w-auto min-w-40 gap-2">
          <CalendarRange className="size-4 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {DATE_RANGES.map((item) => (
            <SelectItem key={item.key} value={item.key}>
              {item.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/*  Chỉ hiện khi thật sự cần: bày sẵn một ô lịch cạnh ô mức thời gian là
           hai thứ cùng trả lời một câu, người dùng phải đoán cái nào đang ăn. */}
      {rangeKey === 'custom' && (
        <DateRangePicker
          from={fromDate}
          to={toDate}
          onChange={(from, to) =>
            onChange({ companyId, departmentId, rangeKey: 'custom', fromDate: from, toDate: to })
          }
        />
      )}
    </div>
  )
}

