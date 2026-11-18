import { CircleCheck, FolderKanban, ListTodo, Timer, TriangleAlert, UserRoundX } from 'lucide-react'

import { StatCard } from '@/shared/ui/stat-card'

import type { WorkOverview } from '../hooks/use-work-overview'

const num = (value: number | undefined) => (value ?? 0).toLocaleString('vi-VN')

interface WorkOverviewStatCardsProps {
  data: WorkOverview | undefined
  periodDays: number
  isLoading: boolean
}

/**
 * Sáu ô số đầu màn Tổng quan Dự án (duoc-CR-782) — luôn đứng TRÊN dải tab, đổi tab không mất con số chung.
 *
 * Hai ô một hàng ở khổ hẹp: con số ngắn, ô không cần rộng — sáu ô xếp dọc là phải vuốt hai lần mới tới phần đáng xem.
 */
export function WorkOverviewStatCards({ data, periodDays, isLoading }: WorkOverviewStatCardsProps) {
  const overdueShare = data?.task_open ? Math.round((data.task_overdue * 100) / data.task_open) : 0
  const onTime = data?.on_time_rate ?? null

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 xl:grid-cols-6">
      <StatCard icon={FolderKanban} label="Dự án đang chạy" value={num(data?.project_total)} loading={isLoading} />
      <StatCard
        icon={ListTodo}
        label="Việc đang mở"
        value={num(data?.task_open)}
        hint={data ? `${num(data.task_created_in_period)} việc mới trong ${periodDays} ngày` : undefined}
        loading={isLoading}
      />
      <StatCard
        icon={TriangleAlert}
        label="Việc quá hạn"
        value={num(data?.task_overdue)}
        //  Tô đỏ một số 0 là báo động giả.
        hint={data?.task_overdue ? `${overdueShare}% số việc đang mở` : undefined}
        tone={data?.task_overdue ? 'danger' : undefined}
        loading={isLoading}
      />
      <StatCard
        icon={CircleCheck}
        label={`Xong trong ${periodDays} ngày`}
        value={num(data?.task_done_in_period)}
        loading={isLoading}
      />
      <StatCard
        icon={Timer}
        label="Xong đúng hạn"
        //  `null` = chưa có việc xong nào có hạn để đo — hiện gạch, không hiện 0%.
        value={onTime === null ? '—' : `${onTime}%`}
        hint="Trên số việc xong trong kỳ có đặt hạn"
        tone={onTime !== null && onTime < 50 ? 'warning' : undefined}
        loading={isLoading}
      />
      <StatCard
        icon={UserRoundX}
        label="Chưa ai nhận"
        value={num(data?.task_unassigned)}
        hint={data ? `${num(data.task_no_due)} việc chưa đặt hạn` : undefined}
        tone={data?.task_unassigned ? 'warning' : undefined}
        loading={isLoading}
      />
    </div>
  )
}
