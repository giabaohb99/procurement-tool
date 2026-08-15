import type { Editor } from '@tiptap/react'
import { ImagePlus, Upload } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'

/**
 * Ảnh chèn từ máy được nhúng thẳng vào nội dung dạng base64, mà nội dung văn
 * bản đang giữ trong localStorage (~5MB cho cả phân hệ) — chặn từ 1MB để một
 * tấm ảnh không ăn hết chỗ của mọi văn bản khác.
 */
const MAX_FILE_SIZE = 1024 * 1024

interface ImageMenuProps {
  editor: Editor
}

/** Chèn ẢNH: dán địa chỉ ảnh trên mạng hoặc chọn tệp trong máy. */
export function ImageMenu({ editor }: ImageMenuProps) {
  const [open, setOpen] = useState(false)
  const [url, setUrl] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)

  function insert(src: string) {
    editor.chain().focus().setImage({ src }).run()
    setUrl('')
    setOpen(false)
  }

  function pickFile(file: File) {
    if (file.size > MAX_FILE_SIZE) {
      toast.error('Ảnh quá nặng (tối đa 1MB). Nén lại hoặc dán địa chỉ ảnh.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => insert(String(reader.result))
    reader.onerror = () => toast.error('Không đọc được tệp ảnh')
    reader.readAsDataURL(file)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title="Chèn ảnh"
          aria-label="Chèn ảnh"
          onMouseDown={(event) => event.preventDefault()}
        >
          <ImagePlus className="size-4" />
        </Button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-80 space-y-2">
        <Input
          autoFocus
          value={url}
          placeholder="Dán địa chỉ ảnh (https://…)"
          onChange={(event) => setUrl(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && url.trim()) {
              event.preventDefault()
              insert(url.trim())
            }
          }}
        />

        <div className="flex items-center justify-between gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => fileInput.current?.click()}
          >
            <Upload className="size-4" />
            Chọn tệp
          </Button>
          <Button type="button" size="sm" disabled={!url.trim()} onClick={() => insert(url.trim())}>
            Chèn
          </Button>
        </div>

        <input
          ref={fileInput}
          type="file"
          accept="image/*"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) pickFile(file)
            // Xóa giá trị để chọn lại đúng tệp vừa rồi vẫn kích hoạt `change`.
            event.target.value = ''
          }}
        />
      </PopoverContent>
    </Popover>
  )
}
