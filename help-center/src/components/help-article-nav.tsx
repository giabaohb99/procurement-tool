import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'

import { useArticlePath } from '@/lib/help-slug'
import type { HelpNode } from '@/lib/help-tree'

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

function NavCard({ node, dir }: { node: HelpNode; dir: 'prev' | 'next' }) {
  const isNext = dir === 'next'
  const pathOf = useArticlePath()
  return (
    <Link
      to={pathOf(node.id)}
      className={`group flex flex-col gap-1 rounded-lg border px-4 py-3 transition-colors hover:border-primary hover:bg-muted/50 ${
        isNext ? 'sm:items-end sm:text-right' : ''
      }`}
    >
      <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {!isNext && <ArrowLeft className="size-3.5" />}
        {isNext ? 'Bài tiếp theo' : 'Bài trước'}
        {isNext && <ArrowRight className="size-3.5" />}
      </span>
      <span className="line-clamp-2 text-[15px] font-semibold leading-snug text-navy transition-colors group-hover:text-primary">
        {node.title}
      </span>
    </Link>
  )
}
