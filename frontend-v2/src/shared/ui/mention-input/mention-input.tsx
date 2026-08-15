import { forwardRef, useImperativeHandle, useRef, useState, type KeyboardEvent } from 'react'

import { cn } from '@/shared/utils/cn'
import { MentionSuggestionList } from './mention-suggestion-list'
import { createMentionChip, serializeMentionBody, type MentionPerson } from './serialize-mention-body'
import { useMentionSuggestions } from './use-mention-suggestions'

export interface MentionInputHandle {
  /** Nội dung kèm thẻ `@[id]`, đã cắt khoảng trắng thừa. */
  getValue: () => string
  clear: () => void
  focus: () => void
}

interface MentionInputProps {
  placeholder: string
  /** Tìm người theo chữ đang gõ sau dấu `@`. */
  search: (query: string) => Promise<MentionPerson[]>
  /** Ctrl/Cmd + Enter. */
  onSubmit: () => void
  onCancel?: () => void
  /** Báo ra ngoài để cha bật/tắt nút Gửi — ô này không có state nội dung. */
  onEmptyChange?: (empty: boolean) => void
  className?: string
}

/**
 * Ô soạn bình luận có gõ `@` để nhắc tên.
 *
 * Vì sao KHÔNG dùng `<textarea>`: textarea chỉ chứa được chữ thuần, không hiện
 * được chip. Ở đây dùng `contenteditable`, mỗi người được nhắc là một `<span>`
 * khóa cứng — xóa là mất nguyên cụm.
 *
 * Ô chạy KHÔNG ĐIỀU KHIỂN (uncontrolled): React không ghi đè nội dung trong lúc
 * gõ, nên bộ gõ tiếng Việt (Telex/VNI) không bị nhảy dấu — lỗi kinh điển khi bọc
 * contenteditable bằng state. Cha lấy nội dung qua ref lúc bấm Gửi.
 */
export const MentionInput = forwardRef<MentionInputHandle, MentionInputProps>(
  function MentionInput({ placeholder, search, onSubmit, onCancel, onEmptyChange, className }, ref) {
    const boxRef = useRef<HTMLDivElement>(null)
    const [empty, setEmpty] = useState(true)
    const { people, activeIndex, searching, rangeRef, scan, close, move, setActiveIndex } =
      useMentionSuggestions(search)

    useImperativeHandle(ref, () => ({
      getValue: () => (boxRef.current ? serializeMentionBody(boxRef.current) : ''),
      clear: () => {
        if (boxRef.current) boxRef.current.innerHTML = ''
        close()
        refreshEmpty()
      },
      focus: () => boxRef.current?.focus(),
    }))

    function refreshEmpty() {
      const box = boxRef.current
      const isEmpty = !box || (!box.querySelector('[data-uid]') && !(box.textContent || '').trim())
      setEmpty(isEmpty)
      onEmptyChange?.(isEmpty)
    }

    /** Thay đoạn `@abc` đang gõ bằng chip của người vừa chọn. */
    function pick(person: MentionPerson) {
      const target = rangeRef.current
      const box = boxRef.current
      if (!target || !box) return

      const range = document.createRange()
      range.setStart(target.node, target.start)
      range.setEnd(target.node, Math.min(target.end, (target.node.textContent || '').length))
      range.deleteContents()

      const spacer = document.createTextNode(' ')
      range.insertNode(spacer)
      range.insertNode(createMentionChip(person))

      const selection = window.getSelection()
      if (selection) {
        const after = document.createRange()
        after.setStartAfter(spacer)
        after.collapse(true)
        selection.removeAllRanges()
        selection.addRange(after)
      }

      close()
      refreshEmpty()
      box.focus()
    }

    function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
      if (people.length) {
        if (event.key === 'ArrowDown') {
          event.preventDefault()
          move(1)
          return
        }
        if (event.key === 'ArrowUp') {
          event.preventDefault()
          move(-1)
          return
        }
        if (event.key === 'Enter' || event.key === 'Tab') {
          event.preventDefault()
          pick(people[activeIndex])
          return
        }
        if (event.key === 'Escape') {
          event.preventDefault()
          close()
          return
        }
      }
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault()
        onSubmit()
        return
      }
      if (event.key === 'Escape' && onCancel) {
        event.preventDefault()
        onCancel()
      }
    }

    return (
      <div className="relative">
        <div
          ref={boxRef}
          contentEditable
          suppressContentEditableWarning
          role="textbox"
          aria-multiline="true"
          aria-label={placeholder}
          onInput={() => {
            refreshEmpty()
            scan(boxRef.current)
          }}
          onKeyUp={(event) => {
            // Menu đang mở thì lên/xuống là để CHỌN NGƯỜI, con trỏ không nhúc
            // nhích → đừng dò lại kẻo highlight nhảy về dòng đầu.
            if (people.length && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) return
            if (event.key.startsWith('Arrow') || event.key === 'Home' || event.key === 'End') {
              scan(boxRef.current)
            }
          }}
          onKeyDown={handleKeyDown}
          // Chờ cú bấm chuột vào menu kịp chạy rồi mới đóng.
          onBlur={() => setTimeout(close, 150)}
          onPaste={(event) => {
            // Chỉ lấy chữ thuần — không kéo theo màu mè, thẻ HTML từ nơi khác.
            event.preventDefault()
            const text = event.clipboardData.getData('text/plain')
            document.execCommand('insertText', false, text)
          }}
          className={cn(
            'max-h-56 min-h-16 w-full overflow-y-auto whitespace-pre-wrap break-words rounded-md border bg-transparent px-3 py-2 text-base shadow-xs outline-none md:text-sm',
            'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50',
            className,
          )}
        />
        {empty && (
          <span className="pointer-events-none absolute left-3 top-2 text-base text-muted-foreground md:text-sm">
            {placeholder}
          </span>
        )}
        <MentionSuggestionList
          people={people}
          activeIndex={activeIndex}
          searching={searching}
          onHover={setActiveIndex}
          onPick={pick}
        />
      </div>
    )
  },
)
