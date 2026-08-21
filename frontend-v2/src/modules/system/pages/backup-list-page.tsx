import {
  Database,
  Download,
  Info,
  Loader2,
  RotateCw,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'

import {
  useBackups,
  useDeleteBackup,
  useDownloadBackup,
  useRunBackup,
} from '../hooks/use-backups'
import type { DbBackupItem } from '../types/backup'

export function BackupListPage() {
  const { can } = usePermission()
  const canCreate = can('backup', 'create')
  const canDelete = can('backup', 'delete')

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data, isLoading, isError, refetch } = useBackups({
    page,
    page_size: pageSize,
  })

  const runMutation = useRunBackup()
  const downloadMutation = useDownloadBackup()
  const deleteMutation = useDeleteBackup()

  const columns: DataTableColumn<DbBackupItem>[] = [
    {
      key: 'id',
      header: '#',
      width: 60,
      hideable: false,
      cell: (r) => <span className="text-xs text-muted-foreground font-mono">#{r.id}</span>,
    },
    {
      key: 'started_at',
      header: 'Thời gian sao lưu',
      width: 170,
      cell: (r) => (
        <span className="font-medium text-foreground">
          {formatDateTime(r.started_at || r.created_at) || '—'}
        </span>
      ),
    },
    {
      key: 'source',
      header: 'Nguồn',
      width: 110,
      cell: (r) => (
        <Badge
          variant={r.source === 'manual' ? 'default' : 'secondary'}
          className={r.source === 'manual' ? 'bg-emerald-600 hover:bg-emerald-700' : ''}
        >
          {r.source === 'manual' ? 'Bấm tay' : 'Tự động'}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 130,
      cell: (r) => {
        if (r.status === 'running') {
          return (
            <Badge variant="outline" className="border-amber-500 text-amber-600 bg-amber-50 gap-1 animate-pulse">
              <Loader2 className="size-3 animate-spin" />
              Đang chạy...
            </Badge>
          )
        }
        if (r.status === 'success') {
          return (
            <Badge variant="outline" className="border-emerald-500 text-emerald-600 bg-emerald-50">
              Thành công
            </Badge>
          )
        }
        return (
          <Badge variant="destructive">
            Thất bại
          </Badge>
        )
      },
    },
    {
      key: 'size_bytes',
      header: 'Dung lượng',
      width: 110,
      cell: (r) => (
        <span className="font-mono text-xs text-foreground font-medium">
          {formatFileSize(r.size_bytes)}
        </span>
      ),
    },
    {
      key: 'created_by_name',
      header: 'Người thực hiện',
      width: 170,
      cell: (r) => r.created_by_name || 'Hệ thống (tự động)',
    },
    {
      key: 'message',
      header: 'Ghi chú / Thông báo',
      width: 250,
      wrap: true,
      cell: (r) => (
        <span className={r.status === 'failed' ? 'text-destructive font-medium' : 'text-muted-foreground'}>
          {r.message || '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Thao tác',
      width: 110,
      hideable: false,
      cell: (r) => (
        <div className="flex items-center justify-center gap-1">
          {r.status === 'success' && r.file_key && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Tải bản sao lưu về"
              disabled={downloadMutation.isPending}
              onClick={() => downloadMutation.mutate(r.id)}
            >
              <Download className="size-4 text-primary" />
            </Button>
          )}

          {canDelete && r.status !== 'running' && (
            <ConfirmIconButton
              icon={Trash2}
              title="Xóa bản sao lưu"
              confirmTitle="Xóa bản sao lưu CSDL này?"
              confirmDescription="Tệp sao lưu trên kho lưu trữ riêng cũng sẽ bị xóa vĩnh viễn. Hành động này không thể hoàn tác."
              destructive
              disabled={deleteMutation.isPending}
              onConfirm={() => deleteMutation.mutate(r.id)}
            />
          )}
        </div>
      ),
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Sao lưu CSDL"
        description="Quản lý và tạo bản sao lưu cơ sở dữ liệu hệ thống"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              title="Làm mới danh sách"
            >
              <RotateCw className="size-4" />
            </Button>

            {canCreate && (
              <Button
                onClick={() => runMutation.mutate()}
                disabled={runMutation.isPending}
                className="gap-2"
              >
                {runMutation.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Database className="size-4" />
                )}
                Sao lưu ngay
              </Button>
            )}
          </div>
        }
      />

      {/* Info Banner */}
      <div className="mb-4 flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-200">
        <Info className="mt-0.5 size-4 shrink-0 text-blue-600 dark:text-blue-400" />
        <div className="space-y-1">
          <p className="font-semibold text-sm">Cơ chế sao lưu dữ liệu tự động:</p>
          <p>
            Hệ thống tự động sao lưu CSDL <strong className="font-semibold">2 lần/ngày</strong> (vào lúc{' '}
            <strong className="font-semibold">01:00</strong> và <strong className="font-semibold">13:00</strong>, giờ VN) và tự động tải tệp nén mã hóa lên kho lưu trữ riêng.
          </p>
          <p>
            Hệ thống tự động giữ lại tối đa <strong className="font-semibold">{data?.keep ?? 30} bản sao lưu mới nhất</strong>, các bản cũ hơn sẽ tự giải phóng. Tệp tải về được bảo mật bằng liên kết tạm thời hết hạn sau 10 phút.
          </p>
        </div>
      </div>

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => String(r.id)}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          emptyMessage="Chưa có bản sao lưu CSDL nào."
          storageKey="system.backups"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'bản sao lưu',
          }}
        />
      </Card>
    </PageContainer>
  )
}
