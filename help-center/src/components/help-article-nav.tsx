import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'

import { useArticlePath } from '@/lib/help-slug'
import type { HelpNode } from '@/lib/help-tree'
import { cn } from '@/lib/utils'

// Cụm nút "Bài trước / Bài tiếp theo" ở cuối bài viết — để đọc tài liệu xuyên suốt như lật trang sách.
// Thứ tự lấy từ findReadingNeighbors (duyệt cây theo chiều sâu), không phải chỉ trong cùng thư mục.

export default function HelpArticleNav({
  prev,
  next,
}: {
  prev: HelpNode | null
  next: HelpNode | null
}) {
  if (!prev && !next) return null

  return (
    <nav className="mt-10 grid gap-3 border-t pt-6 sm:grid-cols-2">
      {/* Ô trống giữ chỗ để nút "Bài tiếp theo" luôn nằm bên phải khi không có bài trước */}
      {prev ? <NavCard node={prev} dir="prev" /> : <span className="hidden sm:block" />}
      {next && <NavCard node={next} dir="next" />}
    </nav>
  )
}

// Hai thẻ phải TRÔNG NHƯ NHAU, chỉ khác hướng: mũi tên ghim ở mép ngoài (trái cho bài trước,
// phải cho bài tiếp theo), phần chữ mới đảo canh lề khi hai thẻ nằm cạnh nhau.
// Trước đây mũi tên nằm lẫn trong dòng nhãn nên hai thẻ cao thấp khác nhau và lúc xếp chồng
// (màn hẹp) thì nhìn như hai kiểu nút khác hẳn nhau.
function NavCard({ node, dir }: { node: HelpNode; dir: 'prev' | 'next' }) {
  const isNext = dir === 'next'
  const pathOf = useArticlePath()
  const Arrow = isNext ? ArrowRight : ArrowLeft

  return (
    <Link
      to={pathOf(node.id)}
      className={cn(
        'group flex h-full items-center gap-3 rounded-lg border px-4 py-3 transition-colors',
        'hover:border-primary hover:bg-muted/50',
        isNext && 'flex-row-reverse',
      )}
    >
      <Arrow className="size-4 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />

      <span className={cn('flex min-w-0 flex-1 flex-col gap-0.5', isNext && 'sm:items-end sm:text-right')}>
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {isNext ? 'Bài tiếp theo' : 'Bài trước'}
        </span>
        <span className="line-clamp-2 text-[15px] font-semibold leading-snug text-navy transition-colors group-hover:text-primary">
          {node.title}
        </span>
      </span>
    </Link>
  )
}
