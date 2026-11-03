// bao-CR-718 — chi tiết MỘT lô xuất toàn bộ chạy nền (`/procurement/customs-prices/exports/:id`). Đây là đích của
// chuông "xuất xong" backend gửi. Lô còn chờ / đang xuất thì hỏi lại mỗi 3 giây (`useCustomsExportBatch`), thanh
// tiến độ + bảng tệp tự lớn dần; xong thì thôi hỏi. Tệp đã ghi xong tải được ngay, kể cả khi lô chưa xong hẳn.
//
// Gác quyền: mục menu ẨN `customsExports` khai `action: 'export'` nên `canAccessRoute` đòi `customs_price.export`.
// Backend còn chặn thêm: chỉ người xuất (hoặc có export phạm vi tất cả) mới xem / tải; chỉ người xuất mới dừng.
import { ArrowLeft, Download, Loader2, Square } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useBackTarget } from '@/shared/hooks/use-back-target'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Progress } from '@/shared/ui/progress'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'

import { downloadCustomsExportFile } from '../api/customs-api'
import { CustomsExportStatusBadge } from '../components/customs/customs-export-status-badge'
import { useCancelCustomsExportBatch, useCustomsExportBatch } from '../hooks/use-customs'
import { CUSTOMS_EXPORT_STATUS, type CustomsExportBatch, type CustomsExportFile } from '../types/customs'
import { exportProgressPercent, formatExportExpiry } from '../utils/customs-export'

function errorStatus(error: unknown): number | undefined {
  return (error as { response?: { status?: number } } | null)?.response?.status
}

function InfoRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
      <dt className="shrink-0 text-muted-foreground sm:w-28">{label}</dt>
      <dd className="min-w-0 break-words">{children}</dd>
    </div>
  )
}

export function CustomsExportDetailPage() {
  const { id } = useParams<{ id: string }>()
  const batchId = Number(id) > 0 ? Number(id) : null
  const navigate = useNavigate()
  const back = useBackTarget(appRoutes.procurement.customsExports)
  const { data: batch, isLoading, error } = useCustomsExportBatch(batchId)

  const backButton = (
    <Button
      type="button"
      variant="outline"
      size="icon"
      title="Quay lại Lô xuất của tôi"
      aria-label="Quay lại Lô xuất của tôi"
      onClick={() => navigate(back.url)}
    >
      <ArrowLeft className="size-4" />
    </Button>
  )

  if (isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải lô xuất…</p>
      </PageContainer>
    )
  }
  if (!batch) {
    const status = errorStatus(error)
    return (
      <PageContainer>
        <PageHeader leading={backButton} title={batchId ? `Lô xuất #${batchId}` : 'Lô xuất'} />
        <p className="text-sm text-muted-foreground">
          {status === 403
            ? extractErrorMessage(error)
            : 'Không tìm thấy lô xuất này — có thể đường dẫn sai hoặc lô đã bị xóa.'}
        </p>
      </PageContainer>
    )
  }
  return <ExportBatchView batch={batch} backButton={backButton} />
}

/** Nút tải MỘT tệp. Tắt khi tệp đã bị dọn; `useSingleFlight` chặn bấm dồn (một cú bấm = một lần tải). */
function ExportFileDownloadButton({ batchId, file }: { batchId: number; file: CustomsExportFile }) {
  const singleFlight = useSingleFlight()
  const [downloading, setDownloading] = useState(false)

  return (
    <Button
      type="button"
      size="sm"
      variant="outline"
      disabled={!file.available || downloading}
      title={file.available ? `Tải ${file.filename}` : 'Tệp đã quá hạn giữ và bị dọn — tạo lô xuất mới'}
      aria-label={`Tải tệp ${file.part}`}
      onClick={(event) => {
        event.stopPropagation()
        void singleFlight(async () => {
          setDownloading(true)
          try {
            await downloadCustomsExportFile(batchId, file.part, file.filename)
          } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Không tải được tệp')
          } finally {
            setDownloading(false)
          }
        })
      }}
    >
      {downloading ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
      Tải
    </Button>
  )
}

function ExportBatchView({ batch, backButton }: { batch: CustomsExportBatch; backButton: ReactNode }) {
  const cancel = useCancelCustomsExportBatch()
  const singleFlight = useSingleFlight()
  const percent = exportProgressPercent(batch)

  function stop() {
    void singleFlight(async () => {
      const ok = await confirm({
        title: `Dừng lô xuất #${batch.id}`,
        message:
          'Dừng ghi các tệp còn lại? Tệp đã xong vẫn tải được tới hạn giữ. Muốn xuất tiếp phải tạo lô mới.',
        confirmLabel: 'Dừng lô',
      })
      if (!ok) return
      try {
        await cancel.mutateAsync(batch.id)
        toast.success(`Đã dừng lô xuất #${batch.id}`)
      } catch (err) {
        toast.error(extractErrorMessage(err))
      }
    })
  }

  const columns = useMemo<DataTableColumn<CustomsExportFile>[]>(
    () => [
      { key: 'part', header: 'Tệp', width: 70, hideable: false, cell: (f) => `${f.part}/${batch.file_count}` },
      //  Nút Tải đứng ngay sau số tệp: màn hẹp không phải cuộn ngang qua tên tệp dài mới bấm được.
      {
        key: 'download',
        header: 'Tải',
        width: 110,
        hideable: false,
        cell: (f) => <ExportFileDownloadButton batchId={batch.id} file={f} />,
      },
      { key: 'filename', header: 'Tên tệp', width: 320, wrap: true, cell: (f) => f.filename },
      {
        key: 'rows',
        header: 'Số dòng',
        width: 110,
        align: 'right',
        cell: (f) => f.rows.toLocaleString('vi-VN'),
      },
      { key: 'size', header: 'Dung lượng', width: 110, align: 'right', cell: (f) => formatFileSize(f.size) },
    ],
    [batch.id, batch.file_count],
  )

  return (
    <PageContainer className="flex flex-col gap-3">
      <PageHeader
        leading={backButton}
        title={
          <span className="flex flex-wrap items-center gap-2">
            Lô xuất #{batch.id}
            <CustomsExportStatusBadge batch={batch} />
          </span>
        }
        description="Xuất toàn bộ dữ liệu Tra cứu thị trường theo bộ lọc, chia mỗi tệp tối đa 50.000 dòng."
        actions={
          batch.active && (
            <Button type="button" variant="destructive" disabled={cancel.isPending} onClick={stop}>
              <Square className="size-4" />
              Dừng
            </Button>
          )
        }
      />

      <Card className="gap-3 p-4">
        <dl className="grid gap-2 text-sm">
          <InfoRow label="Bộ lọc">{batch.filter_summary || 'Toàn bộ dữ liệu'}</InfoRow>
          <InfoRow label="Lúc tạo">{formatDateTime(batch.created_at)}</InfoRow>
          {batch.finished_at && <InfoRow label="Kết thúc">{formatDateTime(batch.finished_at)}</InfoRow>}
          <InfoRow label="Hạn giữ tệp">{formatExportExpiry(batch.expires_at)}</InfoRow>
        </dl>

        <div className="flex flex-col gap-1.5">
          <Progress value={percent} aria-label="Tiến độ xuất" />
          <p className="text-sm text-muted-foreground">
            Tệp xong: <strong className="text-foreground">{batch.files_done}/{batch.file_count}</strong> · Dòng đã
            ghi:{' '}
            <strong className="text-foreground">
              {batch.rows_done.toLocaleString('vi-VN')}/{batch.total_rows.toLocaleString('vi-VN')}
            </strong>
            {batch.active && ' · đang tự cập nhật, xong sẽ báo chuông'}
          </p>
        </div>

        {batch.error && (
          <p role="alert" className="text-sm text-destructive">
            Lỗi: {batch.error}
          </p>
        )}
        {batch.status === CUSTOMS_EXPORT_STATUS.expired && (
          <p className="text-sm text-muted-foreground">
            Lô đã quá hạn giữ, các tệp đã được dọn. Cần dữ liệu thì tạo lô xuất mới từ Tra cứu thị trường.
          </p>
        )}
      </Card>

      <DataTable
        columns={columns}
        rows={batch.files}
        getRowId={(f) => f.part}
        emptyMessage={batch.active ? 'Đang ghi tệp đầu tiên…' : 'Lô này không có tệp nào.'}
        mobileCard={(f) => (
          <div className="flex items-center justify-between gap-3 text-sm">
            <div className="flex min-w-0 flex-col gap-0.5">
              <span className="font-medium">
                Tệp {f.part}/{batch.file_count}
              </span>
              <span className="text-muted-foreground">
                {f.rows.toLocaleString('vi-VN')} dòng · {formatFileSize(f.size)}
              </span>
            </div>
            <ExportFileDownloadButton batchId={batch.id} file={f} />
          </div>
        )}
      />
    </PageContainer>
  )
}
