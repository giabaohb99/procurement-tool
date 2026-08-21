import { ExternalLink, Eye, RotateCw, Search, User } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router'

import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { formatDateTime } from '@/shared/utils/format-date'

import type { SystemAuditLogItem } from '../api/audit-log-api'
import { AUDIT_LOG_FILTER_FIELDS } from '../config/audit-log-filter-fields'
import { useAuditLogs } from '../hooks/use-audit-logs'

const ACTION_TONES: Record<string, string> = {
  create: 'border-emerald-500 text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40',
  update: 'border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-950/40',
  delete: 'border-rose-500 text-rose-600 bg-rose-50 dark:bg-rose-950/40',
  submitted: 'border-amber-500 text-amber-600 bg-amber-50 dark:bg-amber-950/40',
  approved: 'border-emerald-500 text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40',
  rejected: 'border-rose-500 text-rose-600 bg-rose-50 dark:bg-rose-950/40',
  paid: 'border-teal-500 text-teal-600 bg-teal-50 dark:bg-teal-950/40',
  cancelled: 'border-slate-400 text-slate-600 bg-slate-100 dark:bg-slate-800',
}

const ENTITY_LABELS: Record<string, string> = {
  product: 'Sản phẩm & Vật tư',
  contract: 'Hợp đồng',
  supplier: 'Nhà cung cấp',
  purchase_request: 'Yêu cầu mua hàng',
  purchase_order: 'Đơn mua hàng',
  payable: 'Công nợ',
  payment_request: 'Yêu cầu thanh toán',
  user: 'Tài khoản người dùng',
  role: 'Vai trò',
  setting: 'Cấu hình hệ thống',
  document: 'Văn bản',
  ticket: 'Phiếu hỗ trợ',
  backup: 'Sao lưu CSDL',
  employee: 'Nhân sự',
  company: 'Công ty',
  department: 'Phòng ban',
}

const ENTITY_ROUTES: Record<string, (id: number) => string> = {
  product: (id) => `/production/products/${id}`,
  contract: (id) => `/production/contracts/${id}`,
  supplier: (id) => `/production/suppliers/${id}`,
  purchase_request: (id) => `/procurement/purchase-requests/${id}`,
  purchase_order: (id) => `/procurement/purchase-orders/${id}`,
  ticket: (id) => `/support/tickets/${id}`,
  employee: (id) => `/hr/employees/${id}`,
  company: (id) => `/hr/companies/${id}`,
  department: (id) => `/hr/departments/${id}`,
}

export function AuditLogListPage() {
  return (
    <FilterProvider config={{ fields: AUDIT_LOG_FILTER_FIELDS }}>
      <AuditLogListContent />
    </FilterProvider>
  )
}

function AuditLogListContent() {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [selectedLog, setSelectedLog] = useState<SystemAuditLogItem | null>(null)

  const { queryParams, queryKey } = useFilterQuery()
  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue])

  // Trích xuất tham số từ ngày / đến ngày từ ConditionalFilter (hỗ trợ nhiều operator)
  const fromDate =
    (queryParams.from_date as string) ||
    (queryParams.from_date__gte as string) ||
    (queryParams.from_date__is as string) ||
    (queryParams.from_date__gte as string)

  const toDate =
    (queryParams.to_date as string) ||
    (queryParams.to_date__lte as string) ||
    (queryParams.to_date__is as string) ||
    (queryParams.to_date__lte as string)

  const params = {
    page,
    page_size: pageSize,
    search: debouncedValue || (queryParams.search as string),
    entity: queryParams.entity as string,
    action: queryParams.action as string,
    from_date: fromDate,
    to_date: toDate,
  }

  const { data, isLoading, isError, refetch } = useAuditLogs(params)

  const columns: DataTableColumn<SystemAuditLogItem>[] = [
    {
      key: 'id',
      header: '#',
      width: 60,
      hideable: false,
      cell: (r) => <span className="text-xs text-muted-foreground font-mono">#{r.id}</span>,
    },
    {
      key: 'at',
      header: 'Thời gian',
      width: 160,
      cell: (r) => (
        <span className="font-medium text-foreground">
          {formatDateTime(r.at) || '—'}
        </span>
      ),
    },
    {
      key: 'by',
      header: 'Người thực hiện',
      width: 170,
      cell: (r) => (
        <div className="flex items-center gap-1.5 font-medium text-foreground">
          <User className="size-3.5 text-muted-foreground shrink-0" />
          <span>{r.by || 'Hệ thống'}</span>
        </div>
      ),
    },
    {
      key: 'action',
      header: 'Hành động',
      width: 120,
      cell: (r) => (
        <Badge
          variant="outline"
          className={ACTION_TONES[r.action] || 'border-slate-300 text-slate-600 bg-slate-50'}
        >
          {r.action_label || r.action}
        </Badge>
      ),
    },
    {
      key: 'entity',
      header: 'Đối tượng',
      width: 170,
      cell: (r) => (
        <div className="flex items-center gap-1">
          <Badge variant="secondary" className="font-mono text-[11px]">
            {ENTITY_LABELS[r.entity] || r.entity}
          </Badge>
          {r.entity_id > 0 && (
            <span className="text-xs text-muted-foreground font-mono">#{r.entity_id}</span>
          )}
        </div>
      ),
    },
    {
      key: 'message',
      header: 'Chi tiết thao tác / Thông điệp',
      width: 300,
      wrap: true,
      cell: (r) => r.message || '—',
    },
    {
      key: 'actions',
      header: 'Chi tiết',
      width: 80,
      hideable: false,
      cell: (r) => (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          title="Xem chi tiết nhật ký"
          onClick={(e) => {
            e.stopPropagation()
            setSelectedLog(r)
          }}
        >
          <Eye className="size-4 text-primary" />
        </Button>
      ),
    },
  ]

  const entityTargetUrl = selectedLog && ENTITY_ROUTES[selectedLog.entity]
    ? ENTITY_ROUTES[selectedLog.entity](selectedLog.entity_id)
    : null

  return (
    <PageContainer fill>
      <PageHeader
        title="Nhật ký hệ thống"
        description="Theo dõi toàn bộ lịch sử thao tác (thêm, sửa, xóa, duyệt...) trên toàn hệ thống"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            title="Làm mới danh sách nhật ký"
          >
            <RotateCw className="size-4 mr-1.5" /> Làm mới
          </Button>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => String(r.id)}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          onRowClick={(r) => setSelectedLog(r)}
          emptyMessage="Không tìm thấy nhật ký thao tác nào."
          storageKey="system.audit_logs"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'nhật ký',
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative w-64 max-w-sm">
                <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Tìm theo nội dung ghi chú…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="pl-8"
                />
              </div>

              <ConditionalFilter />
            </div>
          }
        />
      </Card>

      {/* Popup / Dialog Xem Chi Tiết Log */}
      <Dialog open={!!selectedLog} onOpenChange={(open) => !open && setSelectedLog(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <div className="flex items-center justify-between gap-2 pr-6">
              <DialogTitle className="flex items-center gap-2 text-lg">
                <span>Chi tiết nhật ký thao tác</span>
                <span className="font-mono text-sm text-muted-foreground">#{selectedLog?.id}</span>
              </DialogTitle>
              {selectedLog && (
                <Badge
                  variant="outline"
                  className={ACTION_TONES[selectedLog.action] || 'border-slate-300 text-slate-600 bg-slate-50'}
                >
                  {selectedLog.action_label || selectedLog.action}
                </Badge>
              )}
            </div>
            <DialogDescription>
              Lịch sử ghi nhận thao tác của người dùng trên hệ thống
            </DialogDescription>
          </DialogHeader>

          {selectedLog && (
            <div className="space-y-4 py-2 text-sm">
              <div className="grid grid-cols-2 gap-4 rounded-lg border bg-muted/30 p-3">
                <div>
                  <span className="text-xs text-muted-foreground">Thời gian ghi nhận</span>
                  <p className="font-medium text-foreground">{formatDateTime(selectedLog.at) || '—'}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Người thực hiện</span>
                  <p className="font-medium text-foreground flex items-center gap-1.5">
                    <User className="size-3.5 text-muted-foreground" />
                    {selectedLog.by || 'Hệ thống'}
                    {selectedLog.by_id && (
                      <span className="text-xs text-muted-foreground font-mono">(#{selectedLog.by_id})</span>
                    )}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Đối tượng (Entity)</span>
                  <p className="font-medium text-foreground">
                    {ENTITY_LABELS[selectedLog.entity] || selectedLog.entity}{' '}
                    {selectedLog.entity_id > 0 && (
                      <span className="font-mono text-muted-foreground">#{selectedLog.entity_id}</span>
                    )}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Loại hành động</span>
                  <p className="font-medium text-foreground">{selectedLog.action_label} ({selectedLog.action})</p>
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="font-medium text-foreground">Nội dung chi tiết thao tác / Thông điệp:</span>
                <div className="max-h-60 overflow-y-auto rounded-md border bg-slate-950 p-3 font-mono text-xs text-slate-100 dark:bg-slate-900">
                  <pre className="whitespace-pre-wrap break-words">{selectedLog.message || '— Không có thông điệp phụ —'}</pre>
                </div>
              </div>

              {entityTargetUrl && (
                <div className="flex justify-end pt-2">
                  <Button
                    variant="outline"
                    className="gap-2"
                    onClick={() => {
                      setSelectedLog(null)
                      navigate(entityTargetUrl)
                    }}
                  >
                    <ExternalLink className="size-4" />
                    Mở trang {ENTITY_LABELS[selectedLog.entity] || selectedLog.entity} #{selectedLog.entity_id}
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </PageContainer>
  )
}
