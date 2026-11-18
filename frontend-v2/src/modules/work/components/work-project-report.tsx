import { LineChart as LineChartIcon } from 'lucide-react'
import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

import { DEFAULT_WORK_OVERVIEW_PERIOD, useWorkOverview } from '../hooks/use-work-overview'
import { trendStepLabel } from '../utils/trend-step-label'
import { WorkOverviewPeopleChart, WorkOverviewStatusChart } from './work-overview-charts'
import { WorkOverviewPeopleTable } from './work-overview-people-table'
import { WorkOverviewPeriodSwitch } from './work-overview-period-switch'
import { WorkOverviewTrendChart } from './work-overview-trend-chart'
import { WorkProjectAttentionCard } from './work-project-attention-card'
import { WorkProjectReportSummary } from './work-project-report-summary'

/**
 * Khung nhìn BÁO CÁO của MỘT dự án — tab cuối trong chi tiết dự án (duoc-CR-782, anh Được: "khi anh nhấn vào từng dự án,
 * anh cũng muốn có mục báo cáo riêng cho từng dự án").
 *
 * Bố cục "cột phải cố định" anh chọn 18/11/2026 (bản trước xếp dọc một cột, sáu ô số bị cây dự án bóp hẹp):
 * - cột TRÁI rộng: nút kỳ, biểu đồ diễn biến của dự án, biểu đồ theo người, bảng đối chiếu theo người;
 * - cột PHẢI cố định 18rem: tóm tắt (% hoàn thành + sức khỏe + các số), tình trạng việc mở, việc cần xử lý.
 *
 * ⚠️ Chia cột theo bề rộng của CHÍNH KHUNG NÀY (`@container`), không theo bề rộng màn hình: cùng một màn 1440px mà cây
 * dự án mở hay đóng thì khung rộng hẹp khác hẳn. Khung hẹp thì xếp một cột, cột phải lên TRƯỚC — % hoàn thành là
 * câu trả lời đầu tiên người xem cần.
 */
export function WorkProjectReport({ listId }: { listId: number }) {
  const [periodDays, setPeriodDays] = useState<number>(DEFAULT_WORK_OVERVIEW_PERIOD)
  const { data, isLoading, isError } = useWorkOverview(periodDays, listId)
  const project = data?.projects.find((p) => p.list_id === listId)

  return (
    <div className="@container min-h-0 flex-1 space-y-4 overflow-y-auto pb-6">
      {/*  Nút kỳ đứng TRÊN cả hai cột: số "xong trong kỳ" ở thẻ tóm tắt cũng theo nó, và hai cột bắt đầu thẳng hàng. */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground">Kỳ thống kê:</span>
        <WorkOverviewPeriodSwitch value={periodDays} onChange={setPeriodDays} />
      </div>

      <div className="flex flex-col gap-4 @3xl:flex-row @3xl:items-start">
        <div className="min-w-0 flex-1 space-y-4">
          <Card className="gap-3">
            <CardHeader className="max-md:px-4">
              <CardTitle className="flex items-center gap-2 text-base">
                <LineChartIcon className="size-4 text-muted-foreground" />
                Diễn biến của dự án
              </CardTitle>
              <CardDescription>
                Theo từng {trendStepLabel(periodDays)} trong {periodDays} ngày: cột là việc xong (đúng hạn / trễ / không
                đặt hạn), đường là việc mới giao.
              </CardDescription>
            </CardHeader>
            <CardContent className="max-md:px-4">
              <WorkOverviewTrendChart kind="project" id={listId} periodDays={periodDays} />
            </CardContent>
          </Card>

          <WorkOverviewPeopleChart data={data} periodDays={periodDays} isLoading={isLoading} />

          <WorkOverviewPeopleTable
            people={data?.people}
            periodDays={periodDays}
            isLoading={isLoading}
            isError={isError}
          />
        </div>

        <aside aria-label="Tóm tắt dự án" className="order-first space-y-4 @3xl:order-none @3xl:w-72 @3xl:shrink-0 @6xl:w-80">
          <WorkProjectReportSummary data={data} project={project} periodDays={periodDays} isLoading={isLoading} />
          <WorkOverviewStatusChart data={data} isLoading={isLoading} />
          <WorkProjectAttentionCard data={data} isLoading={isLoading} />
        </aside>
      </div>
    </div>
  )
}
