import { IdCard, Loader2, Upload } from 'lucide-react'
import { useState, type ChangeEvent } from 'react'

import { Button } from '@/shared/ui/button'
import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
import { cn } from '@/shared/utils/cn'

/**
 * Hai ô ảnh CCCD (mặt trước / mặt sau) — C4 của duoc-CR-314.
 *
 * ⚠️ Ảnh đi qua cửa upload RIÊNG (`POST /employees/{id}/id-image/{side}`) chứ
 * không phải một ô trong form hồ sơ: nhận đường dẫn từ client là cho phép trỏ ô
 * ảnh giấy tờ tùy thân vào một URL bên ngoài, rồi màn hồ sơ và bản in sẽ tải nó
 * về hộ. Vì thế nút này lưu NGAY, không chờ nút Lưu của cả trang — nói rõ điều
 * đó ở chân khối để người dùng không tưởng mình còn phải bấm Lưu.
 *
 * ⚠️ Backend đòi `employee_sensitive.read` cho cả GHI, không chỉ ĐỌC: ghi đè
 * được ảnh CCCD của người khác là thay giấy tờ tùy thân của họ trong hồ sơ mà
 * người đọc hồ sơ không có cách nào biết.
 */

interface EmployeeIdCardUploaderProps {
  frontUrl?: string
  backUrl?: string
  canWrite: boolean
  isUploading: boolean
  onUpload: (side: 'front' | 'back', file: File) => void
  className?: string
}

export function EmployeeIdCardUploader({
  frontUrl,
  backUrl,
  canWrite,
  isUploading,
  onUpload,
  className,
}: EmployeeIdCardUploaderProps) {
  const sides = [
    { key: 'front' as const, label: 'Mặt trước', url: frontUrl },
    { key: 'back' as const, label: 'Mặt sau', url: backUrl },
  ]

  //  Chỉ đưa ảnh ĐÃ CÓ vào bộ xem — nhét ô rỗng vào thì bấm ảnh mặt trước lại
  //  mở đúng vị trí của một ảnh không tồn tại.
  const shown = sides.filter((s) => s.url)
  const lightbox = useImageLightbox()

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <div className="grid gap-4 sm:grid-cols-2">
        {sides.map((side) => (
          <IdCardSlot
            key={side.key}
            label={side.label}
            url={side.url}
            canWrite={canWrite}
            isUploading={isUploading}
            onPick={(file) => onUpload(side.key, file)}
            onView={() => {
              const at = shown.findIndex((s) => s.key === side.key)
              if (at >= 0) lightbox.openAt(at)
            }}
          />
        ))}
      </div>

      {canWrite && (
        <p className="text-xs text-muted-foreground">
          Ảnh lưu ngay khi chọn — không cần bấm Lưu ở đầu trang.
        </p>
      )}

      <ImageLightbox
        images={shown.map((s) => ({ url: s.url ?? '', name: `CCCD ${s.label}` }))}
        {...lightbox.bind}
      />
    </div>
  )
}

interface IdCardSlotProps {
  label: string
  url?: string
  canWrite: boolean
  isUploading: boolean
  onPick: (file: File) => void
  onView: () => void
}

function IdCardSlot({ label, url, canWrite, isUploading, onPick, onView }: IdCardSlotProps) {
  const [inputKey, setInputKey] = useState(0)

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) onPick(file)
    //  Đổi key để dựng lại `<input>`: chọn LẠI đúng tệp vừa chọn thì trình duyệt
    //  không bắn `change` (giá trị không đổi), và người dùng tưởng nút hỏng.
    setInputKey((k) => k + 1)
  }

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-medium">{label}</span>

      {url ? (
        <button
          type="button"
          onClick={onView}
          className="overflow-hidden rounded-md border transition hover:opacity-90"
          aria-label={`Xem ảnh CCCD ${label.toLowerCase()}`}
        >
          <img src={url} alt={`CCCD ${label}`} className="h-40 w-full object-cover" />
        </button>
      ) : (
        <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-md border border-dashed text-muted-foreground">
          <IdCard className="size-8" />
          <span className="text-xs">Chưa có ảnh</span>
        </div>
      )}

      {canWrite && (
        <Button type="button" variant="outline" size="sm" asChild disabled={isUploading}>
          <label className="cursor-pointer">
            {isUploading ? <Loader2 className="animate-spin" /> : <Upload />}
            {url ? 'Đổi ảnh' : 'Tải ảnh lên'}
            <input
              key={inputKey}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleChange}
            />
          </label>
        </Button>
      )}
    </div>
  )
}
