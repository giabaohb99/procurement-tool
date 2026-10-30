import { Fragment } from 'react'

import { splitInlineEmphasis } from '@/shared/utils/inline-emphasis'

/**
 * Chữ trơn từ máy chủ có thể mang `**in đậm**` / `*in nghiêng*` (bao-CR-695) — vẽ thành `<strong>` / `<em>`, phần còn
 * lại giữ nguyên là chữ (React tự thoát ký tự, không có đường nào chèn HTML). Xem `splitInlineEmphasis`.
 */
export function InlineEmphasisText({ text }: { text: string }) {
  return (
    <>
      {splitInlineEmphasis(text).map((seg, i) =>
        seg.bold ? (
          <strong key={i} className="font-semibold">
            {seg.text}
          </strong>
        ) : seg.italic ? (
          <em key={i}>{seg.text}</em>
        ) : (
          <Fragment key={i}>{seg.text}</Fragment>
        ),
      )}
    </>
  )
}
