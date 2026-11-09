import { FileText, Paperclip, Trash2, Upload, X } from 'lucide-react'
import { useEffect, useMemo, useRef } from 'react'

import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  useDeletePurchaseRequestAttachment,
  usePurchaseRequestAttachments,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'

const IMAGE_PATTERN = /\.(jpe?g|png|webp|gif)$/i

/**
 * Chữ trên khung đính kèm — duoc-CR-741: mỗi màn dùng ĐÚNG chữ của bản v1, mà hai
 * màn v1 nói khác nhau (Phiếu khảo sát có nút *Tải file lên*, YCBG có vùng *Kéo thả
 * hoặc bấm chọn file*). Màn gọi truyền bộ chữ của mình; bỏ trống thì giữ chữ cũ của v2.
 */
export interface LineAttachmentsLabels {
  /** `button` = nút ở góc tiêu đề; `dropzone` = vùng kéo thả dưới danh sách tệp. */
  uploadMode: 'button' | 'dropzone'
  /** Chữ nút tải lên, hoặc dòng chính giữa vùng kéo thả. */
  uploadLabel: string
  /** Chữ nút trong lúc đang tải (chỉ kiểu `button`). */
  uploadingLabel: string
  /** Dòng nhỏ dưới vùng kéo thả khi dòng ĐÃ lưu (định dạng nhận). */
  uploadHint?: string
  /** Dòng nhỏ dưới vùng kéo thả khi dòng CHƯA lưu. */
  pendingUploadHint?: string
  /** Gợi ý nút xóa tệp đã tải. */
  deleteTooltip: string
  /** Câu hỏi khi xóa tệp — bỏ trống thì hỏi kèm tên tệp. */
  deleteConfirmTitle?: string
  /** Câu giải thích dưới câu hỏi — `''` = không có. */
  deleteConfirmDescription: string
  deleteConfirmLabel: string
  /** Gợi ý nút bỏ một tệp đang chờ lưu. */
  removePendingTooltip: string
}

const DEFAULT_LABELS: LineAttachmentsLabels = {
  uploadMode: 'button',
  uploadLabel: 'Thêm tệp',
  uploadingLabel: 'Thêm tệp',
  deleteTooltip: 'Xóa tệp',
  deleteConfirmDescription: 'Tệp sẽ bị gỡ khỏi dòng này.',
  deleteConfirmLabel: 'Xóa',
  removePendingTooltip: 'Bỏ tệp này',
}

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
  /** Bộ chữ riêng của màn gọi (duoc-CR-741) — xem `LineAttachmentsLabels`. */
  labels?: Partial<LineAttachmentsLabels>
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
  labels,
}: LineAttachmentsProps) {
  const text = { ...DEFAULT_LABELS, ...labels }
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

  /** Dòng đã lưu thì tải lên ngay; dòng chưa lưu thì trang giữ hộ tới lúc bấm Lưu. */
  function addFiles(picked: File[]) {
    if (!picked.length) return
    if (lineId > 0) void upload.mutateAsync({ files: picked })
    else onPendingFilesChange([...pendingFiles, ...picked])
  }

  const deleteButton = (file: { id: number; filename: string }) => (
    <ConfirmIconButton
      icon={Trash2}
      title={text.deleteTooltip}
      confirmTitle={text.deleteConfirmTitle ?? `Xóa tệp ${file.filename}?`}
      confirmDescription={text.deleteConfirmDescription || undefined}
      confirmLabel={text.deleteConfirmLabel}
      destructive
      disabled={remove.isPending}
      onConfirm={() => void remove.mutateAsync(file.id)}
    />
  )

  return (
    <section className="rounded-lg border p-3">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-navy dark:text-foreground">
          <Paperclip className="size-4 text-primary" />
          {title}
        </h4>
        {canManage && text.uploadMode === 'button' && (
          <>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              multiple
              onChange={(event) => {
                addFiles(Array.from(event.target.files ?? []))
                event.target.value = ''
              }}
            />
            {/*  `type="button"`: popup dòng có thể nằm trong `<form>` của trang. */}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={upload.isPending}
              onClick={() => inputRef.current?.click()}
            >
              <Upload />
              {upload.isPending ? text.uploadingLabel : text.uploadLabel}
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
                  {deleteButton(file)}
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
              {canManage && deleteButton(file)}
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
                type="button"
                variant="ghost"
                size="icon-sm"
                className="absolute right-0.5 top-0.5 bg-background/90 text-destructive hover:text-destructive"
                title={text.removePendingTooltip}
                aria-label={text.removePendingTooltip}
                onClick={() => onPendingFilesChange(pendingFiles.filter((_, i) => i !== index))}
              >
                <X />
              </Button>
            )}
          </div>
        ))}
      </div>

      {/*  Kiểu YCBG v1: vùng kéo thả nằm DƯỚI danh sách tệp. */}
      {canManage && text.uploadMode === 'dropzone' && (
        <FileDropzone
          className="mt-3"
          hint={text.uploadLabel}
          description={lineId > 0 ? text.uploadHint : text.pendingUploadHint}
          busy={upload.isPending}
          onFiles={addFiles}
        />
      )}

      {imageFiles.length > 0 && (
        <ImageLightbox
          images={imageFiles.map((f) => ({ url: f.url, name: f.filename }))}
          {...lightbox.bind}
        />
      )}
    </section>
  )
}
