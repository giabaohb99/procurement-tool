import { Building2, CalendarRange, Network } from 'lucide-react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import {
  useDepartments,
  useDepartmentsByCompanies,
} from '@/modules/hr/hooks/use-departments'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { cn } from '@/shared/utils/cn'
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
/**
 * Lớp dùng chung cho ba ô lọc ở đây.
 *
 * ⚠️ `SelectTrigger` của shadcn để `justify-between`, mà ba ô này có **BA** con:
 * biểu tượng · giá trị · mũi tên. Ô lại rộng hơn nội dung (`min-w-*`), nên ba
 * thứ bị dàn đều ra và **chữ trôi vào giữa ô**, cách hẳn biểu tượng bên trái
 * (khách báo 26/08/2026). Ô chọn thường chỉ có hai con nên không ai gặp.
 *
 * Cho ô giá trị `flex-1` là nó ăn hết chỗ thừa: biểu tượng dính mép trái, chữ
 * bắt đầu ngay sau nó, mũi tên bị đẩy về mép phải. Sửa ở đây thay vì bỏ
 * `min-w-*`: bề rộng tối thiểu là cố ý, để ba ô không nhảy qua nhảy lại mỗi lần
 * đổi lựa chọn dài ngắn khác nhau.
 */
const O_LOC = 'w-auto gap-2 [&>[data-slot=select-value]]:flex-1 [&>[data-slot=select-value]]:text-left'

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
  const { data: departmentLevel } = useDepartmentsByCompanies(companyId ? [companyId] : [])

  const departmentOptions = companyId
    ? (departmentLevel ?? []).map((cap) => ({ id: cap.department_id, name: cap.department_name }))
    : (departments?.items ?? [])
        .filter((item) => item.is_active)
        .map((item) => ({ id: item.id, name: item.name }))

  //  Pháp nhân CHƯA khai phòng ban nào là chuyện có thật trên dữ liệu đang chạy
  //  (13 pháp nhân, phòng ban mới khai cho 2). Ô chọn bung ra rỗng trơn mà không
  //  nói gì thì người dùng tưởng hệ hỏng — nói thẳng ra là thiếu khai báo.
  const noDepartmentDeclared = Boolean(companyId) && departmentOptions.length === 0

  //  «Đang lọc» = KHÁC mặc định, chứ không phải «có giá trị»: mặc định của ô
  //  thời gian là `all` (Tất cả) chứ không phải rỗng, đếm nó là ô nào cũng
  //  luôn luôn đang lọc và huy hiệu mất hết ý nghĩa.
  const activeCount =
    (companyId ? 1 : 0) + (departmentId ? 1 : 0) + (rangeKey !== 'all' ? 1 : 0)

  //  Tên pháp nhân có thể CHƯA về (ô chọn nạp bất đồng bộ) — bỏ qua phần chưa
  //  biết còn hơn in ra «#12», thứ không nói được gì cho người đọc.
  const summary = [
    companies?.items.find((item) => item.id === companyId)?.name,
    departmentOptions.find((item) => item.id === departmentId)?.name,
    rangeKey === 'all' ? undefined : DATE_RANGES.find((item) => item.key === rangeKey)?.label,
  ]
    .filter(Boolean)
    .join(' · ')

  /**
   * Dựng ba ô chọn. Gọi HAI lần — một cho thanh ngang ở màn rộng, một cho tờ
   * trượt ở khổ hẹp — vì hai chỗ chỉ khác nhau ở bề rộng: trên thanh thì ô ôm
   * lấy nội dung (`min-w-*`), trong tờ trượt thì trải hết bề ngang màn hình.
   * Khai một lần rồi tái dùng để hai khổ màn không lệch nhau dần: thêm một
   * pháp nhân vào ô này mà quên ô kia là điện thoại và máy tính lọc ra hai con
   * số khác nhau, không chỗ nào báo.
   */
  const buildFields = (inSheet: boolean) => ({
    company: (
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
        <SelectTrigger className={cn(O_LOC, inSheet ? 'w-full' : 'min-w-52')}>
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
    ),

    department: (
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
        <SelectTrigger className={cn(O_LOC, inSheet ? 'w-full' : 'min-w-52')}>
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
    ),

    range: (
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
        <SelectTrigger className={cn(O_LOC, inSheet ? 'w-full' : 'min-w-40')}>
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
    ),

    //  Chỉ hiện khi thật sự cần: bày sẵn một ô lịch cạnh ô mức thời gian là
    //  hai thứ cùng trả lời một câu, người dùng phải đoán cái nào đang ăn.
    dates:
      rangeKey === 'custom' ? (
        <DateRangePicker
          from={fromDate}
          to={toDate}
          onChange={(from, to) =>
            onChange({ companyId, departmentId, rangeKey: 'custom', fromDate: from, toDate: to })
          }
        />
      ) : null,
  })

  const bar = buildFields(false)
  const sheet = buildFields(true)

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {/*  ⚠️ Khổ hẹp: ba ô dọn vào TỜ TRƯỢT. Ba ô bề rộng cứng (52+52+40 nấc
           Tailwind ≈ 540px) trên 358px dùng được thì mỗi ô rớt xuống một hàng
           riêng — đúng ba hàng bậc thang, cao 124px, nằm chắn ngay trên dải số
           liệu là thứ người ta mở trang này để xem. Nút gọn còn 36px.

           `QuickFilterSheet` tự mang `md:hidden`, còn thanh ngang bên dưới tự
           `hidden md:flex` — không có nhánh JS nào chọn giữa hai bản, nên đổi
           cỡ cửa sổ không cần dựng lại gì. */}
      <QuickFilterSheet
        activeCount={activeCount}
        onClearAll={() =>
          onChange({
            companyId: undefined,
            departmentId: undefined,
            rangeKey: 'all',
            fromDate: undefined,
            toDate: undefined,
          })
        }
      >
        <QuickFilterField label="Pháp nhân">{sheet.company}</QuickFilterField>
        <QuickFilterField label="Phòng ban">{sheet.department}</QuickFilterField>
        <QuickFilterField label="Khoảng thời gian">{sheet.range}</QuickFilterField>
        {sheet.dates && (
          <QuickFilterField label="Từ ngày — đến ngày">{sheet.dates}</QuickFilterField>
        )}
      </QuickFilterSheet>

      {/*  ⚠️ Tóm tắt phải bày RA NGOÀI tờ trượt. Đây là trang tổng quan: mọi con
           số và cả năm biểu đồ đều là kết quả của ba ô kia, mà giấu hết vào sau
           một cái nút thì người đọc không còn cách nào biết «20 văn bản» là của
           toàn công ty hay của một phòng. Huy hiệu đếm của tờ trượt chỉ nói CÓ
           BAO NHIÊU ô đang lọc, không nói lọc cái gì. Dòng này chỉ mọc ra khi
           thật sự có lọc — chưa lọc gì thì nó là chữ thừa. */}
      {summary && (
        <p className="min-w-0 flex-1 truncate text-xs text-muted-foreground md:hidden">
          {summary}
        </p>
      )}

      <div className="hidden flex-wrap items-center gap-2 md:flex">
        {bar.company}
        {bar.department}
        {bar.range}
        {bar.dates}
      </div>
    </div>
  )
}

