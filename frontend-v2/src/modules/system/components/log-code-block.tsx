import { CopyButton } from '@/shared/ui/copy-button'
import { cn } from '@/shared/utils/cn'
import { logBodyText } from '../utils/system-log-format'
import { tokenizeJson, type JsonTokenKind } from '../utils/tokenize-json'

/** Màu từng loại token — hai tông cho hai chế độ nền. */
const TOKEN_CLASS: Record<JsonTokenKind, string> = {
  key: 'text-sky-700 dark:text-sky-300',
  string: 'text-emerald-700 dark:text-emerald-300',
  number: 'text-amber-700 dark:text-amber-400',
  keyword: 'text-violet-700 dark:text-violet-300',
  plain: '',
}

interface LogCodeBlockProps {
  title: string
  /** Chuỗi (traceback) HOẶC object JSON (thân yêu cầu / trả về) — xem `logBodyText`. */
  text?: unknown
  tone?: 'default' | 'danger'
}

/**
 * Khối JSON / traceback của màn Nhật ký hệ thống.
 *
 * `undefined` nghĩa là backend đã lược (không có quyền) — nhưng nhánh đó đã được
 * chặn ở tầng trên, nên ở đây rỗng chỉ còn nghĩa *lượt gọi vốn không có phần
 * này* (GET không có thân, lượt chạy trót lọt không có traceback). Vẫn nói rõ
 * thay vì vẽ một khung trống.
 *
 * ⚠️ Tô màu CHỈ chạy khi giá trị gốc là **object** (`typeof text === 'object'`),
 * tức thân thật sự là JSON. Traceback là văn xuôi: cho nó qua bộ soi mẫu thì mọi
 * số hiệu dòng và mọi đoạn trong nháy kép sáng lên lung tung, đọc còn khó hơn
 * chữ đen trơn — mà traceback là thứ người ta đọc kỹ nhất ở màn này.
 */
export function LogCodeBlock({ title, text, tone = 'default' }: LogCodeBlockProps) {
  const body = logBodyText(text)
  const highlight = typeof text === 'object' && text !== null

  return (
    <div className="overflow-hidden rounded-lg border">
      {/*  Thanh tiêu đề: chữ nhỏ + nền mờ, để phần đáng nhìn là khối mã bên dưới. */}
      <div className="flex items-center justify-between gap-2 border-b bg-muted px-3 py-2">
        <span className="text-xs font-medium text-muted-foreground">{title}</span>
        {body && <CopyButton value={body} label={title.toLowerCase()} />}
      </div>

      {body ? (
        //  ⚠️ `whitespace-pre` chứ KHÔNG `whitespace-pre-wrap` + `break-all` như
        //  bản trước: `break-all` cắt chữ giữa từ nên một khóa JSON dài bị xé làm
        //  đôi giữa dòng, và thụt đầu dòng mất nghĩa vì dòng gập vào lại thẳng
        //  lề trái. Khối mã thì cuộn NGANG, đừng gập.
        <pre
          className={cn(
            'max-h-80 overflow-auto bg-muted/30 p-3 font-mono text-xs leading-relaxed whitespace-pre',
            tone === 'danger' && 'text-destructive',
          )}
        >
          {highlight ? (
            tokenizeJson(body).map((token, index) => (
              <span key={index} className={TOKEN_CLASS[token.kind]}>
                {token.text}
              </span>
            ))
          ) : (
            body
          )}
        </pre>
      ) : (
        <p className="p-3 text-xs italic text-muted-foreground">Không có nội dung.</p>
      )}
    </div>
  )
}
