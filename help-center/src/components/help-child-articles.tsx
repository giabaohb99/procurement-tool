import { Link } from 'react-router-dom'
import {
  ChevronDown, ChevronUp, FilePlus2, FileText, Pencil, SquareArrowOutUpRight, Trash2,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  createArticle, deleteArticle, levelLabel, renameArticle, reorderSibling,
} from '@/lib/help-article-actions'
import type { HelpNode } from '@/lib/help-tree'

// Danh sách bài viết CON của bài đang mở (tab "Bài viết con" ở /admin/:id).
// Cho phép thêm / đổi tên / đổi thứ tự / xóa ngay tại chỗ, không cần về trang danh sách.

const MAX_DEPTH = 2

export default function HelpChildArticles({
  parent, depth, onChanged,
}: {
  parent: HelpNode
  /** Độ sâu của CHÍNH bài đang mở (0 = mục gốc). */
  depth: number
  onChanged: () => Promise<void> | void
}) {
  const children = parent.children || []
  const childDepth = depth + 1
  const canAddChild = depth < MAX_DEPTH

  const run = async (fn: () => Promise<boolean | number | null>) => {
    const changed = await fn()
    if (changed) await onChanged()
  }

  if (!canAddChild) {
    return (
      <div className="rounded-md border border-dashed px-6 py-10 text-center">
        <FileText className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
        <strong className="block text-navy">Đây là bài chi tiết</strong>
        <span className="text-sm text-muted-foreground">
          Cấu trúc tài liệu chỉ sâu 3 cấp nên bài này không thêm bài con được.
        </span>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {children.length > 0
            ? `${children.length} ${levelLabel(childDepth).toLowerCase()} bên trong bài này.`
            : `Chưa có ${levelLabel(childDepth).toLowerCase()} nào bên trong bài này.`}
        </p>
        <Button
          size="sm"
          onClick={() => run(() => createArticle(parent.id, children.length, childDepth))}
        >
          <FilePlus2 /> Thêm {levelLabel(childDepth).toLowerCase()}
        </Button>
      </div>

      {children.length === 0 ? (
        <div className="rounded-md border border-dashed px-6 py-10 text-center">
          <FilePlus2 className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
          <strong className="block text-navy">Chưa có bài viết con</strong>
          <span className="text-sm text-muted-foreground">
            Bài con sẽ hiện thành danh sách ở trang danh mục bên phía người dùng.
          </span>
        </div>
      ) : (
        <ul className="overflow-hidden rounded-md border">
          {children.map((child, index) => {
            const grandChildren = child.children?.length || 0
            return (
              <li
                key={child.id}
                className="flex items-center gap-3 border-b px-4 py-2.5 last:border-b-0 hover:bg-secondary/60"
              >
                <FileText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                <Link
                  to={`/admin/${child.id}`}
                  className="min-w-0 flex-1 truncate text-sm text-navy hover:text-primary hover:underline"
                >
                  {child.title}
                </Link>

                {grandChildren > 0 && (
                  <Badge variant="outline" className="shrink-0 font-normal text-muted-foreground">
                    {grandChildren} bài chi tiết
                  </Badge>
                )}

                <div className="flex shrink-0 items-center gap-0.5">
                  <Button variant="ghost" size="icon" className="size-7" title="Lên"
                          disabled={index === 0}
                          onClick={() => run(() => reorderSibling(children, index, -1))}>
                    <ChevronUp className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="size-7" title="Xuống"
                          disabled={index === children.length - 1}
                          onClick={() => run(() => reorderSibling(children, index, 1))}>
                    <ChevronDown className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="size-7" title="Đổi tiêu đề"
                          onClick={() => run(() => renameArticle(child))}>
                    <Pencil className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="size-7" title="Mở bài viết" asChild>
                    <Link to={`/admin/${child.id}`}><SquareArrowOutUpRight className="size-4" /></Link>
                  </Button>
                  <Button
                    variant="ghost" size="icon" title="Xóa"
                    className="size-7 text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => run(() => deleteArticle(child))}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
