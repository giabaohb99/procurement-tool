import { CalendarOff, ClipboardCheck, TriangleAlert, UserPlus, Users } from 'lucide-react'

import { StatCard } from '@/shared/ui/stat-card'
import { NEW_HIRE_DAYS, type HrOverview } from '../hooks/use-hr-overview'
import type { LeaveGlance } from '../hooks/use-hr-leave-glance'

interface HrOverviewStatsProps {
  overview: HrOverview
  leave: LeaveGlance
}

/**
 * Dải số liệu đầu trang Tổng quan Nhân sự.
 *
 * Chọn năm ô theo NHỊP LÀM VIỆC chứ không theo "cái gì đếm được": đội hình đang
 * có · ai mới vào · hôm nay ai vắng · còn gì phải ký · hồ sơ nào phải nhập bù.
 * Số người ĐÃ NGHỈ cố ý không có ô riêng — nó không sinh ra việc gì, và vẫn đọc
 * được ở biểu đồ "Cơ cấu trạng thái".
 */
export function HrOverviewStats({ overview, leave }: HrOverviewStatsProps) {
  const { stats, gaps } = overview

  return (
    // 2 → 3 → 5 cột, HAI CỘT ngay từ điện thoại: năm ô xếp một cột là hơn một
    // màn hình cuộn chỉ để đi qua dải số liệu. Thiếu mốc `lg` ở giữa thì khoảng
    // 1024–1279px (cửa sổ chia đôi màn 13") tụt thẳng về 2 cột, tức ba hàng thẻ
    // trước khi thấy được biểu đồ nào.
    <div className="mb-4 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 xl:grid-cols-5">
      <StatCard
        icon={Users}
        label="Đang làm việc"
        value={stats.active}
        hint={overview.orgHint}
        loading={overview.isLoading}
      />

      <StatCard
        icon={UserPlus}
        label={`Mới vào ${NEW_HIRE_DAYS} ngày`}
        value={stats.newHires}
        hint="Tính theo ngày vào làm"
        loading={overview.isLoading}
      />

      {/* Hai ô nghỉ phép vẫn dựng khi thiếu quyền — `StatCard` hiện 0 kèm câu
          giải thích, còn giấu hẳn thì dải thẻ đổi từ 5 sang 3 ô và bố cục lưới
          của từng người dùng một khác. */}
      <StatCard
        icon={CalendarOff}
        label="Nghỉ hôm nay"
        value={leave.canRead ? leave.offToday : 0}
        hint={
          !leave.canRead
            ? 'Không có quyền xem'
            : leave.offToday
              ? 'Đang trong kỳ nghỉ'
              : 'Hôm nay đủ quân'
        }
        loading={leave.isLoading}
      />

      <StatCard
        icon={ClipboardCheck}
        label="Đơn nghỉ chờ duyệt"
        value={leave.canRead ? leave.pending : 0}
        hint={
          !leave.canRead
            ? 'Không có quyền xem'
            : leave.pending
              ? 'Đang chờ chữ ký'
              : 'Không tồn đọng'
        }
        tone={leave.canRead && leave.pending ? 'warning' : undefined}
        loading={leave.isLoadingPending}
      />

      {/* Câu chú thích cũ «Thiếu ô bắt buộc, xem thẻ bên dưới» gãy hai dòng ở
          mọi cửa sổ dưới 1500px, mà nửa sau vốn thừa: thẻ ngay bên dưới đã mang
          đúng tên «Hồ sơ cần bổ sung» và liệt kê từng ô. */}
      <StatCard
        icon={TriangleAlert}
        label="Hồ sơ cần bổ sung"
        value={gaps.total}
        hint={gaps.total ? 'Thiếu ô bắt buộc' : 'Đã khai đủ'}
        tone={gaps.total ? 'warning' : undefined}
        loading={overview.isLoading}
      />
    </div>
  )
}
