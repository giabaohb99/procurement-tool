import { Copy, Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { SealStatusBadge } from '../components/status-pill'
import { useSealRequests } from '../hooks/use-seal-requests'
import { SEAL_STATUS_LABELS, type SealRequest } from '../types/seal-request'

const ALL = 'all'

export function SealRequestListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canCreate = can('seal_request', 'create')
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.search = debouncedValue
    if (status !== ALL) p.status = status
    if (sortBy) {
      p.sort_by = sortBy
      p.sort_dir = sortDir
    }
    return p
  }, [page, pageSize, debouncedValue, status, sortBy, sortDir])

  const { data, isLoading, isError } = useSealRequests(params)

  const columns = useMemo<DataTableColumn<SealRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        cell: (r) => <span className="font-medium tabular-nums">{r.code || '—'}</span>,
        width: 120,
        hideable: false,
        defaultPinned: true,
        sortable: true,
      },
      {
        key: 'purpose',
        header: 'Mục đích',
        cell: (r) => r.purpose,
        wrap: true,
        minWidth: 200,
        sortable: true,
      },
      {
        key: 'companies',
        header: 'Công ty',
        cell: (r) =>
          r.companies.length > 0 ? r.companies.map((c) => c.name).join(', ') : '—',
        wrap: true,
        minWidth: 200,
      },
      {
        key: 'requester',
        header: 'Người tạo',
        cell: (r) => r.requester,
        width: 150,
        sortable: true,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        cell: (r) => <SealStatusBadge status={r.status} label={r.status_label} />,
        width: 130,
        sortable: true,
      },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        cell: (r) => <span className="tabular-nums">{formatDateTime(r.created_at) || '—'}</span>,
        width: 150,
        sortable: true,
      },
      {
        key: 'actions',
        header: 'Thao tác',
        align: 'center',
        width: 90,
        hideable: false,
        cell: (r) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon"
              aria-label={`Nhân bản ${r.code}`}
              title="Nhân bản"
              //  Ô hành động phải chặn nổi bọt, không thì bấm là mở luôn trang chi tiết.
              onClick={(e) => {
                e.stopPropagation()
                navigate(`${appRoutes.approvalSeal.new}?from=${r.id}`)
              }}
            >
              <Copy className="size-4" />
            </Button>
          ) : null,
      },
    ],
    [canCreate, navigate],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Yêu cầu đóng dấu"
        description="Tạo và theo dõi yêu cầu trình ký, duyệt và đóng dấu chứng từ."
        actions={
          canCreate ? (
            <Button onClick={() => navigate(appRoutes.approvalSeal.new)}>
              <Plus className="size-4" />
              Tạo yêu cầu
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          onRowClick={(r) => navigate(appRoutes.approvalSeal.detail(r.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có yêu cầu đóng dấu nào."
          storageKey="approval-seal.list"
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
            setPage(1)
          }}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'yêu cầu',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã, mục đích…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
                  {Object.entries(SEAL_STATUS_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
