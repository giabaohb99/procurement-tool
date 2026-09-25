/**
 * Đoạn trích TÌM KIẾM TOÀN VĂN (phase 07, duoc-CR-477) — tô sáng từ khóa
 * bằng `<mark>` dựng qua React, KHÔNG `dangerouslySetInnerHTML` (Bảo mật §
 * của phase: backend chỉ trả offset, không trả HTML — xem
 * `search_service._snippet`).
 */
import { buildHighlightParts } from '../helpers/search-snippet-highlight'
import type { DocumentSearchHit } from '../types/document-search'
import { cn } from '@/shared/utils/cn'

interface SearchSnippetProps {
  /** `row.search` từ kết quả `/api/documents/search` — `null`/`undefined` thì không dựng gì. */
  hit: DocumentSearchHit | null | undefined
  className?: string
}

/**
 * Dòng đoạn trích dưới trích yếu trong bảng kết quả tìm — nhãn "trúng trong:
 * …" + chữ tô sáng. Không có `snippet` (khớp thuần trên siêu dữ liệu, không
 * phải nội dung/tệp) → không dựng gì, tiêu đề tự nói đủ.
 */
export function SearchSnippet({ hit, className }: SearchSnippetProps) {
  if (!hit?.snippet) return null
  const parts = buildHighlightParts(hit.snippet.text, hit.snippet.highlights)
  if (parts.length === 0) return null

  return (
    <div className={cn('truncate text-xs text-muted-foreground', className)}>
      {hit.match_label && (
        <span className="mr-1 font-medium text-foreground/80">{hit.match_label}:</span>
      )}
      {parts.map((part, index) =>
        part.highlighted ? (
          //  `text-foreground` (thay vì mặc định đen của `<mark>`) đủ tương
          //  phản trên nền vàng nhạt ở giao diện SÁNG, nhưng `--foreground` ở
          //  giao diện TỐI là màu sáng — chữ sáng trên nền vàng nhạt gần như
          //  không đọc được (rà soát 23/09/2026, mục LOW). Ghim riêng một cặp
          //  nền/chữ cho `.dark` thay vì suy theo token chung.
          <mark
            key={index}
            className="rounded-sm bg-yellow-200 px-0.5 text-foreground dark:bg-amber-400/25 dark:text-amber-200"
          >
            {part.text}
          </mark>
        ) : (
          <span key={index}>{part.text}</span>
        ),
      )}
    </div>
  )
}
