import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { AI_PLAN_STATUS } from '@/shared/constants/statuses'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { AiPlanStatusBadge } from '../components/ai-plan-status-badge'
import { WorkSidebarPeekButton } from '../components/work-sidebar-peek-button'
import { useAiPlans } from '../hooks/use-ai-plans'
import { AI_PLAN_STATUS_PENDING, type AiPlanSummary } from '../types/ai-plan'

const ALL = 'all'

/** "2 giai đoạn · 7 việc · 3 việc con" — bỏ phần bằng 0 cho gọn. */
function describeCounts({ counts }: AiPlanSummary): string {
  const parts = [
    counts.phases ? `${counts.phases} giai đoạn` : '',
    counts.tasks ? `${counts.tasks} việc` : '',
    counts.subtasks ? `${counts.subtasks} việc con` : '',
  ].filter(Boolean)
  return parts.join(' · ')
}

/**
 * Danh sách đề xuất kế hoạch AI của TÔI (kh-AI1-3). Mặc định lọc *Chờ duyệt* — màn
 * này sinh ra để duyệt; xem lại đề xuất đã xử lý thì đổi ô trạng thái.
 */
export function AiPlanListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useUrlParamState('status', String(AI_PLAN_STATUS_PENDING))
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([status, pageSize])

  const { data, isLoading, isError } = useAiPlans({
    status: status === ALL ? undefined : Number(status),
    page,
    page_size: pageSize,
  })

  const columns = useMemo<DataTableColumn<AiPlanSummary>[]>(
    () => [
      {
        key: 'title',
        header: 'Kế hoạch',
        width: 320,
        hideable: false,
        cell: (row) => <span className="font-medium">{row.title}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 190,
        cell: (row) => <AiPlanStatusBadge status={row.status} label={row.status_label} />,
      },
      { key: 'deadline', header: 'Hạn chót', width: 110, cell: (row) => formatDate(row.deadline) },
      { key: 'counts', header: 'Quy mô', width: 220, cell: (row) => describeCounts(row) },
      { key: 'channel', header: 'Hỏi qua', width: 110, cell: (row) => row.channel_label },
      { key: 'created_at', header: 'Lập lúc', width: 150, cell: (row) => formatDateTime(row.created_at) },
    ],
    [],
  )

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 p-4 lg:p-6">
      <header className="flex min-w-0 items-start gap-2">
        <WorkSidebarPeekButton />
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight text-navy">Duyệt kế hoạch AI</h1>
          <p className="mt-1 text-sm text-muted-foreground max-md:hidden">
            Kế hoạch Trợ lý AI soạn theo yêu cầu của bạn. Mở một kế hoạch để sửa người, giờ, dòng
            việc rồi duyệt — việc chỉ được tạo trong Dự án sau khi bạn duyệt.
          </p>
        </div>
      </header>

      <DataTable
        fillHeight
        columns={columns}
        rows={data?.items}
        getRowId={(row) => row.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage={
          status === String(AI_PLAN_STATUS_PENDING)
            ? 'Không có kế hoạch nào đang chờ bạn duyệt.'
            : status === ALL
              ? 'Bạn chưa có kế hoạch AI nào. Hỏi Trợ lý AI lập kế hoạch để bắt đầu.'
              : 'Không có kế hoạch nào ở trạng thái này.'
        }
        storageKey="work.ai-plans"
        onRowClick={(row) => navigate(appRoutes.project.aiPlan(row.id))}
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'kế hoạch',
        }}
        toolbar={
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="h-9 w-full text-xs md:w-56" aria-label="Lọc theo trạng thái">
              <SelectValue placeholder="Trạng thái" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
              {AI_PLAN_STATUS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />
    </div>
  )
}
