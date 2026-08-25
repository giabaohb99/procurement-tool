/**
 * Mấy mức thời gian của thanh lọc trang tổng quan.
 *
 * Khai thành hàm `resolve()` chứ không phải hai chuỗi ngày cố định: trang có thể
 * mở từ tối hôm trước sang sáng hôm sau, và "Hôm nay" tính lúc nạp mô-đun thì
 * sáng ra vẫn còn trỏ vào ngày hôm qua.
 *
 * Mọi mức đều tính theo NGÀY LẬP văn bản (`created_at`) — xem `DashboardFilters`
 * bên backend để biết vì sao không phải ngày hiệu lực.
 */
export type DateRangeKey =
  | 'today' | 'week' | 'month' | 'quarter' | 'year' | 'all'
  /** Khoảng do người dùng tự chọn trên lịch — hai đầu nằm ở state của trang. */
  | 'custom'

export interface ResolvedRange {
  /** `YYYY-MM-DD`, hoặc `undefined` nếu mức này không chặn đầu nào. */
  from?: string
  to?: string
}

/** `YYYY-MM-DD` theo giờ ĐỊA PHƯƠNG. `toISOString()` đổi sang UTC nên lệch ngày. */
function iso(day: Date): string {
  const thang = String(day.getMonth() + 1).padStart(2, '0')
  const ngay = String(day.getDate()).padStart(2, '0')
  return `${day.getFullYear()}-${thang}-${ngay}`
}

function truocNgay(so: number): Date {
  const day = new Date()
  day.setDate(day.getDate() - so)
  return day
}

export const DATE_RANGES: {
  key: DateRangeKey
  label: string
  resolve: () => ResolvedRange
}[] = [
  {
    key: 'today',
    label: 'Hôm nay',
    resolve: () => ({ from: iso(new Date()), to: iso(new Date()) }),
  },
  {
    key: 'week',
    label: '7 ngày qua',
    resolve: () => ({ from: iso(truocNgay(6)), to: iso(new Date()) }),
  },
  {
    key: 'month',
    label: '30 ngày qua',
    resolve: () => ({ from: iso(truocNgay(29)), to: iso(new Date()) }),
  },
  {
    key: 'quarter',
    label: '90 ngày qua',
    resolve: () => ({ from: iso(truocNgay(89)), to: iso(new Date()) }),
  },
  {
    key: 'year',
    label: 'Năm nay',
    resolve: () => {
      const now = new Date()
      return { from: `${now.getFullYear()}-01-01`, to: iso(now) }
    },
  },
  {
    key: 'all',
    label: 'Tất cả',
    //  Không chặn đầu nào — backend bỏ qua tham số rỗng.
    resolve: () => ({}),
  },
  {
    key: 'custom',
    label: 'Khoảng ngày…',
    //  Hai đầu KHÔNG suy được từ đây — chúng do người dùng chọn trên lịch và
    //  nằm ở state của trang. `toDashboardParams` nhận riêng qua tham số cuối.
    resolve: () => ({}),
  },
]

/**
 * Dịch lựa chọn của thanh lọc thành tham số gửi lên backend.
 *
 * Nằm ở đây chứ không cạnh component: tệp component chỉ nên export component
 * (`react-refresh/only-export-components`), và đây vốn là logic thuần — có chỗ
 * này thì kiểm được bằng test mà không phải dựng cả một cây React.
 */
export function toDashboardParams(
  companyId: number | undefined,
  departmentId: number | undefined,
  rangeKey: DateRangeKey,
  /** Chỉ dùng khi `rangeKey === 'custom'` — khoảng người dùng chọn trên lịch. */
  khoangTuChon?: ResolvedRange,
): { company_id?: number; department_id?: number; from_date?: string; to_date?: string } {
  const khoang =
    rangeKey === 'custom'
      ? khoangTuChon ?? {}
      : DATE_RANGES.find((item) => item.key === rangeKey)?.resolve()
  return {
    company_id: companyId,
    department_id: departmentId,
    //  Chuỗi rỗng phải thành `undefined`: gửi `from_date=` lên backend là một
    //  tham số có mặt nhưng vô nghĩa, và `apply_filters` sẽ so với chuỗi rỗng.
    from_date: khoang?.from || undefined,
    to_date: khoang?.to || undefined,
  }
}
