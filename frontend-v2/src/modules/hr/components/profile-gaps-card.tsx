import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { ChartCard } from '@/shared/ui/chart'
import { cn } from '@/shared/utils/cn'
import type { ProfileGaps } from '../utils/hr-overview-metrics'

interface ProfileGapsCardProps {
  gaps: ProfileGaps
  loading: boolean
  canRead: boolean
  /** Ô span trên lưới của trang Tổng quan. */
  className?: string
}

interface GapRow {
  key: string
  label: string
  /** Hậu quả của việc bỏ trống ô đó — lý do duy nhất để nó nằm trên trang này. */
  hint: string
  count: number
  /** Đường lọc sẵn ở màn danh sách; bỏ trống khi backend chưa lọc được cột đó. */
  to?: string
}

/**
 * Bốn ô của hồ sơ mà bỏ trống thì hỏng việc Ở CHỖ KHÁC.
 *
 * Đây là thứ trang tổng quan nợ người dùng: bốn biểu đồ cơ cấu không sinh ra
 * việc gì để làm, còn danh sách này thì bấm vào là ra đúng những hồ sơ phải đi
 * nhập bù. Câu mô tả nói HẬU QUẢ chứ không nhắc lại tên ô — "chưa gán quản lý
 * trực tiếp" tự nó không giục được ai, "đơn nghỉ phép không tìm được người ký"
 * thì có.
 */
export function ProfileGapsCard({
  gaps,
  loading,
  canRead,
  className,
}: ProfileGapsCardProps) {
  if (!canRead) {
    return (
      <ChartCard
        className={className}
        title="Hồ sơ cần bổ sung"
        isEmpty
        emptyLabel="Bạn không có quyền xem hồ sơ nhân sự."
      >
        <div />
      </ChartCard>
    )
  }

  const rows: GapRow[] = [
    {
      key: 'department',
      label: 'Chưa gán phòng ban',
      hint: 'Không vào được báo cáo cơ cấu, cũng không lọt phạm vi dữ liệu theo phòng.',
      count: gaps.noDepartment,
      //  `department_id=0` là GIÁ TRỊ THẬT của nhóm "chưa gắn", không phải mã
      //  giả cho "tất cả" — ô chọn phòng ban ở màn danh sách có sẵn mục này.
      to: `${appRoutes.hr.employees}?department_id=0`,
    },
    {
      key: 'manager',
      label: 'Chưa gán quản lý trực tiếp',
      hint: 'Đơn nghỉ phép không tìm được người ký, lặng lẽ chạy sai đường.',
      count: gaps.noManager,
      //  Cú pháp của bộ lọc nâng cao: `<cột>__<hậu tố>`. `manager_id` nằm trong
      //  `EMPLOYEE_FILTER_FIELDS` nên mở link ra là thấy sẵn dòng điều kiện.
      to: `${appRoutes.hr.employees}?manager_id__eq=0`,
    },
    {
      key: 'hire-date',
      label: 'Chưa nhập ngày vào làm',
      hint: 'Thâm niên tính bằng 0 — người đó mất phần ngày phép cộng thêm.',
      count: gaps.noHireDate,
      //  Không có link: `hire_date` không nằm trong whitelist lọc của backend,
      //  đưa link ra sẽ mở một danh sách KHÔNG lọc gì mà trông như đã lọc.
    },
    {
      key: 'position',
      label: 'Chưa gán chức vụ',
      hint: 'Phiếu in ra trống chức danh người ký.',
      count: gaps.noPosition,
    },
  ]

  return (
    <ChartCard
      className={className}
      title="Hồ sơ cần bổ sung"
      description={
        gaps.total
          ? `${gaps.total} hồ sơ đang thiếu ít nhất một ô.`
          : 'Nhân sự đang làm việc đã khai đủ.'
      }
      loading={loading}
    >
      <ul className="divide-y">
        {rows.map((row) => (
          <GapRowItem key={row.key} row={row} />
        ))}
      </ul>
    </ChartCard>
  )
}

function GapRowItem({ row }: { row: GapRow }) {
  const content = (
    <>
      <div className="min-w-0">
        <p className="text-sm font-medium">{row.label}</p>
        <p className="text-xs text-muted-foreground">{row.hint}</p>
      </div>
      <span className="flex shrink-0 items-center gap-1">
        <span
          className={cn(
            'text-lg font-semibold tabular-nums',
            row.count > 0 ? 'text-warning' : 'text-muted-foreground',
          )}
        >
          {row.count}
        </span>
        {/* Mũi tên chỉ hiện khi bấm vào THẬT SỰ đi tới đâu đó: dòng không có
            link mà vẫn vẽ mũi tên thì người dùng bấm hụt vài lần rồi thôi. */}
        <ChevronRight
          className={cn('size-4 text-muted-foreground', !row.to && 'invisible')}
          aria-hidden
        />
      </span>
    </>
  )

  const className = 'flex items-center justify-between gap-3 py-2.5'

  //  Đếm bằng 0 thì bỏ link: mở ra một danh sách rỗng không nói thêm được gì.
  if (!row.to || row.count === 0) {
    return <li className={className}>{content}</li>
  }

  return (
    <li>
      <Link
        to={row.to}
        className={cn(className, '-mx-2 rounded-md px-2 transition-colors hover:bg-accent')}
      >
        {content}
      </Link>
    </li>
  )
}
