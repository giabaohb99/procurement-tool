import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { useWorkOverview } from '../hooks/use-work-overview'

/**
 * Màn mặc định của phân hệ Dự án — trang BÁO CÁO, cùng khuôn `ModuleDashboard`
 * với Nhân sự / Sản xuất / Quản trị.
 *
 * Trước đây chỗ này chỉ là một dòng "chọn một dự án ở cột bên trái": mở phân hệ
 * ra thấy trang trắng, không biết mình đang có bao nhiêu việc, việc nào trễ.
 *
 * Cố ý KHÔNG tự nhảy vào dự án đầu tiên: nhảy thì người dùng mở phân hệ ra đã
 * thấy việc của một đội nào đó mà không hiểu vì sao đang đứng ở đó.
 */
export function WorkOverviewPage() {
  const { data, isLoading, byProject, byPriority } = useWorkOverview()

  return (
    <ModuleDashboard
      title="Dự án"
      description="Dự án, bảng kanban, giao việc và theo dõi tiến độ."
      stats={
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <StatCard label="Dự án đang chạy" value={data?.project_total} loading={isLoading} />
            <StatCard label="Việc chưa xong" value={data?.task_open} loading={isLoading} />
            <StatCard
              label="Việc quá hạn"
              value={data?.task_overdue}
              loading={isLoading}
              //  Quá hạn là con số phải đập vào mắt; 0 thì để màu thường, tô đỏ
              //  một số 0 là báo động giả.
              tone={data?.task_overdue ? 'danger' : undefined}
            />
            <StatCard label="Việc của tôi" value={data?.task_mine} loading={isLoading} />
            <StatCard label="Đã hoàn thành" value={data?.task_done} loading={isLoading} />
          </div>

          {/* MỖI HÀNG một lưới riêng để thẻ trong hàng cao bằng nhau. Biểu đồ
              cột cần bề ngang nên chiếm 2/3, vòng cơ cấu 1/3. */}
          <div className="grid gap-4 lg:grid-cols-3">
            <ChartCard
              className="lg:col-span-2"
              title="Việc chưa xong theo dự án"
              description="Tám dự án nhiều việc nhất; dự án đã lưu trữ không tính."
              loading={isLoading}
              isEmpty={byProject.length === 0}
            >
              <HorizontalBarChart data={byProject} unit="việc" />
            </ChartCard>

            <ChartCard
              title="Cơ cấu mức ưu tiên"
              description="Việc chưa xong, theo mức ưu tiên đang đặt."
              loading={isLoading}
              isEmpty={byPriority.length === 0}
            >
              <DonutChart data={byPriority} centerLabel="việc" unit="việc" />
            </ChartCard>
          </div>
        </div>
      }
    />
  )
}

function StatCard({
  label,
  value,
  loading,
  tone,
}: {
  label: string
  value?: number
  loading: boolean
  tone?: 'danger'
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-7 w-16" />
        ) : (
          <p
            className={cn(
              'text-2xl font-bold text-navy',
              tone === 'danger' && 'text-destructive',
            )}
          >
            {(value ?? 0).toLocaleString('vi-VN')}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
