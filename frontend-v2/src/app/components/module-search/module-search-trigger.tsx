import { Search } from 'lucide-react'
import { useEffect, useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { ModuleSearchDialog } from './module-search-dialog'

/** Máy Apple hiện phím ⌘, máy khác hiện Ctrl — nhãn sai phím là người dùng bấm mãi không ăn. */
const IS_APPLE = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.userAgent)

/**
 * Ô tìm phân hệ ở đầu màn chọn phân hệ (duoc-CR-781), ngang hàng lời chào: trông như ô nhập kèm nhãn phím tắt.
 * Bấm vào hoặc nhấn Ctrl/⌘ + K đều mở `ModuleSearchDialog`.
 *
 * Là NÚT chứ không phải ô gõ thật: gõ thật tại chỗ thì kết quả phải bung thành danh sách sổ xuống đè lên lưới
 * thẻ; mở hộp riêng thì có chỗ cho đủ kết quả gom theo phân hệ và phím mũi tên chạy đúng.
 */
export function ModuleSearchTrigger({ className }: { className?: string }) {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        //  Chặn mặc định: Ctrl+K của Chrome / Firefox là nhảy lên ô tìm của trình duyệt.
        event.preventDefault()
        setOpen((current) => !current)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={cn(
          'flex h-10 w-full items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm text-muted-foreground shadow-xs transition-colors hover:border-ring/60 hover:text-foreground',
          className,
        )}
      >
        <Search className="size-4 shrink-0" />
        <span className="flex-1 truncate text-left">Tìm phân hệ, chức năng…</span>
        {/*  Điện thoại không có bàn phím vật lý — nhãn phím tắt chỉ chiếm chỗ. */}
        <kbd className="rounded border bg-muted px-1.5 py-0.5 font-sans text-[11px] text-muted-foreground max-sm:hidden">
          {IS_APPLE ? '⌘' : 'Ctrl'} K
        </kbd>
      </button>
      <ModuleSearchDialog open={open} onOpenChange={setOpen} />
    </>
  )
}
