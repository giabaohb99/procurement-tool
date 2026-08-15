import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, FileText, Loader2, Paperclip, X } from 'lucide-react'
import { useRef } from 'react'
import { toast } from 'sonner'

import { purchaseRequestSupportApi } from '@/modules/procurement/api/purchase-request-support-api'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { FormCard } from '@/shared/ui/form-card'

/**
 * Đính kèm treo vào **PHIÊN BẢN**, không vào văn bản (`entity = 'document_version'`).
 *
 * Cố ý: bản đã duyệt phải tra ra đúng bộ tệp lúc duyệt, kể cả sau khi bản mới đã
 * gỡ bớt. Mở phiên bản mới thì backend chép liên kết tệp sang bản mới nên người
 * dùng không thấy khác biệt gì — chỉ khi lật lại bản cũ mới thấy nó giữ nguyên
 * bộ tệp của nó.
 *
 * ⚠️ Đang đi đường tải tệp CHUNG (`/api/attachments`), link công khai theo
 * `file.url`. Kho tệp riêng tư + link tạm 60–120 giây là P0-T02…T04, chưa làm —
 * cho tới khi xong thì **không đưa văn bản mật thật vào hệ thống**.
 */
const ENTITY = 'document_version'

interface DocumentAttachmentListProps {
  /** Phiên bản đang mở. Chưa có thì khối này chỉ hiện lời nhắc. */
  versionId: number | null
  /** Bản đã duyệt là bất biến — chỉ xem, không thêm không gỡ. */
  readOnly?: boolean
}

export function DocumentAttachmentList({
  versionId,
  readOnly = false,
}: DocumentAttachmentListProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

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
                <p className="text-xs text-muted-foreground">{formatSize(file.size)}</p>
              </div>

              <Button asChild variant="ghost" size="icon-sm" title="Tải về">
                <a href={file.url} target="_blank" rel="noreferrer">
                  <Download className="size-4" />
                </a>
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
    </FormCard>
  )
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
