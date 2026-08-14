import { Download, File, FileImage, FileText, Info, Paperclip, Trash2, Upload } from 'lucide-react'
import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import type { AttachmentFile } from '../api/purchase-request-support-api'
import {
  useDeletePurchaseRequestAttachment,
  useDocumentTypes,
  usePurchaseRequestAttachments,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'

interface DocumentAttachmentsCardProps {
  /** `purchase_request` hoặc `purchase_order` — quyết định chính sách file ở backend. */
  entity: string
  entityId: number
  canManage: boolean
}

/** Chứng từ của chứng từ mua hàng — dùng chung cho YCMH và ĐMH. */
export function DocumentAttachmentsCard({
  entity,
  entityId,
  canManage,
}: DocumentAttachmentsCardProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [docType, setDocType] = useState('other')
  const { data: files, isLoading, isError } = usePurchaseRequestAttachments(entity, entityId)
  const { data: documentTypes } = useDocumentTypes()
  const upload = useUploadPurchaseRequestAttachments(entity, entityId)
  const remove = useDeletePurchaseRequestAttachment(entity, entityId)
  const isNew = entityId <= 0

  const labels = Object.fromEntries(
    (documentTypes ?? []).map((option) => [option.value, option.label]),
  )

  async function handleFiles(selected: FileList | null) {
    const next = Array.from(selected ?? [])
    if (!next.length) return
    await upload.mutateAsync({ files: next, docType })
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <Card className="gap-4 py-4">
      {/*
        `pb-3!` chứ không phải `pb-3`: `CardHeader` của shadcn có luật
        `[.border-b]:pb-6` — selector kép nên thắng class thường, không đánh dấu
        important thì mọi thẻ có gạch chân đều bị đệm 24px, cao thấp lệch nhau.
      */}
      <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
        <div className="flex items-center gap-2">
          <Paperclip className="size-4 text-primary" />
          <CardTitle className="text-base text-navy dark:text-foreground">
            Chứng từ &amp; Tài liệu đính kèm
          </CardTitle>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {files?.length ?? 0} tệp
          </span>
        </div>

        {canManage && !isNew && (
          <div className="flex flex-wrap items-center gap-2">
            <Select value={docType} onValueChange={setDocType}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Loại chứng từ" />
              </SelectTrigger>
              <SelectContent>
                {(documentTypes ?? []).map((option) => (
                  <SelectItem key={option.value} value={option.value || 'other'}>
                    {option.label}
                  </SelectItem>
                ))}
                {!(documentTypes ?? []).some((option) => option.value === 'other') && (
                  <SelectItem value="other">Tài liệu khác</SelectItem>
                )}
              </SelectContent>
            </Select>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              multiple
              onChange={(event) => void handleFiles(event.target.files)}
            />
            <Button
              type="button"
              variant="outline"
              disabled={upload.isPending}
              onClick={() => inputRef.current?.click()}
            >
              {upload.isPending ? <Upload className="animate-pulse" /> : <Upload />}
              {upload.isPending ? 'Đang tải' : 'Tải tệp'}
            </Button>
          </div>
        )}
      </CardHeader>

      <CardContent className="px-4">
        {isNew ? (
          <p className="flex items-center justify-center gap-2 rounded-lg border border-dashed bg-muted/20 py-5 text-center text-sm text-muted-foreground">
            <Info className="size-4" />
            Vui lòng lưu chứng từ trước khi đính kèm tài liệu.
          </p>
        ) : (
          <>
            <p className="mb-3 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Info className="size-3.5" />
              Mỗi file tối đa 20 MB. Hỗ trợ PDF, ảnh, Word, Excel, XML, TXT, CSV, Email và CorelDRAW.
            </p>
            {isLoading && <Skeleton className="h-24 w-full" />}
            {isError && (
              <p className="text-sm text-destructive">Không tải được danh sách chứng từ.</p>
            )}
            {!isLoading && !isError && files?.length === 0 && (
              <p className="rounded-lg border border-dashed bg-muted/20 py-5 text-center text-sm text-muted-foreground">
                Chưa có tài liệu đính kèm.
              </p>
            )}

            {!!files?.length && (
              <div className="divide-y rounded-lg border">
                {files.map((file) => (
                  <AttachmentRow
                    key={file.id}
                    file={file}
                    typeLabel={labels[file.doc_type] || file.doc_type || 'Tài liệu khác'}
                    canDelete={canManage}
                    pending={remove.isPending}
                    onDelete={() => void remove.mutateAsync(file.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

function AttachmentRow({
  file,
  typeLabel,
  canDelete,
  pending,
  onDelete,
}: {
  file: AttachmentFile
  typeLabel: string
  canDelete: boolean
  pending: boolean
  onDelete: () => void
}) {
  // `attachmentIcon` chỉ TRA CỨU và trả về một trong các icon lucide khai báo sẵn ở
  // cấp module, không tạo component mới mỗi lần render -> không có chuyện remount.
  const Icon = attachmentIcon(file)
  return (
    <div className="flex min-h-12 items-center gap-3 px-3 py-2">
      {/* eslint-disable-next-line react-hooks/static-components */}
      <Icon className="size-5 shrink-0 text-primary" />
      <div className="min-w-0 flex-1">
        <a
          className="block truncate text-sm font-medium text-navy hover:text-primary hover:underline dark:text-foreground"
          href={file.url}
          target="_blank"
          rel="noreferrer"
          title={file.filename}
        >
          {file.filename}
        </a>
        <p className="text-xs text-muted-foreground">
          {typeLabel} · {formatFileSize(file.size)}
        </p>
      </div>
      <Button variant="ghost" size="icon-sm" asChild title="Mở hoặc tải tệp">
        <a href={file.url} target="_blank" rel="noreferrer" download={file.filename}>
          <Download />
        </a>
      </Button>
      {canDelete && (
        <ConfirmIconButton
          icon={Trash2}
          title="Xóa tệp"
          confirmTitle={`Xóa "${file.filename}"?`}
          confirmDescription="Tệp sẽ bị gỡ khỏi chứng từ này."
          confirmLabel="Xóa"
          destructive
          disabled={pending}
          onConfirm={onDelete}
        />
      )}
    </div>
  )
}

function attachmentIcon(file: AttachmentFile) {
  if (file.content_type?.startsWith('image/')) return FileImage
  if (file.content_type?.includes('pdf') || /\.(pdf|docx?|xlsx?)$/i.test(file.filename)) {
    return FileText
  }
  return File
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '0 KB'
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
