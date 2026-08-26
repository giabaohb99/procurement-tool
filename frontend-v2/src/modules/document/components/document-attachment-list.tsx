import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Eye, FileText, Loader2, Paperclip, X } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { downloadFile, extractErrorMessage } from '@/core/api'
import {
  purchaseRequestSupportApi,
  type AttachmentFile,
} from '@/modules/procurement/api/purchase-request-support-api'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { FormCard } from '@/shared/ui/form-card'
import { canPreviewInline } from '../helpers/inline-viewable'
import { AttachmentViewerDialog } from './attachment-viewer-dialog'

/**
 * Đính kèm treo vào **PHIÊN BẢN**, không vào văn bản (`entity = 'document_version'`).
 *
 * Cố ý: bản đã duyệt phải tra ra đúng bộ tệp lúc duyệt, kể cả sau khi bản mới đã
 * gỡ bớt. Mở phiên bản mới thì backend chép liên kết tệp sang bản mới nên người
 * dùng không thấy khác biệt gì — chỉ khi lật lại bản cũ mới thấy nó giữ nguyên
 * bộ tệp của nó.
 *
 * **Tải tệp đi đường riêng tư (C03).** `document_version` nằm trong
 * `PRIVATE_ENTITIES` nên backend trả `url` rỗng; tải bằng `downloadFile` qua
 * `GET /api/attachments/{id}/download` — đường đó kiểm quyền đọc văn bản trước
 * khi trả byte nào.
 *
 * ⚠️ **Vẫn chưa kín hoàn toàn.** Object trên kho lưu trữ còn đọc được nếu ai đó
 * đã có URL từ trước (tệp tải lên trước 17/08/2026) hoặc đoán đúng key — bịt hẳn
 * phải chuyển kho sang riêng tư, là việc hạ tầng P0-N02/N03 đụng cả `frontend/`
 * đang đóng băng. Tới lúc đó thì **chưa đưa văn bản Tuyệt mật thật vào hệ thống**.
 */
const ENTITY = 'document_version'

interface DocumentAttachmentListProps {
  /** Phiên bản đang mở. Chưa có thì khối này chỉ hiện lời nhắc. */
  versionId: number | null
  /** Bản đã duyệt là bất biến — chỉ xem, không thêm không gỡ. */
  readOnly?: boolean
  /** Số hiệu văn bản — in vào watermark của khung xem. */
  documentCode?: string
}

export function DocumentAttachmentList({
  versionId,
  readOnly = false,
  documentCode,
}: DocumentAttachmentListProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()
  //  Tệp đang mở trong khung xem tại chỗ. `null` = khung đang đóng.
  const [dangXem, setDangXem] = useState<AttachmentFile | null>(null)

  const queryKey = ['document', 'attachments', versionId ?? 0] as const

  const { data: files = [] } = useQuery({
    queryKey,
    queryFn: () => purchaseRequestSupportApi.listAttachments(ENTITY, versionId as number),
    enabled: Boolean(versionId),
  })

  const upload = useMutation({
    mutationFn: (picked: File[]) =>
      purchaseRequestSupportApi.uploadAttachments(ENTITY, versionId as number, picked),
    onSuccess: (added) => {
      toast.success(`Đã đính kèm ${added.length} tệp`)
      void queryClient.invalidateQueries({ queryKey })
    },
  })

  const remove = useMutation({
    mutationFn: (linkId: number) => purchaseRequestSupportApi.deleteAttachment(linkId),
    onSuccess: () => {
      toast.success('Đã gỡ tệp')
      void queryClient.invalidateQueries({ queryKey })
    },
  })

  //  Tải qua đường có kiểm quyền. Giữ id đang tải để hiện vòng xoay đúng dòng —
  //  tệp 30MB mà nút không đổi gì thì người dùng bấm lại mấy lần.
  const download = useMutation({
    mutationFn: (file: AttachmentFile) =>
      downloadFile(`/api/attachments/${file.id}/download`, file.filename),
    onError: (error) => toast.error(extractErrorMessage(error)),
  })

  function handleFiles(list: FileList | null) {
    if (!list?.length || !versionId) return
    upload.mutate(Array.from(list))
    // Xóa giá trị input để chọn LẠI ĐÚNG tệp vừa gỡ vẫn kích hoạt `onChange`.
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <FormCard
      title="Tệp đính kèm"
      actions={
        !readOnly && versionId ? (
          <>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={upload.isPending}
              onClick={() => inputRef.current?.click()}
            >
              {upload.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Paperclip className="size-4" />
              )}
              Chọn tệp
            </Button>
            <input
              ref={inputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(event) => handleFiles(event.target.files)}
            />
          </>
        ) : null
      }
    >
      {!versionId ? (
        <p className="text-sm text-muted-foreground">
          Lưu văn bản trước, rồi mới đính kèm được tệp.
        </p>
      ) : files.length === 0 ? (
        <p className="text-sm text-muted-foreground">Chưa có tệp nào.</p>
      ) : (
        <ul className="divide-y">
          {files.map((file) => (
            <li key={file.id} className="flex items-center gap-3 py-2 first:pt-0">
              <FileText className="size-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{file.filename}</p>
                <p className="text-xs text-muted-foreground">
                  {formatSize(file.size)}
                  {/*  Mã băm để người cầm tệp ngoài hệ thống đối chiếu được nó
                       có đúng tệp đã đính kèm không (C06). Hiện 12 ký tự đầu cho
                       vừa dòng; rê chuột ra chuỗi đầy đủ để so từng ký tự. */}
                  {file.sha256 && (
                    <>
                      {' · '}
                      <span className="font-mono" title={`SHA-256: ${file.sha256}`}>
                        {file.sha256.slice(0, 12)}
                      </span>
                    </>
                  )}
                </p>
              </div>

              {/*  XEM TẠI CHỖ đứng TRƯỚC nút tải: phần lớn lượt mở tệp là để
                   liếc một cái, không phải để giữ một bản trên máy. Chỉ hiện với
                   kiểu tệp backend cho mở tại chỗ (ảnh + PDF) — kiểu khác bấm
                   vào chỉ nhận 415. */}
              {canPreviewInline(file.content_type, file.filename) && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  title="Xem tại chỗ"
                  onClick={() => setDangXem(file)}
                >
                  <Eye className="size-4" />
                </Button>
              )}

              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                title="Tải về"
                disabled={download.isPending}
                onClick={() => download.mutate(file)}
              >
                {download.isPending && download.variables?.id === file.id ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Download className="size-4" />
                )}
              </Button>

              {!readOnly && (
                <ConfirmIconButton
                  icon={X}
                  title="Gỡ tệp"
                  destructive
                  confirmTitle={`Gỡ "${file.filename}"?`}
                  confirmDescription="Tệp bị gỡ khỏi phiên bản này; các phiên bản khác vẫn giữ tệp của chúng."
                  confirmLabel="Gỡ"
                  onConfirm={() => remove.mutate(file.id)}
                />
              )}
            </li>
          ))}
        </ul>
      )}

      <AttachmentViewerDialog
        linkId={dangXem?.id ?? null}
        filename={dangXem?.filename ?? ''}
        contentType={dangXem?.content_type}
        documentCode={documentCode}
        onClose={() => setDangXem(null)}
      />
    </FormCard>
  )
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
