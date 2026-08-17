import { AlertTriangle, CalendarClock, CheckCircle2, FileText, PenLine } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { CHART_COLORS, CHART_NEUTRAL, ChartCard } from '@/shared/ui/chart'
import { ColumnChart } from '@/shared/ui/column-chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { useDocumentDashboard } from '../hooks/use-document-dashboard'
import type { DocumentRecord } from '../types/document-record'
import type { DocumentTodo } from '../types/document-dashboard'

/**
 * Tổng quan Văn thư: KPI + văn bản ban hành theo tháng + cơ cấu theo loại +
 * việc cần xử lý + văn bản gần đây.
 *
 * Dựng đúng khuôn trang Tổng quan Thu mua (`ProcurementDashboardPage`) — cùng
 * `StatCard`, `ChartCard`, `ColumnChart`, `DonutChart` — để hai phân hệ không
 * đọc ra hai thứ tiếng khác nhau.
 *
 * Toàn bộ lấy từ MỘT lần gọi `/api/documents/dashboard`, và backend đã lọc theo
 * đúng phạm vi dữ liệu như danh sách văn bản.
 */
export function DocumentDashboardPage() {
  const { data, isLoading } = useDocumentDashboard()

  const kpi = data?.kpi
  const banHanhNam = (data?.issued_12m ?? []).reduce((sum, item) => sum + item.value, 0)

  return (
    <PageContainer>
      <PageHeader
        title="Văn thư"
        description="Công văn, quyết định, quy chế và biểu mẫu nội bộ."
      />

      <div className="mb-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          icon={CheckCircle2}
          label="Đang có hiệu lực"
          value={kpi?.effective ?? 0}
          hint="Văn bản đang áp dụng"
          loading={isLoading}
        />
        <StatCard
          icon={PenLine}
          label="Đang chờ duyệt"
          value={kpi?.submitted ?? 0}
          hint={kpi?.submitted ? 'Cần phê duyệt' : 'Không tồn đọng'}
          tone={kpi?.submitted ? 'warning' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={AlertTriangle}
          label="Cần rà lại"
          value={kpi?.needs_review ?? 0}
          hint={kpi?.needs_review ? 'Văn bản cha đã đổi' : 'Không có'}
          tone={kpi?.needs_review ? 'danger' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={CalendarClock}
          label="Sắp hết hiệu lực"
          value={kpi?.expiring ?? 0}
          hint="Trong 30 ngày tới"
          tone={kpi?.expiring ? 'warning' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={FileText}
          label="Bản nháp"
          value={kpi?.draft ?? 0}
          hint="Đang soạn"
          loading={isLoading}
        />
      </div>

      <div className="grid items-start gap-4 lg:grid-cols-3">
        <ChartCard
          className="lg:col-span-2"
          title="Văn bản ban hành theo tháng"
          description={`${banHanhNam} văn bản trong 12 tháng gần nhất`}
          loading={isLoading}
          isEmpty={banHanhNam === 0}
          emptyLabel="12 tháng qua chưa ban hành văn bản nào."
        >
          <ColumnChart data={data?.issued_12m ?? []} unit="văn bản" />
        </ChartCard>

        <ChartCard
          title="Việc cần xử lý"
          description={`${(data?.todo ?? []).reduce((s, i) => s + i.count, 0)} việc đang chờ`}
          loading={isLoading}
          isEmpty={(data?.todo ?? []).length === 0}
          emptyLabel="Không có việc nào đang treo."
        >
          <ul className="divide-y">
            {(data?.todo ?? []).map((item) => (
              <TodoRow key={item.key} item={item} />
            ))}
          </ul>
        </ChartCard>

        <ChartCard
          className="lg:col-span-2"
          title="Văn bản gần đây"
          description="8 văn bản mới nhất trong phạm vi bạn xem được."
          loading={isLoading}
          isEmpty={(data?.recent ?? []).length === 0}
          emptyLabel="Chưa có văn bản nào."
        >
          <ul className="divide-y">
            {(data?.recent ?? []).map((row) => (
              <RecentRow key={row.id} row={row} />
            ))}
          </ul>
        </ChartCard>

        <ChartCard
          title="Cơ cấu theo loại"
          description="Văn bản đang có hiệu lực."
          loading={isLoading}
          isEmpty={(data?.by_type ?? []).length === 0}
        >
          <DonutChart
            centerLabel="văn bản"
            unit="văn bản"
            data={(data?.by_type ?? []).map((item, index) => ({
              label: item.name,
              value: item.value,
              //  Quá 4 loại thì phần đuôi dùng xám trung tính — bảng màu chỉ có
              //  4 tông đã kiểm cho người mù màu.
              color: CHART_COLORS[index] ?? CHART_NEUTRAL,
            }))}
          />
        </ChartCard>
      </div>
    </PageContainer>
  )
}

function TodoRow({ item }: { item: DocumentTodo }) {
  return (
    <li className="flex items-center justify-between gap-3 py-2.5 first:pt-0">
      <div className="min-w-0">
        <p className="text-sm font-medium">{item.label}</p>
        <p className="text-xs text-muted-foreground">{item.hint}</p>
      </div>
      <span
        className={cn(
          'shrink-0 text-lg font-semibold tabular-nums',
          item.tone === 'warning' && 'text-warning',
        )}
      >
        {item.count}
      </span>
    </li>
  )
}

function RecentRow({ row }: { row: DocumentRecord }) {
  return (
    <li className="py-2.5 first:pt-0">
      <Link
        to={appRoutes.document.documentDetail(row.id)}
        className="flex flex-wrap items-center gap-2 text-sm hover:underline"
      >
        <span className="font-mono text-xs text-muted-foreground">
          {row.display_code || 'chưa cấp số'}
        </span>
        <span className="min-w-0 flex-1 truncate font-medium">{row.title}</span>
        <span className="text-xs text-muted-foreground">{row.status_label}</span>
        {row.effective_date && (
          <span className="text-xs text-muted-foreground">
            {formatDate(row.effective_date)}
          </span>
        )}
      </Link>
    </li>
  )
}
