import { ArrowLeft, Download, FileSpreadsheet, FileText, Loader2 } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'

import { EXPORT_FORMAT_LABELS } from '../config/export-meta'
import { useDownloadExportFile, useExportDetail } from '../hooks/use-exports'

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground">{label}</p>
      <ReadOnlyValue>{value}</ReadOnlyValue>
    </div>
  )
}

function FormatBadge({ fmt }: { fmt: string }) {
  const isXlsx = fmt === 'xlsx'
  return (
    <Badge
      variant="outline"
      className={cn(
        'mt-1 gap-1',
        isXlsx
          ? 'border-emerald-500 bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40'
          : 'border-sky-500 bg-sky-50 text-sky-600 dark:bg-sky-950/40',
      )}
    >
      {isXlsx ? <FileSpreadsheet className="size-3" /> : <FileText className="size-3" />}
      {EXPORT_FORMAT_LABELS[fmt] || fmt}
    </Badge>
  )
}

export function ExportDetailPage() {
  const navigate = useNavigate()
  const { id: rawId } = useParams()
  const id = Number(rawId)

  const { data: item, isLoading, isError } = useExportDetail(id)
  const downloadMutation = useDownloadExportFile()

  if (!Number.isFinite(id) || id <= 0) {
    return (
      <PageContainer fill>
        <PageHeader title="Không tìm thấy lần xuất" />
      </PageContainer>
    )
  }

  return (
    <PageContainer fill>
      <PageHeader
        title={
          <span className="inline-flex flex-wrap items-center gap-2">
            <span>
              Export #{id}
              {item ? ` — ${item.entity_label || item.entity}` : ''}
            </span>
            {item && <FormatBadge fmt={item.fmt} />}
          </span>
        }
        leading={
          <Button
            variant="ghost"
            size="sm"
            className="mt-0.5 h-8 w-8 p-0"
            title="Quay lại danh sách"
            onClick={() => navigate(appRoutes.system.exports)}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        actions={
          item?.has_file && (
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              disabled={downloadMutation.isPending}
              onClick={() => downloadMutation.mutate({ id, filename: item.filename })}
            >
              {downloadMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Download className="size-4" />
              )}
              Tải file
            </Button>
          )
        }
      />

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 size-5 animate-spin" /> Đang tải…
        </div>
      )}

      {isError && (
        <Card className="p-6 text-center text-destructive">Không tải được thông tin lần xuất.</Card>
      )}

      {item && (
        <Card className="p-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
            <InfoField label="Người xuất" value={item.created_by_name || '—'} />
            <InfoField label="Thời gian" value={formatDateTime(item.created_at) || '—'} />
            <InfoField label="Đối tượng" value={item.entity_label || item.entity} />
            <InfoField label="Định dạng" value={EXPORT_FORMAT_LABELS[item.fmt] || item.fmt} />
            <InfoField label="Số dòng" value={String(item.row_count)} />
            <InfoField label="Dung lượng" value={formatFileSize(item.file_size ?? 0)} />
            <InfoField label="Tên file" value={item.filename} />
          </div>

          {!item.has_file && (
            <p className="mt-4 text-sm text-muted-foreground">
              Lần xuất này không còn file đã lưu để tải lại.
            </p>
          )}
        </Card>
      )}
    </PageContainer>
  )
}
