import { useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { DetailPageHeader } from '@/shared/ui/detail-page-header'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

import { AGENT_DIR_IN, type AgentRunRow } from '../api/agent-hub-api'
import { AgentTaskStatusBadge } from '../components/agent-task-status-badge'
import { useAgentTask } from '../hooks/use-agent-tasks'
import { formatDurationMs, formatUsd, stripTelegramHtml } from '../utils/agent-task-format'

/**
 * CHI TIẾT một việc của bot (ai-CR-036) — `/system/agent-tasks/:id`.
 *
 * Bốn khối theo thứ tự đáng đọc: thông tin chung · yêu cầu / rà soát / kế hoạch · các bước đã
 * chạy (thời gian, token, chi phí) · hội thoại Telegram. Chỉ đọc — không có nút thao tác.
 */
export function AgentTaskDetailPage() {
  const { id } = useParams()
  const taskId = Number(id) || 0
  const { data: task, isLoading, isError, refetch } = useAgentTask(taskId)

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-48 w-full" />
      </PageContainer>
    )
  }
  if (isError || !task) {
    return (
      <PageContainer>
        <ErrorState title="Không tải được việc này" description="Việc không còn trong sổ, hoặc mạng đang lỗi.">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Thử lại
          </Button>
        </ErrorState>
      </PageContainer>
    )
  }

  const runColumns: DataTableColumn<AgentRunRow>[] = [
    { key: 'started_at', header: 'Lúc', width: 140, cell: (r) => formatDateTime(r.started_at) || '—' },
    { key: 'stage', header: 'Bước', width: 150, cell: (r) => r.stage_label },
    { key: 'status', header: 'Kết quả', width: 90, cell: (r) => r.status_label },
    { key: 'duration', header: 'Lâu', width: 90, cell: (r) => formatDurationMs(r.duration_ms) },
    {
      key: 'tokens',
      header: 'Token vào / ra',
      width: 130,
      cell: (r) => (r.input_tokens || r.output_tokens ? `${r.input_tokens} / ${r.output_tokens}` : '—'),
    },
    { key: 'cost', header: 'Chi phí ước', width: 100, cell: (r) => formatUsd(r.cost_usd) },
    { key: 'model', header: 'Model', width: 180, defaultHidden: true, cell: (r) => r.model || '—' },
    {
      key: 'error',
      header: 'Lỗi',
      width: 280,
      cell: (r) => (r.error ? <span className="truncate text-destructive" title={r.error}>{r.error}</span> : ''),
    },
  ]

  const facts: [string, string][] = [
    ['Nguồn', task.source_label],
    ['Rủi ro', task.risk_label],
    ['Nhận lúc', formatDateTime(task.created_at) || '—'],
    ['Đóng lúc', formatDateTime(task.closed_at) || '—'],
    ['Nhánh', task.branch_name || '—'],
    ['Bản gộp', task.merged_sha ? task.merged_sha.slice(0, 10) : '—'],
    ['Lên dev', formatDateTime(task.deployed_dev_at) || '—'],
    ['Chi phí ước', formatUsd(task.cost_usd)],
  ]

  return (
    <PageContainer>
      <DetailPageHeader
        backTo={appRoutes.system.agentTasks}
        backLabel="Về danh sách việc của bot"
        title={`${task.code} · ${task.title}`}
        badges={<AgentTaskStatusBadge status={task.status} label={task.status_label} />}
      />

      <Card>
        <CardContent className="grid gap-x-6 gap-y-2 pt-6 sm:grid-cols-2 lg:grid-cols-4">
          {facts.map(([label, value]) => (
            <div key={label} className="min-w-0">
              <div className="text-xs text-muted-foreground">{label}</div>
              <div className="truncate text-sm" title={value}>{value}</div>
            </div>
          ))}
          {task.timing && <p className="text-sm text-muted-foreground sm:col-span-2 lg:col-span-4">{task.timing}</p>}
          {task.note && (
            <p className="whitespace-pre-wrap text-sm sm:col-span-2 lg:col-span-4">
              <span className="text-muted-foreground">Ghi chú: </span>
              {task.note}
            </p>
          )}
          {task.pr_url && (
            <a className="text-sm text-primary underline sm:col-span-2" href={task.pr_url} target="_blank" rel="noreferrer">
              Mở PR trên GitHub
            </a>
          )}
        </CardContent>
      </Card>

      <TextBlock title="Yêu cầu" body={task.summary} />
      <TextBlock title="Rà soát mã" body={task.scan_message} />
      <TextBlock
        title="Kế hoạch"
        body={[task.plan, task.plan_files.length ? `Tệp dự kiến đụng:\n${task.plan_files.join('\n')}` : '']
          .filter(Boolean)
          .join('\n\n')}
      />
      {task.questions.length > 0 && <TextBlock title="Câu đang hỏi đại ca" body={task.questions.join('\n')} />}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Các bước đã chạy ({task.run_list.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={runColumns}
            rows={task.run_list}
            getRowId={(r) => String(r.id)}
            emptyMessage="Chưa chạy bước nào."
            storageKey="system.agent_task_runs"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Hội thoại Telegram ({task.messages.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {task.messages.length === 0 && <p className="text-sm text-muted-foreground">Chưa có tin nào gắn với việc này.</p>}
          {task.messages.map((m) => (
            <div
              key={m.id}
              className={cn(
                'max-w-[85%] rounded-lg px-3 py-2 text-sm',
                m.direction === AGENT_DIR_IN ? 'ml-auto bg-primary/10' : 'bg-muted',
              )}
            >
              <div className="mb-1 text-xs text-muted-foreground">
                {m.direction_label} · {formatDateTime(m.created_at)}
                {m.files > 0 && ` · ${m.files} ảnh`}
              </div>
              <div className="whitespace-pre-wrap break-words">{stripTelegramHtml(m.body)}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </PageContainer>
  )
}

function TextBlock({ title, body }: { title: string; body: string }) {
  if (!body.trim()) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="whitespace-pre-wrap break-words text-sm">{body}</div>
      </CardContent>
    </Card>
  )
}
