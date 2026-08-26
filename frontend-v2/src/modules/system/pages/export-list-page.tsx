import { Download, Loader2, RotateCw, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
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
import { formatFileSize } from '@/shared/utils/format-file-size'

import { ExportRunDialog } from '../components/export-run-dialog'
import { ModuleBadge } from '../components/module-badge'
import { EXPORT_FORMAT_LABELS } from '../config/export-meta'
import { useDownloadExportFile, useExports } from '../hooks/use-exports'
import type { ExportLog } from '../types/export-log'

const ALL = 'all'

export function ExportListPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [entityFilter, setEntityFilter] = useState<string>(ALL)
  const [fmtFilter, setFmtFilter] = useState<string>(ALL)
  const [creatorFilter, setCreatorFilter] = useState<string>(ALL)
  const [filename, setFilename] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [runOpen, setRunOpen] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  const downloadMutation = useDownloadExportFile()

  function resetTo1<T>(setter: (v: T) => void) {
    return (value: T) => {
      setter(value)
      setPage(1)
    }
  }

  const params = useMemo(
    () => ({
      page,
      page_size: pageSize,
      entity: entityFilter === ALL ? undefined : entityFilter,
      fmt: fmtFilter === ALL ? undefined : fmtFilter,
      created_by_name: creatorFilter === ALL ? undefined : creatorFilter,
      filename: filename || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [page, pageSize, entityFilter, fmtFilter, creatorFilter, filename, dateFrom, dateTo],
  )

  const { data, isLoading, isError, refetch } = useExports(params)
  const creators = data?.creators ?? []
  // Danh sách đối tượng đã từng xuất — cho bộ lọc "Đối tượng".
  const entityOptions = useMemo(() => {
    const map = new Map<string, string>()
    for (const it of data?.items ?? []) map.set(it.entity, it.entity_label)
    return [...map.entries()]
  }, [data?.items])

  const columns: DataTableColumn<ExportLog>[] = [
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
      width: 160,
      cell: (r) => (
        <span className="font-medium text-foreground">{formatDateTime(r.created_at) || '—'}</span>
      ),
    },
    {
      key: 'created_by_name',
      header: 'Người xuất',
      width: 160,
      cell: (r) => r.created_by_name || '—',
    },
    {
      key: 'phan_he',
      header: 'Phân hệ',
      width: 130,
      cell: (r) => <ModuleBadge moduleId={r.module} />,
    },
    {
      key: 'entity',
      header: 'Bảng',
      width: 160,
      cell: (r) => (
        <Badge variant="secondary" className="font-normal">
          {r.entity_label || r.entity}
        </Badge>
      ),
    },
    {
      key: 'fmt',
      header: 'Định dạng',
      width: 120,
      cell: (r) => (
        <Badge variant="secondary" className="font-normal">
          {EXPORT_FORMAT_LABELS[r.fmt] || r.fmt}
        </Badge>
      ),
    },
    {
      key: 'row_count',
      header: 'Số dòng',
      width: 90,
      cell: (r) => <span className="font-medium text-foreground">{r.row_count}</span>,
    },
    {
      key: 'file_size',
      header: 'Dung lượng',
      width: 110,
      cell: (r) => (
        <span className="font-mono text-xs text-muted-foreground">{formatFileSize(r.file_size ?? 0)}</span>
      ),
    },
    {
      key: 'filename',
      header: 'Tên file',
      width: 240,
      cell: (r) => (
        <span className="block max-w-[240px] truncate" title={r.filename}>
          {r.filename}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Thao tác',
      width: 90,
      hideable: false,
      cell: (r) =>
        r.has_file ? (
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            title="Tải file"
            aria-label="Tải file"
            disabled={downloadingId === r.id}
            onClick={(e) => {
              // Chặn nổi bọt để bấm nút KHÔNG mở trang chi tiết của dòng.
              e.stopPropagation()
              setDownloadingId(r.id)
              downloadMutation.mutate(
                { id: r.id, filename: r.filename },
                { onSettled: () => setDownloadingId(null) },
              )
            }}
          >
            {downloadingId === r.id ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Download className="size-4" />
            )}
          </Button>
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Quản lý xuất dữ liệu"
        description="Tải dữ liệu các bảng ra CSV/XLSX và theo dõi nhật ký các lần đã xuất"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()} title="Làm mới danh sách">
              <RotateCw className="size-4" />
            </Button>
            <Button size="sm" className="gap-2" onClick={() => setRunOpen(true)}>
              <Download className="size-4" />
              Xuất dữ liệu
            </Button>
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
          onRowClick={(r) => navigate(appRoutes.system.exportDetail(r.id))}
          emptyMessage="Chưa có lần xuất nào."
          storageKey="system.exports"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'lần xuất',
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative w-56 max-w-xs">
                <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Tìm theo tên file…"
                  value={filename}
                  onChange={(e) => resetTo1(setFilename)(e.target.value)}
                  className="pl-8"
                />
              </div>

              {entityOptions.length > 0 && (
                <Select value={entityFilter} onValueChange={resetTo1(setEntityFilter)}>
                  <SelectTrigger className="h-9 w-40 text-xs">
                    <SelectValue placeholder="Đối tượng" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL}>Tất cả đối tượng</SelectItem>
                    {entityOptions.map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              <Select value={fmtFilter} onValueChange={resetTo1(setFmtFilter)}>
                <SelectTrigger className="h-9 w-32 text-xs">
                  <SelectValue placeholder="Định dạng" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi định dạng</SelectItem>
                  <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                </SelectContent>
              </Select>

              {creators.length > 0 && (
                <Select value={creatorFilter} onValueChange={resetTo1(setCreatorFilter)}>
                  <SelectTrigger className="h-9 w-40 text-xs">
                    <SelectValue placeholder="Người xuất" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL}>Mọi người xuất</SelectItem>
                    {creators.map((name) => (
                      <SelectItem key={name} value={name}>
                        {name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              <DateRangePicker
                from={dateFrom}
                to={dateTo}
                onChange={(from, to) => {
                  setDateFrom(from)
                  setDateTo(to)
                  setPage(1)
                }}
              />
            </div>
          }
        />
      </Card>

      <ExportRunDialog open={runOpen} onOpenChange={setRunOpen} />
    </PageContainer>
  )
}
