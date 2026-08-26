import { ArrowUp, Loader2 } from 'lucide-react'
import { useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent } from 'react'

import { cn } from '@/shared/utils/cn'

/** Trần chiều cao ô nhập; quá thì tự cuộn trong ô, không đẩy khung chat lên. */
const MAX_HEIGHT = 200

interface ChatComposerProps {
  /** Không dùng được (chưa cấu hình nhà cung cấp) — khóa hẳn cả ô nhập. */
  disabled: boolean
  /**
   * Đang chờ trả lời. KHÁC `disabled`: ô nhập vẫn gõ được, chỉ chặn GỬI.
   * Khóa cả ô lúc chờ là cướp mất mấy giây người dùng có thể gõ sẵn câu sau —
   * mà câu trả lời hay mất vài giây tới cả chục giây.
   */
  busy: boolean
  /** Ném lỗi nếu gửi hỏng — ô nhập sẽ trả lại nguyên câu vừa gõ. */
  onSend: (message: string) => Promise<void> | void
}

/**
 * Ô soạn câu hỏi: Enter gửi, Shift+Enter xuống dòng.
 *
 * Khác bản cũ ở ba điểm:
 *  - **Ô tự cao dần** theo số dòng thay vì cố định 2 dòng rồi cuộn trong một ô
 *    bé xíu. Câu hỏi ba bốn dòng là chuyện thường, mà không nhìn thấy hết câu
 *    mình vừa gõ thì rất khó soát lại trước khi gửi.
 *  - **Nút gửi nằm TRONG khung**, góc dưới bên phải — cả cụm đọc như một ô nhập
 *    duy nhất, thay vì một ô và một nút rời nhau.
 *  - **Viền sáng lên khi đang gõ** (`focus-within`) để biết con trỏ đang ở đâu.
 */
export function ChatComposer({ disabled, busy, onSend }: ChatComposerProps) {
  const [text, setText] = useState('')
  const oNhap = useRef<HTMLTextAreaElement>(null)

  //  Trả con trỏ về ô nhập ngay khi trả lời xong, để hỏi tiếp không phải với
  //  tay ra chuột.
  useEffect(() => {
    if (!busy && !disabled) oNhap.current?.focus()
  }, [busy, disabled])

  //  Đo lại chiều cao NGAY trong nhịp vẽ (layout effect), không để tới sau khi
  //  sơn xong — dùng `useEffect` thì mắt kịp thấy ô nhảy một cái.
  useLayoutEffect(() => {
    const o = oNhap.current
    if (!o) return
    o.style.height = 'auto' //  phải hạ về auto trước, nếu không nó chỉ phình ra
    o.style.height = `${Math.min(o.scrollHeight, MAX_HEIGHT)}px`
  }, [text])

  const canSend = text.trim().length > 0 && !disabled && !busy

  const send = async () => {
    if (!canSend) return
    const sentence = text.trim()
    //  Xóa ô ngay cho mượt, nhưng GỬI HỎNG THÌ TRẢ LẠI NGUYÊN VĂN.
    //  Trước 25/08/2026 câu hỏi mất trắng khi gọi hỏng: xóa khỏi ô nhập, mà
    //  bong bóng chờ trong luồng cũng bị gỡ — người dùng phải gõ lại từ đầu một
    //  câu vừa nghĩ cả phút (đã dựng lại được bằng cách ép `/chat` trả 500).
    setText('')
    try {
      await onSend(sentence)
    } catch {
      setText(sentence)
      oNhap.current?.focus()
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    //  Bỏ qua khi bộ gõ tiếng Việt đang ghép chữ: Enter lúc đó là "chốt chữ",
    //  không phải "gửi" — không chặn thì gõ dấu xong là câu bay đi mất.
    if (e.nativeEvent.isComposing) return
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send()
    }
  }

  return (
    <div className="shrink-0 px-4 pb-4">
      <div className="mx-auto w-full max-w-3xl">
        <div
          className={cn(
            'flex items-end gap-2 rounded-2xl border bg-card p-2 pl-4 shadow-sm transition-colors',
            'focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/15',
          )}
        >
          <textarea
            ref={oNhap}
            rows={1}
            value={text}
            disabled={disabled}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={busy ? 'Gõ sẵn câu tiếp theo…' : 'Hỏi trợ lý…'}
            aria-label="Câu hỏi cho trợ lý"
            className="max-h-[200px] flex-1 resize-none self-center bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-60"
          />

          <button
            type="button"
            onClick={() => void send()}
            disabled={!canSend}
            title="Gửi"
            aria-label="Gửi câu hỏi"
            className={cn(
              'flex size-8 shrink-0 items-center justify-center rounded-full transition-colors',
              canSend
                ? 'bg-primary text-primary-foreground hover:opacity-90'
                : 'bg-muted text-muted-foreground',
            )}
          >
            {busy ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <ArrowUp className="size-4" />
            )}
          </button>
        </div>

        <p className="mt-2 text-center text-xs text-muted-foreground">
          Enter để gửi · Shift+Enter xuống dòng · Câu trả lời chỉ mang tính đề xuất
        </p>
      </div>
    </div>
  )
}
