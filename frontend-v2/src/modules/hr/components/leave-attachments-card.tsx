import { Download, Eye, FileImage, FileText, File as FileIcon, Paperclip, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { AttachmentPreviewDialog } from '@/shared/attachments/attachment-preview-dialog'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { leaveAttachmentDownloadUrl, type LeaveAttachment } from '../api/leave-attachment-api'
import {
  useDeleteLeaveAttachment,
  useLeaveAttachments,
  useUploadLeaveAttachments,
} from '../hooks/use-leave-attachments'
import { isPrintableImage } from '../utils/leave-print-attachments'

/** Trần dung lượng MỘT tệp — khai ở `FILE_POLICY["leave_request"]` của backend. */
const MAX_SIZE_MB = 50

/** Khớp tập đuôi `_DOC` của `FILE_POLICY` — hộp chọn tệp chỉ bày những kiểu sẽ được nhận. */
const ACCEPT = '.jpg,.jpeg,.png,.webp,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv'

function fileIcon(file: LeaveAttachment) {
  const type = (file.content_type || '').toLowerCase()
  if (type.startsWith('image/')) return FileImage
  if (type.includes('pdf')) return FileText
  return FileIcon
}

interface LeaveAttachmentsCardProps {
  /** `0` = đơn chưa lưu: chưa có gì để treo tệp vào. */
  requestId: number
  /**
   * Được thêm/gỡ tệp hay không — đơn còn sửa được (Nháp · Trả về) VÀ người xem
   * có quyền sửa đơn. Backend khóa y hệt (`_block_leave_request_locked`), đây
   * chỉ là để không bày ra một vùng thả bấm vào là ăn lỗi.
   */
  editable: boolean
}

/**
 * TỆP ĐÍNH KÈM của đơn nghỉ phép (bao-CR-505) — ảnh giấy khám bệnh, giấy ra
 * viện, thiệp cưới… Ảnh được in kèm ở mặt sau của bản in, mỗi ảnh một trang.
 *
 * Khuôn giống thẻ bản scan của Hồ sơ (`DossierAttachmentsCard`): danh sách
 * phẳng, không chia thư mục theo loại chứng từ — một tờ đơn nghỉ chỉ có vài tệp.
 *
 * ⚠️ `leave_request` là entity RIÊNG TƯ nên backend không trả `url`. Xem trước
 * đi `AttachmentPreviewDialog` (lấy blob qua `/view` có token), tải về đi
 * `downloadFile` — gắn thẳng `<img src>` / `<a href>` vào API là 401.
 */
export function LeaveAttachmentsCard({ requestId, editable }: LeaveAttachmentsCardProps) {
  const { data: files, isLoading } = useLeaveAttachments(requestId)
  const uploadMutation = useUploadLeaveAttachments(requestId)
  const deleteMutation = useDeleteLeaveAttachment(requestId)
  const [previewing, setPreviewing] = useState<LeaveAttachment | null>(null)
  const isNew = requestId === 0

  const handleFiles = (picked: File[]) => {
    //  Chặn tại chỗ cho khỏi chờ tải hết một tệp quá cỡ rồi mới ăn 413.
    const limit = MAX_SIZE_MB * 1024 * 1024
    const tooBig = picked.filter((f) => f.size > limit)
    if (tooBig.length > 0) {
      toast.error(`Vượt quá ${MAX_SIZE_MB}MB: ${tooBig.map((f) => f.name).join(', ')}`)
    }
    const ok = picked.filter((f) => f.size <= limit)
    if (ok.length > 0) uploadMutation.mutate(ok)
  }

  const handleDownload = async (file: LeaveAttachment) => {
    try {
      await downloadFile(leaveAttachmentDownloadUrl(file.id), file.filename)
    } catch {
      toast.error(`Không tải được tệp «${file.filename}».`)
    }
  }

  return (
    <Card className="gap-4 p-3 sm:p-5">
      <div className="min-w-0">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <Paperclip className="size-4 text-muted-foreground" />
          Tệp đính kèm
        </h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Giấy khám bệnh, giấy ra viện… Ảnh được in kèm ở mặt sau đơn, mỗi ảnh một trang A4.
        </p>
      </div>

      {isNew ? (
        //  Đơn chưa có id thì cửa đính kèm không có gì để treo tệp vào — nói rõ
        //  phải làm gì thay vì giấu hẳn khối này đi.
        <p className="rounded-lg border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
          Lưu nháp để đính kèm tệp.
        </p>
      ) : (
        <>
          {editable && (
            <FileDropzone
              onFiles={handleFiles}
              busy={uploadMutation.isPending}
              accept={ACCEPT}
              hint="Kéo tệp vào đây hoặc bấm để chọn"
              description={`Ảnh (JPG, PNG, WEBP), PDF, Word, Excel · tối đa ${MAX_SIZE_MB}MB mỗi tệp`}
            />
          )}

          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : !files || files.length === 0 ? (
            <p className="rounded-lg border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
              {editable
                ? 'Chưa có tệp nào. Kéo tệp vào vùng trên để tải lên.'
                : 'Đơn này không kèm tệp nào.'}
            </p>
          ) : (
            <ul className="space-y-2">
              {files.map((file) => {
                const Icon = fileIcon(file)
                return (
                  <li
                    key={file.id}
                    className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2"
                  >
                    <Icon className="size-5 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium" title={file.filename}>
                        {file.filename}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                        {isPrintableImage(file) && ' · in kèm ở mặt sau'}
                      </p>
                    </div>

                    <div className="flex shrink-0 items-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="size-8"
                        title="Xem trước"
                        aria-label={`Xem trước ${file.filename}`}
                        onClick={() => setPreviewing(file)}
                      >
                        <Eye className="size-4" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="size-8"
                        title="Tải về"
                        aria-label={`Tải về ${file.filename}`}
                        onClick={() => void handleDownload(file)}
                      >
                        <Download className="size-4" />
                      </Button>
                      {editable && (
                        <ConfirmIconButton
                          icon={Trash2}
                          title="Gỡ tệp"
                          confirmTitle="Gỡ tệp đính kèm?"
                          confirmDescription={`Gỡ «${file.filename}» khỏi đơn nghỉ phép này?`}
                          destructive
                          disabled={deleteMutation.isPending}
                          onConfirm={() => deleteMutation.mutate(file.id)}
                        />
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </>
      )}

      <AttachmentPreviewDialog
        file={previewing}
        open={Boolean(previewing)}
        onOpenChange={(open) => !open && setPreviewing(null)}
      />
    </Card>
  )
}
