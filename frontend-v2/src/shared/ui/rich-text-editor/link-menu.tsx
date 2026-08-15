import type { Editor } from '@tiptap/react'
import { Link2, Link2Off } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

interface LinkMenuProps {
  editor: Editor
  /** Con trỏ đang nằm trong một liên kết. */
  active: boolean
}

/**
 * Chèn / sửa / gỡ LIÊN KẾT.
 *
 * Mở popover có ô nhập thay vì `window.prompt`: hộp thoại của trình duyệt cướp
 * mất vùng chọn trong trình soạn thảo trên vài trình duyệt, mà cũng không dán
 * được địa chỉ dài cho tử tế.
 */
export function LinkMenu({ editor, active }: LinkMenuProps) {
  const [open, setOpen] = useState(false)
  const [url, setUrl] = useState('')

  function openMenu(next: boolean) {
    // Mở ra thì đổ sẵn địa chỉ cũ để người dùng sửa chứ không phải gõ lại.
    if (next) setUrl(editor.getAttributes('link').href ?? '')
    setOpen(next)
  }

  function apply() {
    const href = url.trim()
    if (!href) {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
    } else {
      // Thiếu giao thức thì trình duyệt hiểu là đường dẫn nội bộ của trang.
      const full = /^(https?:|mailto:|tel:)/i.test(href) ? href : `https://${href}`
      editor.chain().focus().extendMarkRange('link').setLink({ href: full }).run()
    }
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={openMenu}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title="Liên kết"
          aria-label="Liên kết"
          aria-pressed={active}
          onMouseDown={(event) => event.preventDefault()}
          className={cn(active && 'bg-accent text-accent-foreground')}
        >
          <Link2 className="size-4" />
        </Button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-80 space-y-2">
        <Input
          autoFocus
          value={url}
          placeholder="https://…"
          onChange={(event) => setUrl(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault()
              apply()
            }
          }}
        />

        <div className="flex items-center justify-between gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={!active}
            onClick={() => {
              editor.chain().focus().extendMarkRange('link').unsetLink().run()
              setOpen(false)
            }}
          >
            <Link2Off className="size-4" />
            Gỡ liên kết
          </Button>
          <Button type="button" size="sm" onClick={apply}>
            Áp dụng
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
