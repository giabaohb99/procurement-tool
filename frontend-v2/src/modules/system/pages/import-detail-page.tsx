import { ArrowLeft, Download, Loader2, Undo2, Upload } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDateTime } from '@/shared/utils/format-date'

import { ImportStatusBadge } from '../components/import-status-badge'
import {
  IMPORT_CATEGORY_LABELS,
  IMPORT_LEVEL_ERROR,
  IMPORT_LEVEL_LABELS,
  IMPORT_LEVEL_REVIEW,
  IMPORT_LEVEL_WARNING,
  IMPORT_MODE_APPLY,
  IMPORT_MODE_DRY_RUN,
  IMPORT_MODE_LABELS,
  IMPORT_MODULE_LABELS,
  IMPORT_STATUS_DONE,
  IMPORT_STATUS_FAILED,
} from '../config/import-meta'
import {
  useCommitImport,
  useDownloadImportFile,
  useImportBatch,
  useImportLogs,
  useRevertImport,
} from '../hooks/use-imports'
import type { ImportLog } from '../types/import-batch'

const LEVEL_TONES: Record<number, string> = {
  [IMPORT_LEVEL_WARNING]: 'border-amber-500 text-amber-600 bg-amber-50 dark:bg-amber-950/40',
  [IMPORT_LEVEL_REVIEW]: 'border-violet-500 text-violet-600 bg-violet-50 dark:bg-violet-950/40',
  [IMPORT_LEVEL_ERROR]: 'border-rose-500 text-rose-600 bg-rose-50 dark:bg-rose-950/40',
}

/** Tab lọc log — 'all' = mọi mức. */
const LOG_TABS: { key: string; label: string }[] = [
  { key: 'all', label: 'Tất cả' },
  { key: String(IMPORT_LEVEL_ERROR), label: 'Lỗi' },
  { key: String(IMPORT_LEVEL_REVIEW), label: 'Cần rà soát' },
  { key: String(IMPORT_LEVEL_WARNING), label: 'Cảnh báo' },
]

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground">{label}</p>
      <ReadOnlyValue>{value}</ReadOnlyValue>
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-lg border bg-muted/20 p-3 text-center">
      <p className={`text-xl font-bold ${value ? tone ?? 'text-foreground' : 'text-muted-foreground'}`}>
        {value}
      </p>
      <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
    </div>
  )
}

export function ImportDetailPage() {
  const navigate = useNavigate()
  const { id: rawId } = useParams()
  const { can } = usePermission()
  const id = Number(rawId)

  const [levelTab, setLevelTab] = useState('all')
  const [logPage, setLogPage] = useState(1)
  const [logPageSize, setLogPageSize] = useState<number>(appConfig.defaultPageSize)
  const [confirmRevert, setConfirmRevert] = useState(false)
  const [confirmCommit, setConfirmCommit] = useState(false)

  const { data: batch, isLoading, isError } = useImportBatch(id)
  const logParams = {
    page: logPage,
    page_size: logPageSize,
    level: levelTab === 'all' ? undefined : Number(levelTab),
  }
  const { data: logData, isLoading: logsLoading, isError: logsError, refetch: refetchLogs } =
    useImportLogs(id, logParams)

  const revertMutation = useRevertImport()
  const commitMutation = useCommitImport()
  const downloadMutation = useDownloadImportFile()

  if (!Number.isFinite(id) || id <= 0) {
    return (
      <PageContainer fill>
        <PageHeader title="Không tìm thấy lần import" />
      </PageContainer>
    )
  }

  const canRevert =
    !!batch &&
    batch.status === IMPORT_STATUS_DONE &&
    batch.mode === IMPORT_MODE_APPLY &&
    can('import', 'delete')

  // Bản chạy thử đã hoàn tất -> cho phép "Ghi thật" (thử → xem → ghi).
  const canCommit =
    !!batch &&
    batch.status === IMPORT_STATUS_DONE &&
    batch.mode === IMPORT_MODE_DRY_RUN &&
    can('import', 'create')

  const logColumns: DataTableColumn<ImportLog>[] = [
    { key: 'sheet', header: 'Sheet', width: 110, cell: (r) => r.sheet || '—' },
    {
      key: 'row_no',
      header: 'Dòng',
      width: 70,
      cell: (r) => <span className="font-mono text-xs">{r.row_no ?? '—'}</span>,
    },
    {
      key: 'level',
      header: 'Loại',
      width: 110,
      cell: (r) => (
        <Badge variant="outline" className={LEVEL_TONES[r.level] || 'border-slate-300 text-slate-600 bg-slate-50'}>
          {IMPORT_LEVEL_LABELS[r.level] || r.level}
        </Badge>
      ),
    },
    {
      key: 'category',
      header: 'Phân loại',
      width: 150,
      cell: (r) => (r.category ? IMPORT_CATEGORY_LABELS[r.category] || r.category : '—'),
    },
    {
      key: 'message',
      header: 'Thông báo',
      width: 320,
      wrap: true,
      cell: (r) => r.message || '—',
    },
    {
      key: 'ref_key',
      header: 'Tham chiếu',
      width: 170,
      cell: (r) => (
        <span className="text-xs">
          {r.ref_key || '—'}
          {r.target_code && <span className="text-muted-foreground"> → {r.target_code}</span>}
        </span>
      ),
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title={
          <span className="inline-flex flex-wrap items-center gap-2">
            <span>
              Import #{id}
              {batch ? ` — ${IMPORT_MODULE_LABELS[batch.module] || batch.module}` : ''}
            </span>
            {batch && <ImportStatusBadge status={batch.status} className="mt-1" />}
          </span>
        }
        leading={
          <Button
            variant="ghost"
            size="sm"
            className="mt-0.5 h-8 w-8 p-0"
            title="Quay lại danh sách"
            onClick={() => navigate(appRoutes.system.imports)}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        actions={
          <div className="flex items-center gap-2">
            {!!batch?.file_id && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                disabled={downloadMutation.isPending}
                onClick={() => downloadMutation.mutate({ id, filename: batch.filename })}
              >
                {downloadMutation.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Download className="size-4" />
                )}
                Tải file
              </Button>
            )}
            {canCommit && (
              <Button
                size="sm"
                className="gap-1.5 bg-amber-600 text-white hover:bg-amber-700"
                disabled={commitMutation.isPending}
                onClick={() => setConfirmCommit(true)}
              >
                {commitMutation.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Upload className="size-4" />
                )}
                Ghi thật
              </Button>
            )}
            {canRevert && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 border-rose-500 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                disabled={revertMutation.isPending}
                onClick={() => setConfirmRevert(true)}
              >
                {revertMutation.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Undo2 className="size-4" />
                )}
                Hoàn tác
              </Button>
            )}
          </div>
        }
      />

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 size-5 animate-spin" /> Đang tải…
        </div>
      )}

      {isError && (
        <Card className="p-6 text-center text-destructive">Không tải được thông tin lần import.</Card>
      )}

      {batch && (
        <div className="flex min-h-0 flex-1 flex-col gap-4">
          {/* Khối thông tin + thống kê */}
          <Card className="p-4">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
              <InfoField label="Người nhập" value={batch.created_by_name || '—'} />
              <InfoField label="Bắt đầu" value={formatDateTime(batch.created_at) || '—'} />
              <InfoField label="Kết thúc" value={formatDateTime(batch.finished_at) || '—'} />
              <InfoField label="Chế độ" value={IMPORT_MODE_LABELS[batch.mode] || String(batch.mode)} />
              <InfoField label="Tên file" value={batch.filename} />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
              <Stat label="Tổng dòng" value={batch.total_rows} />
              <Stat label="Tạo" value={batch.created_count} tone="text-emerald-600" />
              <Stat label="Cập nhật" value={batch.updated_count} tone="text-blue-600" />
              <Stat label="Xóa" value={batch.deleted_count} tone="text-rose-600" />
              <Stat label="Bỏ qua" value={batch.skipped_count} />
              <Stat label="Cảnh báo" value={batch.warning_count} tone="text-amber-600" />
              <Stat label="Rà soát" value={batch.review_count} tone="text-violet-600" />
              <Stat label="Lỗi" value={batch.error_count} tone="text-rose-600" />
            </div>

            {batch.status === IMPORT_STATUS_FAILED && batch.error_summary && (
              <pre className="mt-4 max-h-48 overflow-auto rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
                {batch.error_summary}
              </pre>
            )}
          </Card>

          {/* Nhật ký từng dòng */}
          <Card className="flex min-h-0 flex-1 flex-col p-4">
            <DataTable
              fillHeight
              columns={logColumns}
              rows={logData?.items}
              getRowId={(r) => String(r.id)}
              isLoading={logsLoading}
              isError={logsError}
              onRefresh={() => refetchLogs()}
              emptyMessage="Không có dòng nhật ký."
              storageKey="system.import_logs"
              // Thẻ lọc mức log nằm CHUNG HÀNG với nút Tải lại / Cột của bảng.
              toolbar={
                <Tabs
                  value={levelTab}
                  onValueChange={(v) => {
                    setLevelTab(v)
                    setLogPage(1)
                  }}
                >
                  <TabsList>
                    {LOG_TABS.map((tab) => (
                      <TabsTrigger key={tab.key} value={tab.key}>
                        {tab.label}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                </Tabs>
              }
              pagination={{
                page: logPage,
                pageSize: logPageSize,
                total: logData?.total ?? 0,
                onPageChange: setLogPage,
                onPageSizeChange: setLogPageSize,
                unitLabel: 'dòng',
              }}
            />
          </Card>
        </div>
      )}

      <AlertDialog open={confirmRevert} onOpenChange={setConfirmRevert}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Hoàn tác lần import này?</AlertDialogTitle>
            <AlertDialogDescription>
              Phiếu do lần này <strong>TẠO</strong> sẽ bị xoá, phiếu bị <strong>SỬA</strong> sẽ khôi
              phục về trước khi import. Hành động này không thể đảo ngược.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={revertMutation.isPending}>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className="bg-rose-600 text-white hover:bg-rose-700"
              disabled={revertMutation.isPending}
              onClick={(e) => {
                e.preventDefault()
                revertMutation.mutate(id, { onSuccess: () => setConfirmRevert(false) })
              }}
            >
              {revertMutation.isPending && <Loader2 className="mr-1.5 size-4 animate-spin" />}
              Hoàn tác
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={confirmCommit} onOpenChange={setConfirmCommit}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Ghi thật dữ liệu từ bản chạy thử?</AlertDialogTitle>
            <AlertDialogDescription>
              Hệ thống sẽ chạy lại đúng file này ở chế độ <strong>Ghi thật</strong> và lưu vào hệ
              thống. Bạn có thể <strong>Hoàn tác</strong> sau khi ghi nếu cần.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={commitMutation.isPending}>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className="bg-amber-600 text-white hover:bg-amber-700"
              disabled={commitMutation.isPending}
              onClick={(e) => {
                e.preventDefault()
                commitMutation.mutate(id, {
                  onSuccess: (created) => {
                    setConfirmCommit(false)
                    navigate(appRoutes.system.importDetail(created.id))
                  },
                })
              }}
            >
              {commitMutation.isPending && <Loader2 className="mr-1.5 size-4 animate-spin" />}
              Ghi thật
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageContainer>
  )
}
