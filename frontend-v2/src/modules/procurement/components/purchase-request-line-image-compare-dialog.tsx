import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'

/** Một ảnh để đối chiếu: đường dẫn xem được + tên tệp (hiện dưới ảnh). */
export interface CompareImage {
  url: string
  filename?: string
}

interface PurchaseRequestLineImageCompareDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Ảnh gốc của sản phẩm (danh mục). */
  left: CompareImage[]
  /** Ảnh đối chiếu chụp thực tế của dòng. */
  right: CompareImage[]
}

/**
 * Hộp *So sánh* của popup Chi tiết dòng YCMH — dời từ `CompareLightbox` bản v1
 * (duoc-CR-741): CHIA ĐÔI, trái là ảnh gốc của sản phẩm, phải là ảnh đối chiếu
 * thực tế; mỗi bên tự chuyển ảnh trước / sau, độc lập với bên kia. Đóng bằng dấu
 * X, phím Esc hoặc bấm ra ngoài như mọi hộp thoại của v2.
 */
export function PurchaseRequestLineImageCompareDialog({
  open,
  onOpenChange,
  left,
  right,
}: PurchaseRequestLineImageCompareDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-6xl">
        <DialogHeader className="pr-8 text-left">
          <DialogTitle>So sánh</DialogTitle>
          <DialogDescription className="sr-only">
            Đặt ảnh gốc của sản phẩm cạnh ảnh đối chiếu thực tế của dòng.
          </DialogDescription>
        </DialogHeader>
        {/*  Khổ hẹp xếp chồng hai bên: đặt cạnh nhau trong 360px thì mỗi ảnh còn bằng con tem. */}
        <div className="grid gap-4 md:grid-cols-2 md:divide-x">
          <CompareSide images={left} label="Ảnh gốc (catalog)" empty="Chưa có ảnh gốc" />
          <CompareSide
            images={right}
            label="Ảnh đối chiếu (thực tế)"
            empty="Chưa có ảnh đối chiếu"
            className="md:pl-4"
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}

function CompareSide({
  images,
  label,
  empty,
  className,
}: {
  images: CompareImage[]
  label: string
  empty: string
  className?: string
}) {
  const [position, setPosition] = useState(0)
  const count = images.length
  //  Vòng lại khi vượt hai đầu, như bản v1.
  const index = count ? ((position % count) + count) % count : 0
  const image = count ? images[index] : null

  return (
    <section aria-label={label} className={className}>
      <h4 className="mb-2 text-center text-sm font-semibold">{label}</h4>
      {image ? (
        <>
          <div className="relative flex h-[60vh] items-center justify-center rounded-md bg-muted/40">
            <img
              src={image.url}
              alt={image.filename || label}
              className="max-h-full max-w-full rounded-md object-contain"
            />
            {count > 1 && (
              <>
                <Button
                  type="button"
                  variant="secondary"
                  size="icon"
                  title="Ảnh trước"
                  aria-label={`Ảnh trước, ${label}`}
                  className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full"
                  onClick={() => setPosition((current) => current - 1)}
                >
                  <ChevronLeft />
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="icon"
                  title="Ảnh sau"
                  aria-label={`Ảnh sau, ${label}`}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full"
                  onClick={() => setPosition((current) => current + 1)}
                >
                  <ChevronRight />
                </Button>
              </>
            )}
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            {image.filename ? `${image.filename} — ` : ''}
            {index + 1}/{count}
          </p>
        </>
      ) : (
        <p className="py-10 text-center text-sm text-muted-foreground">{empty}</p>
      )}
    </section>
  )
}
