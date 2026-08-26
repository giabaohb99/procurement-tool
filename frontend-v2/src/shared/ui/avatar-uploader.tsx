import { Camera, Loader2 } from 'lucide-react'
import { useState, type ChangeEvent } from 'react'

import { cn } from '@/shared/utils/cn'

interface AvatarUploaderProps {
  /** URL ảnh hiện tại. Trống = hiện chữ viết tắt. */
  src?: string | null
  /** Chữ hiện khi chưa có ảnh (vd "TĐ", "D"). */
  fallback: string
  alt: string
  /** Không truyền = chỉ xem, không hiện lớp phủ máy ảnh. */
  onUpload?: (file: File) => Promise<unknown>
  /** Giải thích vì sao không sửa được (hiện ở tooltip). */
  disabledHint?: string
  /** Logo công ty nền trắng + `contain`; ảnh người thì `cover`. */
  fit?: 'cover' | 'contain'
}

/**
 * Ảnh đại diện tròn ở đầu trang chi tiết, bấm vào để đổi ảnh.
 * Dùng chung cho ảnh nhân sự và logo công ty — hai chỗ chỉ khác endpoint,
 * nên phần chọn file + trạng thái đang tải gom về đây.
 */
export function AvatarUploader({
  src,
  fallback,
  alt,
  onUpload,
  disabledHint,
  fit = 'cover',
}: AvatarUploaderProps) {
  const [busy, setBusy] = useState(false)

  async function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file || !onUpload) return
    setBusy(true)
    try {
      await onUpload(file)
    } finally {
      setBusy(false)
      // Reset để chọn lại đúng file vừa rồi vẫn kích hoạt onChange.
      event.target.value = ''
    }
  }

  const inner = src ? (
    <img
      src={src}
      alt={alt}
      className={cn('size-full', fit === 'contain' ? 'bg-white object-contain' : 'object-cover')}
    />
  ) : (
    <span className="text-xl font-semibold text-primary">{fallback}</span>
  )

  const shell =
    'relative grid size-16 shrink-0 place-items-center overflow-hidden rounded-full border bg-accent'

  if (!onUpload) {
    return (
      <div className={shell} title={disabledHint}>
        {inner}
      </div>
    )
  }

  return (
    <label className={cn(shell, 'group cursor-pointer')} title="Bấm để đổi ảnh">
      {inner}
      <span
        className={cn(
          'absolute inset-x-0 bottom-0 grid h-5 place-items-center bg-navy-solid/70 text-white transition-opacity',
          busy ? 'opacity-100' : 'opacity-0 group-hover:opacity-100',
        )}
      >
        {busy ? <Loader2 className="size-3 animate-spin" /> : <Camera className="size-3" />}
      </span>
      <input type="file" hidden accept="image/*" disabled={busy} onChange={handleChange} />
    </label>
  )
}
