import {
  CheckCircle2,
  Clock,
  ExternalLink,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Users,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchSelect } from '@/shared/ui/search-select'
import { Switch } from '@/shared/ui/switch'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'
import { cn } from '@/shared/utils/cn'
import { CompanyAvatarGroup } from '../components/company-avatar-group'
import { ClerkStatusBadge } from '../components/status-pill'
import { useSealClerks, useSyncSealClerks } from '../hooks/use-seal-clerks'
import { CLERK_STATUS, type SealClerkGroup } from '../types/seal-clerk'

const ALL = 'all'

type FilterTab = 'all' | 'head' | 'active' | 'leave'

function getInitials(name: string | null): string {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[parts.length - 2][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function SealClerkListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  // Quản lý phân công dùng chung khóa quyền `seal_type` (cấu hình Duyệt dấu).
  const canManage = can('seal_type', 'create')
  const canReadCompany = can('company', 'read')
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [tabFilter, setTabFilter] = useState<FilterTab>('all')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: companies } = useCompanies(
    { page_size: 500, is_active: true },
    { enabled: canReadCompany },
  )

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.search = debouncedValue
    if (companyId !== ALL) p.company_id = Number(companyId)
    return p
  }, [page, pageSize, debouncedValue, companyId])

  const { data, isLoading, isError, refetch, isFetching } = useSealClerks(params)
  // Bật/tắt "văn thư tổng" ngay tại dòng.
  const sync = useSyncSealClerks()

  // Dữ liệu hiển thị lọc theo tabFilter ở tầng client (khi đang xem danh sách)
  const filteredItems = useMemo(() => {
    const raw = data?.items ?? []
    if (tabFilter === 'head') return raw.filter((r) => r.is_head)
    if (tabFilter === 'active') return raw.filter((r) => r.status === CLERK_STATUS.active)
    if (tabFilter === 'leave') return raw.filter((r) => r.status !== CLERK_STATUS.active)
    return raw
  }, [data?.items, tabFilter])

  // Thống kê nhanh
  const stats = useMemo(() => {
    const items = data?.items ?? []
    const total = data?.total ?? items.length
    const head = items.filter((i) => i.is_head).length
    const active = items.filter((i) => i.status === CLERK_STATUS.active).length
    const leave = items.filter((i) => i.status !== CLERK_STATUS.active).length
    return { total, head, active, leave }
  }, [data])

  const columns = useMemo<DataTableColumn<SealClerkGroup>[]>(
    () => [
      {
        key: 'employee',
        header: 'Văn thư đóng dấu',
        minWidth: 240,
        sortable: true,
        cell: (r) => {
          const initials = getInitials(r.employee_name)
          return (
            <div className="flex items-center gap-3 py-1">
              <Avatar size="sm" className="size-8 shrink-0 border border-border/70 bg-primary/10 shadow-2xs">
                <AvatarFallback className="text-xs font-bold text-primary">
                  {initials}
                </AvatarFallback>
              </Avatar>

              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-navy dark:text-foreground">
                    {r.employee_name || `#${r.employee_id}`}
                  </span>
                  {r.is_head && (
                    <Badge variant="outline" className="border-indigo-200 bg-indigo-50 text-[10px] text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/60 dark:text-indigo-300">
                      Văn thư tổng
                    </Badge>
                  )}
                </div>
                {r.employee_code && (
                  <span className="font-mono text-[11px] text-muted-foreground">
                    Mã: {r.employee_code}
                  </span>
                )}
              </div>
            </div>
          )
        },
      },
      {
        key: 'is_head',
        header: 'Quyền Đa pháp nhân',
        width: 200,
        cell: (r) => (
          <div
            className="flex items-center gap-2.5 py-0.5"
            onClick={(e) => e.stopPropagation()}
          >
            <Tooltip disableHoverableContent>
              <TooltipTrigger asChild>
                <div>
                  <Switch
                    checked={r.is_head}
                    disabled={!canManage || sync.isPending}
                    aria-label="Đa pháp nhân"
                    onCheckedChange={(checked) =>
                      sync.mutate({
                        employee_id: r.employee_id,
                        company_ids: r.companies.map((c) => c.id),
                        is_head: checked,
                      })
                    }
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs text-xs">
                {r.is_head
                  ? 'Đang bật: Được phụ trách đóng dấu các phiếu yêu cầu nhiều công ty.'
                  : 'Đang tắt: Chỉ phụ trách đóng dấu các phiếu thuộc công ty chỉ định.'}
              </TooltipContent>
            </Tooltip>

            <span
              className={cn(
                'text-xs font-medium',
                r.is_head ? 'text-indigo-600 dark:text-indigo-400' : 'text-muted-foreground',
              )}
            >
              {r.is_head ? 'Đa pháp nhân' : 'Đơn pháp nhân'}
            </span>
          </div>
        ),
      },
      {
        key: 'companies',
        header: 'Công ty phụ trách',
        minWidth: 220,
        cell: (r) => (
          <div className="py-1">
            <CompanyAvatarGroup
              companies={r.companies}
              maxVisible={4}
              showNameWhenSingle={true}
            />
          </div>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 140,
        align: 'center',
        cell: (r) => <ClerkStatusBadge status={r.status} label={r.status_label ?? undefined} />,
      },
      {
        key: 'actions',
        header: 'Thao tác',
        width: 90,
        align: 'center',
        cell: (r) => (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs font-medium text-primary hover:text-primary/80"
            onClick={(e) => {
              e.stopPropagation()
              navigate(appRoutes.approvalSeal.clerkDetail(r.anchor_id))
            }}
          >
            Chi tiết
            <ExternalLink className="ml-1 size-3.5" />
          </Button>
        ),
      },
    ],
    [canManage, navigate, sync],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Phân công văn thư đóng dấu"
        description="Quản lý nhân sự văn thư chịu trách nhiệm đóng dấu theo từng công ty và văn thư tổng xử lý các hồ sơ đa pháp nhân."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="size-9"
              aria-label="Tải lại dữ liệu"
              title="Tải lại dữ liệu"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCw className={cn('size-4', isFetching && 'animate-spin')} />
            </Button>
            {canManage && (
              <Button onClick={() => navigate(appRoutes.approvalSeal.clerksNew)}>
                <Plus className="size-4" />
                Thêm phân công
              </Button>
            )}
          </div>
        }
      />

      {/* Khối KPI Glance Cards */}
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        {/* Tổng văn thư */}
        <Card
          className={cn(
            'flex cursor-pointer flex-col gap-1 p-3.5 transition-all hover:border-primary/50',
            tabFilter === 'all' && 'border-primary ring-1 ring-primary/20 bg-primary/5',
          )}
          onClick={() => setTabFilter('all')}
        >
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Tổng số văn thư</span>
            <Users className="size-4 text-primary" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-2xl tabular-nums text-navy dark:text-foreground">
              {stats.total}
            </span>
            <span className="text-xs text-muted-foreground">nhân sự</span>
          </div>
        </Card>

        {/* Văn thư tổng */}
        <Card
          className={cn(
            'flex cursor-pointer flex-col gap-1 p-3.5 transition-all hover:border-indigo-500/50',
            tabFilter === 'head' && 'border-indigo-500 ring-1 ring-indigo-500/20 bg-indigo-50/50 dark:bg-indigo-950/20',
          )}
          onClick={() => setTabFilter(tabFilter === 'head' ? 'all' : 'head')}
        >
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Đa pháp nhân</span>
            <ShieldCheck className="size-4 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-2xl tabular-nums text-indigo-600 dark:text-indigo-400">
              {stats.head}
            </span>
            <span className="text-xs text-muted-foreground">văn thư tổng</span>
          </div>
        </Card>

        {/* Đang hoạt động */}
        <Card
          className={cn(
            'flex cursor-pointer flex-col gap-1 p-3.5 transition-all hover:border-emerald-500/50',
            tabFilter === 'active' && 'border-emerald-500 ring-1 ring-emerald-500/20 bg-emerald-50/50 dark:bg-emerald-950/20',
          )}
          onClick={() => setTabFilter(tabFilter === 'active' ? 'all' : 'active')}
        >
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Đang hoạt động</span>
            <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-2xl tabular-nums text-emerald-600 dark:text-emerald-400">
              {stats.active}
            </span>
            <span className="text-xs text-muted-foreground">sẵn sàng</span>
          </div>
        </Card>

        {/* Nghỉ phép / Tạm dừng */}
        <Card
          className={cn(
            'flex cursor-pointer flex-col gap-1 p-3.5 transition-all hover:border-amber-500/50',
            tabFilter === 'leave' && 'border-amber-500 ring-1 ring-amber-500/20 bg-amber-50/50 dark:bg-amber-950/20',
          )}
          onClick={() => setTabFilter(tabFilter === 'leave' ? 'all' : 'leave')}
        >
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Nghỉ phép / Tạm dừng</span>
            <Clock className="size-4 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-2xl tabular-nums text-amber-600 dark:text-amber-400">
              {stats.leave}
            </span>
            <span className="text-xs text-muted-foreground">vắng mặt</span>
          </div>
        </Card>
      </div>

      {/* Bảng dữ liệu chính */}
      <Card className="flex min-h-0 flex-1 flex-col p-4 shadow-xs">
        <DataTable
          fillHeight
          columns={columns}
          rows={filteredItems}
          getRowId={(r) => r.employee_id}
          onRowClick={(r) => navigate(appRoutes.approvalSeal.clerkDetail(r.anchor_id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có phân công văn thư nào phù hợp."
          storageKey="approval-seal.clerks"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'văn thư',
          }}
          toolbar={
            <div className="flex flex-1 flex-wrap items-center gap-3">
              {/* Ô tìm kiếm */}
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="h-9 pl-9 text-xs"
                  placeholder="Tìm theo tên, mã văn thư, công ty…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              {/* Lọc theo công ty */}
              {canReadCompany && (
                <SearchSelect
                  value={companyId}
                  onChange={(v) => {
                    setCompanyId(v || ALL)
                    setPage(1)
                  }}
                  options={[
                    { value: ALL, label: 'Tất cả công ty' },
                    ...(companies?.items ?? []).map((c) => ({ value: String(c.id), label: c.name })),
                  ]}
                  placeholder="Lọc theo công ty"
                  searchPlaceholder="Tìm công ty…"
                  searchInTrigger
                  size="sm"
                  className="w-full md:w-60"
                />
              )}

              {/* Tab phân loại nhanh dạng chip buttons */}
              <div className="ml-auto hidden items-center gap-1.5 lg:flex">
                <Button
                  variant={tabFilter === 'all' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="h-8 text-xs"
                  onClick={() => setTabFilter('all')}
                >
                  Tất cả ({stats.total})
                </Button>
                <Button
                  variant={tabFilter === 'head' ? 'secondary' : 'ghost'}
                  size="sm"
                  className={cn('h-8 text-xs', tabFilter === 'head' && 'text-indigo-600 font-semibold dark:text-indigo-400')}
                  onClick={() => setTabFilter('head')}
                >
                  <ShieldCheck className="mr-1 size-3.5 text-indigo-600 dark:text-indigo-400" />
                  Đa pháp nhân ({stats.head})
                </Button>
                <Button
                  variant={tabFilter === 'active' ? 'secondary' : 'ghost'}
                  size="sm"
                  className={cn('h-8 text-xs', tabFilter === 'active' && 'text-emerald-600 font-semibold dark:text-emerald-400')}
                  onClick={() => setTabFilter('active')}
                >
                  <CheckCircle2 className="mr-1 size-3.5 text-emerald-600 dark:text-emerald-400" />
                  Hoạt động ({stats.active})
                </Button>
              </div>
            </div>
          }
        />
      </Card>
    </PageContainer>
  )
}
