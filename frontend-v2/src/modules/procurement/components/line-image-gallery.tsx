import { Image, Trash2, Upload } from 'lucide-react'
import { useRef } from 'react'

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

interface LineImageGalleryProps {
  title: string
  /** Kho ảnh: `product` (ảnh gốc trong danh mục) · `purchase_request_line_image`… */
  entity: string
  /** 0 = chưa có bản ghi để gắn ảnh (dòng mới, hoặc mã hàng không khớp danh mục). */
  entityId: number
  /** Ảnh đại diện dùng khi kho ảnh rỗng — thường là thumbnail của sản phẩm. */
  fallbackUrl?: string
  canManage?: boolean
  /** Câu hiện khi không có ảnh nào. */
  emptyText?: string
}

/**
 * Khối ảnh CHỈ-ẢNH của một dòng chứng từ (khác `LineAttachments` — khối kia nhận cả
 * tài liệu và giữ hộ tệp của dòng chưa lưu).
 *
 * bao-CR-291: tách khỏi popup chi tiết dòng YCMH để dòng YCBG dùng lại — hai màn phải
 * hiện CÙNG một khối "Hình ảnh SP (gốc)", chép ra bản thứ hai là bắt đầu lệch nhau.
 */
export function LineImageGallery({
  title,
  entity,
  entityId,
  fallbackUrl,
  canManage,
  emptyText = 'Chưa có ảnh.',
}: LineImageGalleryProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { data, isLoading } = usePurchaseRequestAttachments(entity, entityId)
  const upload = useUploadPurchaseRequestAttachments(entity, entityId)
  const remove = useDeletePurchaseRequestAttachment(entity, entityId)
  const images = (data ?? []).filter(
    (file) => file.content_type.startsWith('image/') || IMAGE_PATTERN.test(file.filename),
  )
  const lightbox = useImageLightbox()

  return (
    <section className="rounded-lg border p-3">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-navy dark:text-foreground">
          <Image className="size-4 text-primary" />
          {title}
        </h4>
        {canManage && entityId > 0 && (
          <>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              accept="image/*"
              multiple
              onChange={(event) => {
                const files = Array.from(event.target.files ?? [])
                if (files.length) void upload.mutateAsync({ files })
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
              Thêm ảnh
            </Button>
          </>
        )}
      </div>
      {isLoading && entityId > 0 && <Skeleton className="h-20 w-full" />}
      {!isLoading && !images.length && fallbackUrl && (
        <a href={fallbackUrl} target="_blank" rel="noreferrer">
          <img className="size-20 rounded-md border object-cover" src={fallbackUrl} alt={title} />
        </a>
      )}
      {!isLoading && !images.length && !fallbackUrl && (
        <p className="text-xs text-muted-foreground">{emptyText}</p>
      )}
      {!!images.length && (
        <div className="flex flex-wrap gap-2">
          {images.map((file, index) => (
            <div key={file.id} className="group relative">
              <button
                type="button"
                title={file.filename}
                onClick={() => lightbox.openAt(index)}
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
                    title="Xóa ảnh"
                    confirmTitle={`Xóa ảnh ${file.filename}?`}
                    confirmDescription="Ảnh sẽ bị gỡ khỏi dòng này."
                    confirmLabel="Xóa"
                    destructive
                    disabled={remove.isPending}
                    onConfirm={() => void remove.mutateAsync(file.id)}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      {images.length > 0 && (
        <ImageLightbox
          images={images.map((f) => ({ url: f.url, name: f.filename }))}
          {...lightbox.bind}
        />
      )}
    </section>
  )
}
