import { HandHelping, Loader2, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import {
  TICKET_PRIORITY_OPTIONS,
  TICKET_STATUS_OPTIONS,
} from '../config/ticket-constants'
import { TicketPriorityBadge, TicketStatusBadge } from '../config/ticket-meta'
import { useTakeTicket, useTickets } from '../hooks/use-tickets'
import type { Ticket } from '../types/ticket'

const ALL = 'all'

/** Ô chọn "Người xử lý" — chỉ người xử lý mới thấy, dùng đúng ba nhánh của backend. */
const ASSIGNEE_OPTIONS: { value: string; label: string }[] = [
  { value: ALL, label: 'Tất cả người xử lý' },
  { value: 'unassigned', label: 'Chưa ai nhận' },
  { value: 'me', label: 'Tôi đang xử lý' },
]

/**
 * Danh sách phiếu hỗ trợ.
 *
 * Backend giới hạn theo phạm vi: người gửi chỉ thấy phiếu của mình, người có vai
 * trò Hỗ trợ (proxy FE: `can('ticket','delete')`) thấy tất cả và có thêm ô lọc
 * "Người xử lý" cùng nút "Nhận". Bản v1 dùng dải pill + tải hết rồi cắt trang ở
 * trình duyệt; ở đây quy về ô chọn của DataTable và phân trang phía server.
 */
export function TicketListPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { can } = usePermission()
  const isHandler = can('ticket', 'delete')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [priority, setPriority] = useUrlParamState('priority', ALL)
  const [assignee, setAssignee] = useUrlParamState('assignee', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const [page, setPage] = usePageResetOnFilterChange([
    debouncedValue,
    status,
    priority,
    assignee,
  ])

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedValue) params.subject = debouncedValue
  if (status !== ALL) params.status = status
  if (priority !== ALL) params.priority = priority
  if (isHandler && assignee !== ALL) params.assignee = assignee

  const { data, isLoading, isError } = useTickets(params)
  const take = useTakeTicket()

  const columns = useMemo<DataTableColumn<Ticket>[]>(
    () => [
      {
        key: 'subject',
        header: 'Chủ đề',
        width: 280,
        hideable: false,
        defaultPinned: true,
        cell: (t) => (
          <div className="min-w-0">
            <div className="truncate font-medium text-navy dark:text-foreground">
              {t.subject || '(Không có chủ đề)'}
            </div>
            <div className="text-xs text-muted-foreground">{t.code}</div>
          </div>
        ),
      },
      {
        key: 'requester_name',
        header: 'Người gửi',
        width: 160,
        cell: (t) => t.requester_name || '—',
      },
      {
        key: 'department',
        header: 'Bộ phận',
        width: 180,
        cell: (t) => <span className="text-muted-foreground">{t.department || '—'}</span>,
      },
      {
        key: 'priority',
        header: 'Ưu tiên',
        width: 120,
        cell: (t) => <TicketPriorityBadge priority={t.priority} />,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        cell: (t) => <TicketStatusBadge status={t.status} />,
      },
      {
        key: 'assignee_name',
        header: 'Người xử lý',
        width: 160,
        cell: (t) =>
          t.assignee_name ? (
            <span className="font-medium text-navy dark:text-foreground">{t.assignee_name}</span>
          ) : (
            <span className="font-medium text-warning">Chưa ai nhận</span>
          ),
      },
      {
        key: 'updated_at',
        header: 'Cập nhật',
        width: 150,
        cell: (t) => (
          <span className="whitespace-nowrap text-muted-foreground">
            {formatDateTime(t.updated_at)}
          </span>
        ),
      },
      // Cột "Nhận" chỉ có nghĩa với người xử lý (assign là hành động handler-only ở
      // backend); người gửi thấy danh sách phiếu của mình thì không cần cột này.
      ...(isHandler
        ? [
            {
              key: 'action',
              header: '',
              width: 110,
              hideable: false,
              cell: (t: Ticket) =>
                !t.assignee_id && t.status !== 'closed' ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={take.isPending}
                    onClick={(e) => {
                      e.stopPropagation()
                      take.mutate({ ticketId: t.id, assigneeId: user?.id ?? 0 })
                    }}
                  >
                    {take.isPending ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <>
                        <HandHelping className="size-4" />
                        Nhận
                      </>
                    )}
                  </Button>
                ) : null,
            } satisfies DataTableColumn<Ticket>,
          ]
        : []),
    ],
    [isHandler, take, user?.id],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Phiếu hỗ trợ"
        description={
          isHandler
            ? 'Toàn bộ phiếu người dùng gửi lên. Bấm Nhận để tự gán mình làm người xử lý.'
            : 'Các phiếu hỗ trợ bạn đã gửi và tình trạng xử lý của chúng.'
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(t) => t.id}
          onRowClick={(t) => navigate(appRoutes.support.ticketDetail(t.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không có phiếu hỗ trợ nào khớp bộ lọc."
          storageKey="support.tickets"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'phiếu',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo chủ đề…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {TICKET_STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Ưu tiên" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi mức ưu tiên</SelectItem>
                  {TICKET_PRIORITY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {isHandler && (
                <Select value={assignee} onValueChange={setAssignee}>
                  <SelectTrigger className="w-44">
                    <SelectValue placeholder="Người xử lý" />
                  </SelectTrigger>
                  <SelectContent>
                    {ASSIGNEE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
