import { useState } from 'react'
import type { MouseEvent } from 'react'

import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
import type { LightboxImage } from '@/shared/ui/image-lightbox'
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
  /**
   * Đang ở khung CHI TIẾT (trang riêng / popup): chữ to hơn một nấc và KHÔNG
   * gấp «Xem thêm» — người ta mở chi tiết là để đọc trọn bài hướng dẫn dài,
   * bắt bấm thêm một phát nữa là thừa (bao-CR-272).
   */
  detail?: boolean
}

/** Nội dung bài viết: giữ xuống dòng, link bấm được, bài dài có «Xem thêm».
 * Bài rich (CR-261) vẽ HTML qua `sanitizeHtml` (DOMPurify — lớp phòng thủ thứ
 * hai sau sanitize server, cùng lý do với bản in văn thư); bài cũ đi đường
 * chữ trơn y như trước, không đổi một pixel. */
export function PostBody({
  body,
  format = FORUM_BODY_FORMAT.plain,
  detail = false,
}: PostBodyProps) {
  const [expanded, setExpanded] = useState(false)
  //  Ảnh TRONG thân bài rich cũng phóng to được như lưới ảnh đính kèm
  //  (bao-CR-275). HTML vẽ bằng dangerouslySetInnerHTML nên không gắn handler
  //  lên từng <img> được — bắt click ủy quyền trên khung, danh sách ảnh gom
  //  từ DOM ngay lúc bấm.
  const lightbox = useImageLightbox()
  const [bodyImages, setBodyImages] = useState<LightboxImage[]>([])
  const rich = format === FORUM_BODY_FORMAT.richHtml
  const text = rich ? stripRichBodyText(body) : body
  // mỗi thẻ khối của bài rich xấp xỉ một "dòng gõ tay" của bài trơn
  const lineCount = rich
    ? (body.match(/<(p|li|h[1-6]|blockquote|tr)\b/g) ?? []).length
    : body.split('\n').length
  const isLong = !detail && (text.length > LONG_CHARS || lineCount > LONG_LINES)
  // 15px trên feed là chuẩn mạng xã hội, nhưng khung chi tiết mở ra để ĐỌC —
  // lên 17px cho đỡ "viết nhỏ nhỏ" (lời chê nguyên văn, bao-CR-272).
  const sizeClass = detail ? 'text-[17px] leading-[1.7]' : 'text-[15px] leading-relaxed'
  if (!body) return null

  function openBodyImage(event: MouseEvent<HTMLDivElement>) {
    const target = event.target
    if (!(target instanceof HTMLImageElement)) return
    const images = Array.from(event.currentTarget.querySelectorAll('img'))
    setBodyImages(images.map((img) => ({ url: img.src, name: img.alt || undefined })))
    lightbox.openAt(images.indexOf(target))
  }

  return (
    <div className="px-4">
      {rich ? (
        <div
          className={cn(
            //  `doc-excerpt-preview` (index.css) — CÙNG bộ luật hiển thị với ô
            //  soạn `doc-rich-field`: gõ sao đăng lên nhìn vậy, không lệch hình.
            'doc-excerpt-preview break-words',
            sizeClass,
            '[&_a]:break-all [&_a]:text-blue-600 [&_a]:hover:underline',
            '[&_img]:cursor-zoom-in',
            isLong && !expanded && 'line-clamp-[8]',
          )}
          onClick={openBodyImage}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(body) }}
        />
      ) : (
        <div
          className={cn(
            'break-words whitespace-pre-wrap',
            sizeClass,
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
      {rich && <ImageLightbox images={bodyImages} {...lightbox.bind} />}
    </div>
  )
}
