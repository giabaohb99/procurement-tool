import { useState } from 'react'

import { cn } from '@/shared/utils/cn'

import { splitByUrls } from '../utils/split-by-urls'

/**
 * Bài "dài" ước theo số ký tự / số dòng gõ tay thay vì đo pixel: rẻ, không cần
 * ref + reflow, và lệch một hai dòng quanh ngưỡng thì người đọc cũng chẳng thấy
 * khác biệt.
 */
const LONG_CHARS = 400
const LONG_LINES = 8

interface PostBodyProps {
  body: string
}

/** Nội dung bài viết: giữ xuống dòng, link bấm được, bài dài có «Xem thêm». */
export function PostBody({ body }: PostBodyProps) {
  const [expanded, setExpanded] = useState(false)
  const isLong = body.length > LONG_CHARS || body.split('\n').length > LONG_LINES
  if (!body) return null

  return (
    <div className="px-4">
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
