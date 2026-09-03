import { useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { sanitizeHtml } from '@/shared/utils/sanitize-html'

import { FORUM_BODY_FORMAT } from '../types/forum-post'
import { stripRichBodyText } from '../utils/rich-body'
import { splitByUrls } from '../utils/split-by-urls'

/**
 * Bài "dài" ước theo số ký tự / số dòng gõ tay thay vì đo pixel: rẻ, không cần
 * ref + reflow, và lệch một hai dòng quanh ngưỡng thì người đọc cũng chẳng thấy
 * khác biệt. Bài rich (CR-261) đo trên CHỮ đã bóc thẻ + đếm thẻ khối làm "dòng".
 */
const LONG_CHARS = 400
const LONG_LINES = 8

interface PostBodyProps {
  body: string
  /** Giá trị `FORUM_BODY_FORMAT` — `richHtml` thì `body` là HTML đã lọc server. */
  format?: number
}

/** Nội dung bài viết: giữ xuống dòng, link bấm được, bài dài có «Xem thêm».
 * Bài rich (CR-261) vẽ HTML qua `sanitizeHtml` (DOMPurify — lớp phòng thủ thứ
 * hai sau sanitize server, cùng lý do với bản in văn thư); bài cũ đi đường
 * chữ trơn y như trước, không đổi một pixel. */
export function PostBody({ body, format = FORUM_BODY_FORMAT.plain }: PostBodyProps) {
  const [expanded, setExpanded] = useState(false)
  const rich = format === FORUM_BODY_FORMAT.richHtml
  const text = rich ? stripRichBodyText(body) : body
  // mỗi thẻ khối của bài rich xấp xỉ một "dòng gõ tay" của bài trơn
  const lineCount = rich
    ? (body.match(/<(p|li|h[1-6]|blockquote|tr)\b/g) ?? []).length
    : body.split('\n').length
  const isLong = text.length > LONG_CHARS || lineCount > LONG_LINES
  if (!body) return null

  return (
    <div className="px-4">
      {rich ? (
        <div
          className={cn(
            //  `doc-excerpt-preview` (index.css) — CÙNG bộ luật hiển thị với ô
            //  soạn `doc-rich-field`: gõ sao đăng lên nhìn vậy, không lệch hình.
            'doc-excerpt-preview text-[15px] leading-relaxed break-words',
            '[&_a]:break-all [&_a]:text-blue-600 [&_a]:hover:underline',
            isLong && !expanded && 'line-clamp-[8]',
          )}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(body) }}
        />
      ) : (
        <div
          className={cn(
            'text-[15px] leading-relaxed break-words whitespace-pre-wrap',
            isLong && !expanded && 'line-clamp-[8]',
          )}
        >
          {splitByUrls(body).map((part, i) =>
            part.type === 'url' ? (
              <a
                key={i}
                href={part.value}
                target="_blank"
                rel="noreferrer"
                className="break-all text-blue-600 hover:underline"
              >
                {part.value}
              </a>
            ) : (
              <span key={i}>{part.value}</span>
            ),
          )}
        </div>
      )}
      {isLong && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-1 text-sm font-medium text-muted-foreground hover:underline"
        >
          {expanded ? 'Thu gọn' : 'Xem thêm'}
        </button>
      )}
    </div>
  )
}
