import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'
import { Skeleton } from '@/shared/ui/skeleton'
import { AccountCoverageCard } from '../components/account-coverage-card'
import { useHrOverview } from '../hooks/use-hr-overview'

/**
 * Dashboard phân hệ Nhân sự: thẻ số liệu + biểu đồ cơ cấu.
 *
 * KHÔNG lặp lại thẻ lối tắt vào từng màn hình — menu trái đã có sẵn các mục đó.
 */
export function HrDashboardPage() {
  const overview = useHrOverview()

  return (
    <ModuleDashboard
      title="Nhân sự"
      description="Nhân viên, phòng ban, pháp nhân và phân quyền tài khoản."
      stats={
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Đang làm việc"
              value={overview.stats.active}
              loading={overview.isLoading}
            />
            <StatCard
              label="Đã nghỉ"
              value={overview.stats.inactive}
              loading={overview.isLoading}
            />
            <StatCard
              label="Phòng ban"
              value={overview.stats.departments}
              loading={overview.isLoading}
            />
            <StatCard
              label="Pháp nhân"
              value={overview.stats.companies}
              loading={overview.isLoadingCompanies}
            />
          </div>

          {/* MỖI HÀNG là một lưới riêng: thẻ trong cùng hàng cao bằng nhau, hàng
              sau không bị thẻ cao nhất của hàng trước đẩy xuống. Biểu đồ cột cần
              bề ngang nên chiếm 2/3, thẻ cơ cấu 1/3. */}
          <div className="grid gap-4 lg:grid-cols-3">
            <ChartCard
              className="lg:col-span-2"
              title="Nhân sự theo phòng ban"
              description="Số nhân sự đang làm việc của từng phòng."
              loading={overview.isLoading}
              isEmpty={overview.byDepartment.length === 0}
            >
              <HorizontalBarChart data={overview.byDepartment} unit="nhân sự" />
            </ChartCard>

            <ChartCard
              title="Cơ cấu trạng thái"
              description="Toàn bộ hồ sơ nhân sự, kể cả đã nghỉ."
              loading={overview.isLoading}
              isEmpty={overview.byStatus.length === 0}
            >
              <DonutChart data={overview.byStatus} centerLabel="hồ sơ" unit="nhân sự" />
            </ChartCard>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <ChartCard
              className="lg:col-span-2"
              title="Nhân sự theo pháp nhân"
              description="Số nhân sự đang làm việc của từng công ty."
              loading={overview.isLoading || overview.isLoadingCompanies}
              isEmpty={overview.byCompany.length === 0}
            >
              <HorizontalBarChart data={overview.byCompany} unit="nhân sự" />
            </ChartCard>

            <AccountCoverageCard
              data={overview.accounts}
              loading={overview.isLoading || overview.isLoadingAccounts}
              canRead={overview.canReadAccounts}
            />
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
}: {
  label: string
  value?: number
  loading: boolean
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-7 w-16" />
        ) : (
          <p className="text-2xl font-bold text-navy">
            {(value ?? 0).toLocaleString('vi-VN')}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
