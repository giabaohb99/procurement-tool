import { Link } from 'react-router-dom'

import HelpArticleIcon from '@/components/help-article-icon'
import type { HelpNode } from '@/lib/help-tree'

// Thẻ danh mục: icon vuông 48px nền teal nhạt bên trái, tiêu đề + mô tả ngắn bên phải.
// Nền trắng, không viền, đổ bóng mảnh — đồng bộ với lưới "Các Phân hệ" của hệ Văn thư.
// Icon và mô tả đều lấy từ bài viết (người soạn nhập ở khu quản trị).
// Bài chưa chọn icon -> icon mặc định theo vị trí; bài chưa nhập mô tả -> bỏ trống dòng mô tả,
// KHÔNG chèn câu đếm số bài con thay thế (đó là chữ độn, không mang thông tin cho người đọc).

export default function HelpCategoryTiles({ nodes }: { nodes: HelpNode[] }) {
  if (nodes.length === 0) return null

  return (
    <div className="grid grid-cols-1 items-start gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {nodes.map((node, index) => (
        <Link
          key={node.id}
          to={`/${node.id}`}
          className="flex h-full items-start gap-4 rounded-xl bg-card p-6 shadow-[0_4px_12px_rgba(0,0,0,0.03)] transition-all hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(0,0,0,0.07)]"
        >
          <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-primary/8 text-primary">
            <HelpArticleIcon icon={node.icon} index={index} className="size-6" />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-base font-semibold leading-snug text-ink">
              {node.title}
            </span>
            {node.summary && (
              <span className="mt-1 block text-sm leading-relaxed text-ink-muted">
                {node.summary}
              </span>
            )}
          </span>
        </Link>
      ))}
    </div>
  )
}
