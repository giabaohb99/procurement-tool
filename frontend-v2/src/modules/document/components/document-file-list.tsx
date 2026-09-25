import { useMutation } from '@tanstack/react-query'
import { Download, FileText, Loader2 } from 'lucide-react'
import { useMemo } from 'react'
import { toast } from 'sonner'

import { downloadFile, extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { formatDate } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'
import type { DocumentVersionFile } from '../api/document-api'

interface DocumentFileListProps {
  files: DocumentVersionFile[]
  onOpen: (file: DocumentVersionFile) => void
}

/** `application/pdf` → `PDF`. Không nhận diện được thì lấy đuôi tên tệp. */
function fileKindLabel(file: DocumentVersionFile): string {
  const sub = file.content_type?.split('/').pop()
  if (sub) return sub.toUpperCase()
  const ext = file.filename.includes('.') ? file.filename.split('.').pop() : ''
  return ext ? ext.toUpperCase() : '—'
}

/**
 * Bảng danh sách tệp của tab «Tệp» (phase 09) khi văn bản có TỪ HAI TỆP trở
 * lên — bấm dòng mở khung xem chi tiết (`document-file-viewer-layout.tsx`).
 * Ca 0/1 tệp không đi qua bảng này, xem `document-files-tab.tsx`.
 */
export function DocumentFileList({ files, onOpen }: DocumentFileListProps) {
  const download = useMutation({
    mutationFn: (file: DocumentVersionFile) =>
      downloadFile(`/api/attachments/${file.id}/download`, file.filename),
    onError: (error) => toast.error(extractErrorMessage(error)),
  })

  const columns = useMemo<DataTableColumn<DocumentVersionFile>[]>(
    () => [
      {
        key: 'filename',
        header: 'Tên tệp',
        width: 320,
        hideable: false,
        cell: (file) => (
          <div className="flex min-w-0 items-center gap-2">
            <FileText className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate">{file.filename}</span>
          </div>
        ),
      },
      { key: 'kind', header: 'Loại', width: 90, cell: (file) => fileKindLabel(file) },
      { key: 'size', header: 'Dung lượng', width: 110, cell: (file) => formatFileSize(file.size) },
      {
        key: 'version_no',
        header: 'Phiên bản',
        width: 150,
        cell: (file) => (
          <div className="flex items-center gap-1.5">
            <span>{file.version_no || '—'}</span>
            {file.is_current_version && (
              <Badge variant="secondary" className="text-[11px]">
                Đang dùng
              </Badge>
            )}
          </div>
        ),
      },
      {
        key: 'created_by_name',
        header: 'Người tải',
        width: 160,
        cell: (file) => file.created_by_name || '—',
      },
      {
        key: 'created_at',
        header: 'Ngày',
        width: 110,
        cell: (file) => formatDate(file.created_at) || '—',
      },
      {
        key: 'actions',
        header: 'Tải về',
        width: 80,
        align: 'center',
        hideable: false,
        cell: (file) => (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            title="Tải về"
            disabled={download.isPending}
            onClick={(event) => {
              event.stopPropagation()
              download.mutate(file)
            }}
          >
            {download.isPending && download.variables?.id === file.id ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Download className="size-4" />
            )}
          </Button>
        ),
      },
    ],
    [download],
  )

  return (
    <Card className="p-4">
      <DataTable
        columns={columns}
        rows={files}
        getRowId={(file) => file.id}
        onRowClick={onOpen}
        storageKey="document.files"
        emptyMessage="Chưa có tệp nào."
      />
    </Card>
  )
}
