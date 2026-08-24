import { FileText, Paperclip, Trash2, Upload, X } from 'lucide-react'
import { useEffect, useMemo, useRef } from 'react'

import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  useDeletePurchaseRequestAttachment,
  usePurchaseRequestAttachments,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'

const IMAGE_PATTERN = /\.(jpe?g|png|webp|gif)$/i

interface LineAttachmentsProps {
  /** Entity của tệp: `survey_request_line`, `survey_line`… — mỗi loại dòng một kho riêng. */
  entity: string
  /** 0 = dòng chưa lưu, chưa có chỗ để gắn tệp. */
  lineId: number
  canManage: boolean
  /** Tệp chọn trước khi dòng được lưu — trang giữ hộ, lưu xong mới tải lên. */
  pendingFiles: File[]
  onPendingFilesChange: (files: File[]) => void
  title?: string
}

/**
 * Đính kèm của MỘT dòng chứng từ.
 *
 * Dòng CHƯA lưu thì chưa có id để gắn tệp vào, nên ảnh được giữ tạm trong bộ nhớ
 * và chỉ tải lên sau khi bấm Lưu phiếu (trang lo việc đó). Không làm vậy thì
 * người lập phải lưu phiếu trước rồi mới quay lại đính ảnh từng dòng.
 *
 * Dùng chung cho dòng YCBG lẫn dòng phiếu khảo sát — khác nhau đúng một chỗ là
 * `entity`, nên đừng chép ra bản thứ hai.
 */
export function LineAttachments({
  entity,
  lineId,
  canManage,
  pendingFiles,
  onPendingFilesChange,
  title = 'Hình ảnh / tài liệu đính kèm',
}: LineAttachmentsProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { data, isLoading } = usePurchaseRequestAttachments(entity, lineId)
  const upload = useUploadPurchaseRequestAttachments(entity, lineId)
  const remove = useDeletePurchaseRequestAttachment(entity, lineId)

  // Ảnh tạm phải có URL để xem trước; tạo xong nhớ thu hồi, không thì mỗi lần
  // mở popup lại giữ thêm một bản blob trong bộ nhớ trình duyệt.
  const previews = useMemo(
    () => pendingFiles.map((file) => ({ file, url: URL.createObjectURL(file) })),
    [pendingFiles],
  )
  useEffect(
    () => () => previews.forEach((preview) => URL.revokeObjectURL(preview.url)),
    [previews],
  )

  const files = data ?? []
  const isImageFile = (f: { content_type: string; filename: string }) =>
    f.content_type.startsWith('image/') || IMAGE_PATTERN.test(f.filename)
  const imageFiles = files.filter(isImageFile)
  const lightbox = useImageLightbox()

  return (
    <section className="rounded-lg border p-3">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-navy dark:text-foreground">
          <Paperclip className="size-4 text-primary" />
          {title}
        </h4>
        {canManage && (
          <>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              multiple
              onChange={(event) => {
                const picked = Array.from(event.target.files ?? [])
                if (picked.length) {
                  if (lineId > 0) void upload.mutateAsync({ files: picked })
                  else onPendingFilesChange([...pendingFiles, ...picked])
                }
                event.target.value = ''
              }}
            />
            <Button
              variant="ghost"
              size="sm"
              disabled={upload.isPending}
              onClick={() => inputRef.current?.click()}
            >
              <Upload />
              Thêm tệp
            </Button>
          </>
        )}
      </div>

      {lineId > 0 && isLoading && <Skeleton className="h-20 w-full" />}

      {lineId <= 0 && (
        <p className="mb-2 text-xs text-muted-foreground">
          Chọn hình bây giờ — sẽ được lưu cùng khi bạn bấm Lưu.
        </p>
      )}

      {lineId > 0 && !isLoading && !files.length && (
        <p className="text-xs text-muted-foreground">Chưa có tệp nào.</p>
      )}

      <div className="flex flex-wrap gap-2">
        {files.map((file) =>
          isImageFile(file) ? (
            <div key={file.id} className="group relative">
              <button
                type="button"
                title={file.filename}
                onClick={() => lightbox.openAt(imageFiles.indexOf(file))}
                className="block leading-none"
              >
                <img
                  className="size-20 rounded-md border object-cover"
                  src={file.url}
                  alt={file.filename}
                />
              </button>
              {canManage && (
                <div className="absolute right-1 top-1 rounded-md bg-background/90 opacity-0 shadow-sm transition-opacity focus-within:opacity-100 group-hover:opacity-100">
                  <ConfirmIconButton
                    icon={Trash2}
                    title="Xóa tệp"
                    confirmTitle={`Xóa tệp ${file.filename}?`}
                    confirmDescription="Tệp sẽ bị gỡ khỏi dòng này."
                    confirmLabel="Xóa"
                    destructive
                    disabled={remove.isPending}
                    onConfirm={() => void remove.mutateAsync(file.id)}
                  />
                </div>
              )}
            </div>
          ) : (
            <div key={file.id} className="flex items-center gap-1 rounded-md border px-2 py-1">
              <a
                className="flex items-center gap-1.5 text-sm hover:underline"
                href={file.url}
                target="_blank"
                rel="noreferrer"
              >
                <FileText className="size-4 text-muted-foreground" />
                {file.filename}
              </a>
              {canManage && (
                <ConfirmIconButton
                  icon={Trash2}
                  title="Xóa tệp"
                  confirmTitle={`Xóa tệp ${file.filename}?`}
                  confirmDescription="Tệp sẽ bị gỡ khỏi dòng này."
                  confirmLabel="Xóa"
                  destructive
                  disabled={remove.isPending}
                  onConfirm={() => void remove.mutateAsync(file.id)}
                />
              )}
            </div>
          ),
        )}

        {previews.map((preview, index) => (
          <div key={`${preview.file.name}-${index}`} className="group relative">
            {preview.file.type.startsWith('image/') ? (
              <img
                className="size-20 rounded-md border object-cover"
                src={preview.url}
                alt={preview.file.name}
              />
            ) : (
              <div className="flex size-20 flex-col items-center justify-center gap-1 rounded-md border p-1 text-center">
                <FileText className="size-5 text-muted-foreground" />
                <span className="line-clamp-2 text-[10.5px] text-muted-foreground">
                  {preview.file.name}
                </span>
              </div>
            )}
            {canManage && (
              <Button
                variant="ghost"
                size="icon-sm"
                className="absolute right-0.5 top-0.5 bg-background/90 text-destructive hover:text-destructive"
                title="Bỏ tệp này"
                onClick={() => onPendingFilesChange(pendingFiles.filter((_, i) => i !== index))}
              >
                <X />
              </Button>
            )}
          </div>
        ))}
      </div>

      {imageFiles.length > 0 && (
        <ImageLightbox
          images={imageFiles.map((f) => ({ url: f.url, name: f.filename }))}
          {...lightbox.bind}
        />
      )}
    </section>
  )
}
