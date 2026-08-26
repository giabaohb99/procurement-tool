import { RotateCw, Search, Upload } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
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

import { ImportUploadDialog } from '../components/import-upload-dialog'
import { ModuleBadge } from '../components/module-badge'
import { DATA_MODULES } from '../config/data-modules'
import { IMPORT_FILTER_FIELDS } from '../config/import-filter-fields'
import {
  IMPORT_MODE_APPLY,
  IMPORT_MODE_DRY_RUN,
  IMPORT_MODE_LABELS,
  IMPORT_MODULE_LABELS,
  IMPORT_STATUS_LABELS,
  importModuleId,
} from '../config/import-meta'
import { ImportStatusBadge } from '../components/import-status-badge'
import type { ImportListParams } from '../api/import-api'
import { useImports } from '../hooks/use-imports'
import type { ImportBatch } from '../types/import-batch'

const ALL = 'all'

/** Ô đếm nhỏ trong bảng — 0 thì mờ đi, >0 thì tô màu theo loại. */
function CountCell({ value, tone }: { value: number; tone?: string }) {
  if (!value) return <span className="text-muted-foreground">0</span>
  return <span className={tone ?? 'font-medium text-foreground'}>{value}</span>
}

export function ImportListPage() {
  return (
    <FilterProvider config={{ fields: IMPORT_FILTER_FIELDS }}>
      <ImportListContent />
    </FilterProvider>
  )
}

function ImportListContent() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canCreate = can('import', 'create')

  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [phanHe, setPhanHe] = useState<string>(ALL)
  const [statusFilter, setStatusFilter] = useState<string>(ALL)
  const [modeFilter, setModeFilter] = useState<string>(ALL)
  const [filename, setFilename] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [uploadOpen, setUploadOpen] = useState(false)

  const { queryParams, queryKey } = useFilterQuery()

  // Đổi bất kỳ điều kiện lọc nào -> tự về trang 1 (không thì đứng ở trang trống).
  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    phanHe,
    statusFilter,
    modeFilter,
    filename,
    dateFrom,
    dateTo,
  ])

  const params = useMemo<ImportListParams>(
    () => ({
      ...queryParams,
      page,
      page_size: pageSize,
      phan_he: phanHe === ALL ? undefined : phanHe,
      status: statusFilter === ALL ? undefined : Number(statusFilter),
      mode: modeFilter === ALL ? undefined : Number(modeFilter),
      filename: filename || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [queryParams, page, pageSize, phanHe, statusFilter, modeFilter, filename, dateFrom, dateTo],
  )

  const { data, isLoading, isError, refetch } = useImports(params)

  const columns: DataTableColumn<ImportBatch>[] = [
    {
      key: 'id',
      header: '#',
      width: 60,
      hideable: false,
      cell: (r) => <span className="font-mono text-xs text-muted-foreground">#{r.id}</span>,
    },
    {
      key: 'created_at',
      header: 'Thời gian',
      width: 150,
      cell: (r) => (
        <span className="font-medium text-foreground">{formatDateTime(r.created_at) || '—'}</span>
      ),
    },
    {
      key: 'created_by_name',
      header: 'Người nhập',
      width: 150,
      cell: (r) => r.created_by_name || '—',
    },
    {
      key: 'phan_he',
      header: 'Phân hệ',
      width: 130,
      cell: (r) => <ModuleBadge moduleId={importModuleId(r.module)} />,
    },
    {
      key: 'module',
      header: 'Bảng',
      width: 130,
      cell: (r) => (
        <Badge variant="secondary" className="font-normal">
          {IMPORT_MODULE_LABELS[r.module] || `#${r.module}`}
        </Badge>
      ),
    },
    {
      key: 'filename',
      header: 'Tên file',
      width: 220,
      cell: (r) => (
        <span className="block max-w-[220px] truncate" title={r.filename}>
          {r.filename}
        </span>
      ),
    },
    {
      key: 'mode',
      header: 'Chế độ',
      width: 110,
      cell: (r) => (
        <Badge variant="secondary" className="font-normal">
          {IMPORT_MODE_LABELS[r.mode] || r.mode}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 130,
      cell: (r) => <ImportStatusBadge status={r.status} />,
    },
    {
      key: 'created_count',
      header: 'Tạo',
      width: 70,
      cell: (r) => <CountCell value={r.created_count} tone="font-medium text-emerald-600" />,
    },
    {
      key: 'updated_count',
      header: 'Cập nhật',
      width: 80,
      cell: (r) => <CountCell value={r.updated_count} tone="font-medium text-blue-600" />,
    },
    {
      key: 'skipped_count',
      header: 'Bỏ qua',
      width: 80,
      cell: (r) => <CountCell value={r.skipped_count} />,
    },
    {
      key: 'warning_count',
      header: 'Cảnh báo',
      width: 90,
      cell: (r) => <CountCell value={r.warning_count} tone="font-medium text-amber-600" />,
    },
    {
      key: 'review_count',
      header: 'Rà soát',
      width: 80,
      cell: (r) => <CountCell value={r.review_count} tone="font-medium text-violet-600" />,
    },
    {
      key: 'error_count',
      header: 'Lỗi',
      width: 70,
      cell: (r) => <CountCell value={r.error_count} tone="font-medium text-rose-600" />,
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Quản lý nhập dữ liệu"
        description="Nạp dữ liệu hàng loạt từ tệp Excel và theo dõi kết quả xử lý từng lần"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()} title="Làm mới danh sách">
              <RotateCw className="size-4" />
            </Button>
            {canCreate && (
              <Button size="sm" className="gap-2" onClick={() => setUploadOpen(true)}>
                <Upload className="size-4" />
                Nhập dữ liệu
              </Button>
            )}
          </div>
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
          onRowClick={(r) => navigate(appRoutes.system.importDetail(r.id))}
          emptyMessage="Chưa có lần import nào."
          storageKey="system.imports"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'lần import',
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative w-56 max-w-xs">
                <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Tìm theo tên file…"
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  className="pl-8"
                />
              </div>

              <Select value={phanHe} onValueChange={setPhanHe}>
                <SelectTrigger className="h-9 w-40 text-xs">
                  <SelectValue placeholder="Phân hệ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả phân hệ</SelectItem>
                  {DATA_MODULES.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="h-9 w-36 text-xs">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {Object.entries(IMPORT_STATUS_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={modeFilter} onValueChange={setModeFilter}>
                <SelectTrigger className="h-9 w-32 text-xs">
                  <SelectValue placeholder="Chế độ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi chế độ</SelectItem>
                  <SelectItem value={String(IMPORT_MODE_DRY_RUN)}>Chạy thử</SelectItem>
                  <SelectItem value={String(IMPORT_MODE_APPLY)}>Ghi thật</SelectItem>
                </SelectContent>
              </Select>

              <DateRangePicker
                from={dateFrom}
                to={dateTo}
                onChange={(from, to) => {
                  setDateFrom(from)
                  setDateTo(to)
                }}
              />

              <ConditionalFilter />
            </div>
          }
        />
      </Card>

      <ImportUploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        onCreated={(id) => navigate(appRoutes.system.importDetail(id))}
      />
    </PageContainer>
  )
}
