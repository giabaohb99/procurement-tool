import { ArrowUp, FileText, Image as ImageIcon, Loader2, Paperclip, X } from 'lucide-react'
import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ClipboardEvent,
  type KeyboardEvent,
} from 'react'
import { toast } from 'sonner'

import { cn } from '@/shared/utils/cn'
import { assistantApi } from '../api/assistant-api'
import type { AssistantAttachment } from '../types/assistant'
import {
  ACCEPT_ATTACHMENTS,
  MAX_ATTACHMENTS,
  validateAttachment,
} from '../utils/attachment-rules'

/** Trần chiều cao ô nhập; quá thì tự cuộn trong ô, không đẩy khung chat lên. */
const MAX_HEIGHT = 200

/**
 * Một tệp đang gắn vào câu sắp gửi. Tải lên NGAY khi chọn (khuôn tải-trước-gắn-sau):
 * `meta` chưa có = đang tải; tải hỏng thì chip bị gỡ (toast lỗi đã hiện ở tầng API).
 */
interface PendingAttachment {
  key: number
  name: string
  type: string
  meta?: AssistantAttachment
}

interface ChatComposerProps {
  /** Không dùng được (chưa cấu hình nhà cung cấp) — khóa hẳn cả ô nhập. */
  disabled: boolean
  /**
   * Đang chờ trả lời. KHÁC `disabled`: ô nhập vẫn gõ được, chỉ chặn GỬI.
   * Khóa cả ô lúc chờ là cướp mất mấy giây người dùng có thể gõ sẵn câu sau —
   * mà câu trả lời hay mất vài giây tới cả chục giây.
   */
  busy: boolean
  /** Ném lỗi nếu gửi hỏng — ô nhập sẽ trả lại nguyên câu + tệp vừa gắn. */
  onSend: (message: string, attachments?: AssistantAttachment[]) => Promise<void> | void
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
 *
 * CR-204: thêm đính kèm ảnh/PDF — nút kẹp giấy, DÁN ảnh thẳng vào ô (Ctrl+V ảnh
 * chụp màn hình là ca dùng chính), chip tệp có nút gỡ. Tệp tải lên ngay khi chọn,
 * gửi tin chỉ truyền id.
 */
export function ChatComposer({ disabled, busy, onSend }: ChatComposerProps) {
  const [text, setText] = useState('')
  const [attachments, setAttachments] = useState<PendingAttachment[]>([])
  const oNhap = useRef<HTMLTextAreaElement>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const nextKey = useRef(1)

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

  const addFiles = (files: File[]) => {
    if (disabled || files.length === 0) return
    let slots = MAX_ATTACHMENTS - attachments.length
    for (const file of files) {
      const error = validateAttachment(file)
      if (error) {
        toast.error(error)
        continue
      }
      if (slots <= 0) {
        toast.error(`Tối đa ${MAX_ATTACHMENTS} tệp mỗi tin`)
        break
      }
      slots -= 1
      const key = nextKey.current++
      setAttachments((prev) => [...prev, { key, name: file.name, type: file.type }])
      void assistantApi
        .uploadAttachment(file)
        .then((meta) => {
          setAttachments((prev) => prev.map((a) => (a.key === key ? { ...a, meta } : a)))
        })
        .catch(() => {
          //  Toast lỗi đã hiện ở tầng API — chỉ cần gỡ chip đang quay.
          setAttachments((prev) => prev.filter((a) => a.key !== key))
        })
    }
  }

  const onPaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
    //  Dán ảnh chụp màn hình (một dòng Excel, một đoạn báo giá...) thẳng vào ô.
    //  Chỉ chặn mặc định khi clipboard THẬT SỰ có tệp, kẻo nuốt mất dán chữ thường.
    const files = Array.from(e.clipboardData?.files ?? [])
    if (files.length === 0) return
    e.preventDefault()
    addFiles(files)
  }

  const uploading = attachments.some((a) => !a.meta)
  const readyAttachments = attachments
    .map((a) => a.meta)
    .filter((m): m is AssistantAttachment => m != null)
  const canSend =
    (text.trim().length > 0 || readyAttachments.length > 0) && !disabled && !busy && !uploading

  const send = async () => {
    if (!canSend) return
    const sentence = text.trim()
    const sentAttachments = attachments
    //  Xóa ô ngay cho mượt, nhưng GỬI HỎNG THÌ TRẢ LẠI NGUYÊN VĂN (cả chữ lẫn tệp).
    //  Trước 25/08/2026 câu hỏi mất trắng khi gọi hỏng: xóa khỏi ô nhập, mà
    //  bong bóng chờ trong luồng cũng bị gỡ — người dùng phải gõ lại từ đầu một
    //  câu vừa nghĩ cả phút (đã dựng lại được bằng cách ép `/chat` trả 500).
    setText('')
    setAttachments([])
    try {
      await onSend(sentence, readyAttachments.length > 0 ? readyAttachments : undefined)
    } catch {
      setText(sentence)
      setAttachments(sentAttachments)
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
            'rounded-2xl border bg-card p-2 pl-4 shadow-sm transition-colors',
            'focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/15',
          )}
        >
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1 pb-2">
              {attachments.map((a) => (
                <span
                  key={a.key}
                  className="inline-flex max-w-56 items-center gap-1.5 rounded-lg border bg-muted/60 py-1 pr-1 pl-2 text-xs"
                >
                  {!a.meta ? (
                    <Loader2 className="size-3.5 shrink-0 animate-spin text-muted-foreground" />
                  ) : a.type === 'application/pdf' ? (
                    <FileText className="size-3.5 shrink-0 text-muted-foreground" />
                  ) : (
                    <ImageIcon className="size-3.5 shrink-0 text-muted-foreground" />
                  )}
                  <span className="truncate">{a.name}</span>
                  <button
                    type="button"
                    onClick={() =>
                      setAttachments((prev) => prev.filter((x) => x.key !== a.key))
                    }
                    title="Gỡ tệp"
                    aria-label={`Gỡ tệp ${a.name}`}
                    className="flex size-5 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <X className="size-3.5" />
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="flex items-end gap-2">
            <textarea
              ref={oNhap}
              rows={1}
              value={text}
              disabled={disabled}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKeyDown}
              onPaste={onPaste}
              placeholder={busy ? 'Gõ sẵn câu tiếp theo…' : 'Hỏi trợ lý…'}
              aria-label="Câu hỏi cho trợ lý"
              className="max-h-[200px] flex-1 resize-none self-center bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-60"
            />

            <input
              ref={fileInput}
              type="file"
              accept={ACCEPT_ATTACHMENTS}
              multiple
              aria-label="Chọn tệp đính kèm"
              className="hidden"
              onChange={(e) => {
                addFiles(Array.from(e.target.files ?? []))
                //  Cho phép chọn LẠI đúng tệp vừa gỡ — không reset thì onChange câm.
                e.target.value = ''
              }}
            />
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              disabled={disabled || attachments.length >= MAX_ATTACHMENTS}
              title="Đính kèm ảnh hoặc PDF"
              aria-label="Đính kèm ảnh hoặc PDF"
              className={cn(
                'flex size-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors',
                'hover:bg-muted hover:text-foreground disabled:opacity-40 disabled:hover:bg-transparent',
              )}
            >
              <Paperclip className="size-4" />
            </button>

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
        </div>

        <p className="mt-2 text-center text-xs text-muted-foreground">
          Enter để gửi · Shift+Enter xuống dòng · Đính kèm ảnh/PDF hoặc dán ảnh · Câu trả lời
          chỉ mang tính đề xuất
        </p>
      </div>
    </div>
  )
}
