import { Building2, CalendarRange, Network } from 'lucide-react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { DATE_RANGES, type DateRangeKey } from '../helpers/dashboard-date-range'

/** Giá trị ô select khi không lọc gì — Radix không nhận chuỗi rỗng làm value. */
const TAT_CA = 'all'

interface DocumentDashboardFiltersProps {
  companyId?: number
  departmentId?: number
  rangeKey: DateRangeKey
  onChange: (next: {
    companyId?: number
    departmentId?: number
    rangeKey: DateRangeKey
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
  onChange,
}: DocumentDashboardFiltersProps) {
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })

  //  Chọn pháp nhân rồi thì chỉ hiện phòng của pháp nhân đó — danh sách phòng
  //  của cả tập đoàn dài vài chục dòng, mà quá nửa không thuộc nơi đang xem.
  const departmentOptions = (departments?.items ?? []).filter(
    (item) => item.is_active && (!companyId || item.company_id === companyId),
  )

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <Select
        value={companyId ? String(companyId) : TAT_CA}
        onValueChange={(next) =>
          //  Đổi pháp nhân thì BỎ luôn phòng ban đang chọn: phòng đó thuộc pháp
          //  nhân cũ, giữ lại là lọc ra rỗng mà người dùng không hiểu vì sao.
          onChange({
            companyId: next === TAT_CA ? undefined : Number(next),
            departmentId: undefined,
            rangeKey,
          })
        }
      >
        <SelectTrigger className="w-auto min-w-52 gap-2">
          <Building2 className="size-4 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={TAT_CA}>Toàn đơn vị</SelectItem>
          {(companies?.items ?? []).map((company) => (
            <SelectItem key={company.id} value={String(company.id)}>
              {company.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={departmentId ? String(departmentId) : TAT_CA}
        onValueChange={(next) =>
          onChange({
            companyId,
            departmentId: next === TAT_CA ? undefined : Number(next),
            rangeKey,
          })
        }
      >
        <SelectTrigger className="w-auto min-w-52 gap-2">
          <Network className="size-4 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={TAT_CA}>Tất cả phòng ban</SelectItem>
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
          onChange({ companyId, departmentId, rangeKey: next as DateRangeKey })
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
    </div>
  )
}

