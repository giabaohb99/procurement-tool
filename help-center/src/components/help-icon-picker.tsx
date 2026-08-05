import { useRef, useState } from 'react'
import Cropper, { type Area } from 'react-easy-crop'
import { Check, ImagePlus, Loader2, X } from 'lucide-react'
import { toast } from 'sonner'

import { uploadHelpImage } from '@/components/help-article-slides'
import { Button } from '@/components/ui/button'
import { cropImageToFile } from '@/lib/crop-image'
import { HELP_ICONS, isImageIcon } from '@/lib/help-icons'
import { cn } from '@/lib/utils'

// Ô chọn icon cho bài viết. Hai cách chọn:
//   1. Bấm 1 icon dựng sẵn (lưu slug) — bấm lại icon đang chọn để bỏ chọn.
//   2. Tải ảnh riêng lên: cắt vuông ngay tại chỗ rồi upload, lưu URL ảnh.
// Khung cắt hiện INLINE (không mở dialog lồng nhau) vì ô này nằm sẵn trong hộp thoại tạo bài.

/** Chỉ nhận ảnh và giới hạn dung lượng — ảnh gốc quá lớn làm trình duyệt cắt rất chậm. */
const MAX_UPLOAD_MB = 8

interface HelpIconPickerProps {
  value: string | null
  onChange: (icon: string | null) => void
  className?: string
}

export default function HelpIconPicker({ value, onChange, className }: HelpIconPickerProps) {
  const fileRef = useRef<HTMLInputElement>(null)

  // Ảnh đang chờ cắt (data URL). null = đang ở chế độ lưới icon.
  const [rawImage, setRawImage] = useState<string | null>(null)
  const [crop, setCrop] = useState({ x: 0, y: 0 })
  const [zoom, setZoom] = useState(1)
  const [area, setArea] = useState<Area | null>(null)
  const [uploading, setUploading] = useState(false)

  const customIcon = isImageIcon(value) ? value : null

  const pickFile = (file: File | undefined) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast.error('Vui lòng chọn tệp ảnh')
      return
    }
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      toast.error(`Ảnh quá lớn, tối đa ${MAX_UPLOAD_MB}MB`)
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      setRawImage(reader.result as string)
      setCrop({ x: 0, y: 0 })
      setZoom(1)
      setArea(null)
    }
    reader.readAsDataURL(file)
  }

  const cancelCrop = () => {
    setRawImage(null)
    setArea(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  const confirmCrop = async () => {
    if (!rawImage || !area) return
    setUploading(true)
    try {
      const file = await cropImageToFile(rawImage, area)
      const url = await uploadHelpImage(file)
      onChange(url)
      cancelCrop()
      toast.success('Đã đặt ảnh làm icon')
    } catch {
      toast.error('Không cắt/tải được ảnh, vui lòng thử lại')
    } finally {
      setUploading(false)
    }
  }

  // ----- Chế độ cắt ảnh -----
  if (rawImage) {
    return (
      <div className={cn('max-w-md', className)}>
        <div className="relative h-56 overflow-hidden rounded-md border bg-navy-deep">
          <Cropper
            image={rawImage}
            crop={crop}
            zoom={zoom}
            aspect={1}
            cropShape="rect"
            showGrid={false}
            onCropChange={setCrop}
            onZoomChange={setZoom}
            onCropComplete={(_area, pixels) => setArea(pixels)}
          />
        </div>

        <div className="mt-2 flex items-center gap-3">
          <span className="shrink-0 text-xs text-muted-foreground">Thu phóng</span>
          <input
            type="range"
            min={1} max={3} step={0.01}
            value={zoom}
            aria-label="Thu phóng ảnh"
            onChange={(e) => setZoom(Number(e.target.value))}
            className="h-1 flex-1 cursor-pointer accent-primary"
          />
        </div>

        <div className="mt-2 flex justify-end gap-2">
          {/* Nhãn "Bỏ ảnh" chứ không phải "Hủy" — tránh lẫn với nút Hủy của hộp thoại bao ngoài */}
          <Button type="button" variant="outline" size="sm" disabled={uploading} onClick={cancelCrop}>
            Bỏ ảnh
          </Button>
          <Button type="button" size="sm" disabled={!area || uploading} onClick={confirmCrop}>
            {uploading ? <Loader2 className="animate-spin" /> : <Check />}
            {uploading ? 'Đang tải lên…' : 'Cắt & dùng làm icon'}
          </Button>
        </div>
      </div>
    )
  }

  // ----- Chế độ lưới icon -----
  return (
    <div className={className}>
      {/* Ô cố định 36px + tự xuống dòng — không dùng grid aspect-square, nếu không ô sẽ
          phình to theo bề ngang cột ở trang soạn bài (/admin/:id) */}
      <div className="flex flex-wrap gap-1.5 rounded-md border bg-secondary/40 p-2">
        {HELP_ICONS.map(({ slug, label, Icon }) => {
          const active = value === slug
          return (
            <button
              key={slug}
              type="button"
              title={label}
              aria-label={label}
              aria-pressed={active}
              onClick={() => onChange(active ? null : slug)}
              className={cn(
                'grid size-9 shrink-0 place-items-center rounded-md border transition-colors',
                active
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-transparent bg-card text-muted-foreground hover:border-primary/40 hover:text-primary',
              )}
            >
              <Icon className="size-4" strokeWidth={1.75} />
            </button>
          )
        })}

        {/* Ảnh tự upload nằm cuối lưới, luôn ở trạng thái đang chọn */}
        {customIcon && (
          <span
            title="Ảnh riêng đang dùng làm icon"
            className="grid size-9 shrink-0 place-items-center overflow-hidden rounded-md border-2 border-primary bg-card p-0.5"
          >
            <img src={customIcon} alt="Icon tự tải lên" className="size-full object-contain" />
          </span>
        )}

        <button
          type="button"
          title="Tải ảnh riêng lên"
          aria-label="Tải ảnh riêng lên"
          onClick={() => fileRef.current?.click()}
          className="grid size-9 shrink-0 place-items-center rounded-md border border-dashed border-muted-foreground/40 bg-card text-muted-foreground transition-colors hover:border-primary hover:text-primary"
        >
          <ImagePlus className="size-4" strokeWidth={1.75} />
        </button>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => pickFile(e.target.files?.[0])}
      />

      <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
        {value ? (
          <>
            <span>
              Đã chọn:{' '}
              <strong className="font-medium text-navy">
                {customIcon ? 'ảnh riêng' : HELP_ICONS.find((o) => o.slug === value)?.label}
              </strong>
            </span>
            <button
              type="button"
              onClick={() => onChange(null)}
              className="inline-flex items-center gap-1 text-muted-foreground transition-colors hover:text-destructive"
            >
              <X className="size-3" /> Bỏ chọn
            </button>
          </>
        ) : (
          <span>Chưa chọn — hệ thống sẽ tự gán icon mặc định. Bấm ô nét đứt để tải ảnh riêng.</span>
        )}
      </div>
    </div>
  )
}
