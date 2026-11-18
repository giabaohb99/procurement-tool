import { CalendarX2, TriangleAlert, UserRoundCheck, UserRoundX } from 'lucide-react'
import { useState } from 'react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'
import { TAB_LIST_UNDERLINE_ALWAYS, TAB_TRIGGER_UNDERLINE_ALWAYS } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'

import {
  WorkOverviewPeopleChart,
  WorkOverviewProjectChart,
  WorkOverviewStatusChart,
} from '../components/work-overview-charts'
import { WorkOverviewPeopleTable } from '../components/work-overview-people-table'
import { WorkOverviewProjectHealthCards } from '../components/work-overview-project-health-cards'
import { WorkOverviewPeriodSwitch } from '../components/work-overview-period-switch'
import { WorkOverviewStatCards } from '../components/work-overview-stat-cards'
import { WorkOverviewTracker } from '../components/work-overview-tracker'
import { WorkTaskShortlist } from '../components/work-task-shortlist'
import { DEFAULT_WORK_OVERVIEW_PERIOD, useWorkOverview } from '../hooks/use-work-overview'

const TABS = [
  { key: 'overview', label: 'Tổng quan' },
  { key: 'projects', label: 'Dự án' },
  { key: 'people', label: 'Nhân sự' },
] as const

/**
 * Màn mặc định của phân hệ Dự án — trang BÁO CÁO cho người quản lý (duoc-CR-782).
 *
 * Bố cục chia tab anh Được chốt 18/11/2026 (bản xếp dọc chín khối dài và rời): "cái nhìn vô đầu tiên phải là cái
 * chart, rồi mấy cái sau thì để user mò".
 * - TRÊN dải tab, luôn hiện: phạm vi xem, nút kỳ 7 / 30 / 90 ngày, sáu ô số;
 * - **Tổng quan** (mặc định): biểu đồ ĐỨNG ĐẦU (tình trạng việc mở, dự án, theo người), các mục quan trọng ngay dưới —
 *   quá hạn lâu nhất, chưa ai nhận, chưa đặt hạn, cơ cấu ưu tiên, việc của tôi ("các mục quan trọng nên đưa vào tổng quan");
 * - **Dự án**: bảng sức khỏe → theo dõi một dự án;
 * - **Nhân sự**: bảng đối chiếu → theo dõi một người.
 * Tab nằm trên URL (`?tab=`) để gửi link hay bấm quay lại vẫn đúng chỗ.
 *
 * Người được giao xem báo cáo Công việc & Dự án (admin có sẵn) thấy MỌI dự án; người khác thấy dự án mình tham gia.
 */
export function WorkOverviewPage() {
  const [periodDays, setPeriodDays] = useState<number>(DEFAULT_WORK_OVERVIEW_PERIOD)
  const [tab, setTab] = useUrlParamState('tab', 'overview')
  const activeTab = TABS.some((t) => t.key === tab) ? tab : 'overview'
  const { data, isLoading, isError, byPriority } = useWorkOverview(periodDays)

  return (
    <ModuleDashboard
      title="Dự án"
      description="Dự án, bảng kanban, giao việc và theo dõi tiến độ."
      stats={
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-muted-foreground">
              {data?.scope === 'all'
                ? 'Đang xem số liệu của mọi dự án.'
                : 'Đang xem số liệu các dự án bạn tham gia.'}
            </p>
            <WorkOverviewPeriodSwitch value={periodDays} onChange={setPeriodDays} />
          </div>

          <WorkOverviewStatCards data={data} periodDays={periodDays} isLoading={isLoading} />

          <Tabs value={activeTab} onValueChange={setTab}>
            <TabsList className={TAB_LIST_UNDERLINE_ALWAYS}>
              {TABS.map((t) => (
                <TabsTrigger key={t.key} value={t.key} className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                  {t.label}
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value="overview" className="mt-4 space-y-4">
              <div className="grid gap-4 lg:grid-cols-3">
                <WorkOverviewStatusChart data={data} isLoading={isLoading} />
                <div className="lg:col-span-2">
                  <WorkOverviewProjectChart data={data} periodDays={periodDays} isLoading={isLoading} />
                </div>
              </div>
              <WorkOverviewPeopleChart data={data} periodDays={periodDays} isLoading={isLoading} />

              {/*  Các mục quan trọng nằm NGAY DƯỚI biểu đồ trong cùng tab (anh Được: "các mục quan trọng nên đưa vào tổng
                   quan"). Con số chỉ nói "có vấn đề"; ba danh sách nói "vấn đề nằm ở việc nào, ai đang giữ". */}
              <div className="grid gap-4 lg:grid-cols-3">
                <WorkTaskShortlist
                  icon={TriangleAlert}
                  overdue
                  title="Quá hạn lâu nhất"
                  description="Việc trễ lâu nhất lên đầu, kèm số ngày trễ và người đang giữ."
                  tasks={data?.overdue_tasks ?? []}
                  total={data?.task_overdue ?? 0}
                  loading={isLoading}
                  emptyMessage="Không có việc nào quá hạn."
                />
                <WorkTaskShortlist
                  icon={UserRoundX}
                  title="Chưa ai nhận"
                  description="Việc đang mở không có người phụ trách — không ai làm, cũng không hiện ở bảng theo người."
                  tasks={data?.unassigned_tasks ?? []}
                  total={data?.task_unassigned ?? 0}
                  loading={isLoading}
                  emptyMessage="Việc nào cũng đã có người nhận."
                />
                <WorkTaskShortlist
                  icon={CalendarX2}
                  title="Chưa đặt hạn"
                  description="Không có hạn thì không bao giờ quá hạn — lọt khỏi mọi cảnh báo. Việc tạo lâu nhất lên đầu."
                  tasks={data?.no_due_tasks ?? []}
                  total={data?.task_no_due ?? 0}
                  loading={isLoading}
                  emptyMessage="Việc nào cũng đã có hạn."
                />
              </div>
              <div className="grid gap-4 lg:grid-cols-3">
                <ChartCard
                  title="Cơ cấu mức ưu tiên"
                  description="Việc chưa xong, theo mức ưu tiên đang đặt."
                  loading={isLoading}
                  isEmpty={byPriority.length === 0}
                >
                  <DonutChart data={byPriority} centerLabel="việc" unit="việc" />
                </ChartCard>
                <div className="lg:col-span-2">
                  <WorkTaskShortlist
                    icon={UserRoundCheck}
                    title="Việc của tôi"
                    description="Việc tôi đang phụ trách, hạn gần nhất lên đầu."
                    tasks={data?.my_tasks ?? []}
                    total={data?.task_mine ?? 0}
                    loading={isLoading}
                    emptyMessage="Chưa có việc nào giao cho bạn."
                  />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="projects" className="mt-4 space-y-4">
              <WorkOverviewProjectHealthCards projects={data?.projects} isLoading={isLoading} isError={isError} />
              <WorkOverviewTracker kind="project" data={data} periodDays={periodDays} />
            </TabsContent>

            <TabsContent value="people" className="mt-4 space-y-4">
              <WorkOverviewPeopleTable
                people={data?.people}
                periodDays={periodDays}
                isLoading={isLoading}
                isError={isError}
              />
              <WorkOverviewTracker kind="person" data={data} periodDays={periodDays} />
            </TabsContent>
          </Tabs>
        </div>
      }
    />
  )
}
