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
import { cn } from '@/lib/utils'

// Danh sách bài viết CON của bài đang mở.
// compact = true: dạng cột hẹp (sidebar trang soạn bài) — tiêu đề 1 dòng, nút thao tác xuống dưới.

const MAX_DEPTH = 2

export default function HelpChildArticles({
  parent, depth, onChanged, compact = false,
}: {
  parent: HelpNode
  /** Độ sâu của CHÍNH bài đang mở (0 = mục gốc). */
  depth: number
  onChanged: () => Promise<void> | void
  compact?: boolean
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
      <p className="py-2 text-sm text-muted-foreground">
        Đây là bài chi tiết — cấu trúc tài liệu chỉ sâu 3 cấp nên không thêm bài con được.
      </p>
    )
  }

  const addButton = (
    <Button
      size="sm"
      variant={compact ? 'outline' : 'default'}
      className={compact ? 'w-full' : undefined}
      onClick={() => run(() => createArticle(parent.id, children.length, childDepth))}
    >
      <FilePlus2 /> Thêm {levelLabel(childDepth).toLowerCase()}
    </Button>
  )

  const actions = (child: HelpNode, index: number) => (
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
      <Button variant="ghost" size="icon" title="Xóa"
              className="size-7 text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={() => run(() => deleteArticle(child))}>
        <Trash2 className="size-4" />
      </Button>
    </div>
  )

  return (
    <div className="space-y-3">
      {!compact && (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm text-muted-foreground">
            {children.length > 0
              ? `${children.length} ${levelLabel(childDepth).toLowerCase()} bên trong bài này.`
              : `Chưa có ${levelLabel(childDepth).toLowerCase()} nào bên trong bài này.`}
          </p>
          {addButton}
        </div>
      )}

      {children.length === 0 ? (
        <div className={cn('rounded-md border border-dashed text-center', compact ? 'px-4 py-6' : 'px-6 py-10')}>
          <FilePlus2 className="mx-auto mb-2 size-7 text-muted-foreground" strokeWidth={1.5} />
          <strong className="block text-sm text-navy">Chưa có bài viết con</strong>
          <span className="text-xs text-muted-foreground">
            Bài con sẽ hiện thành danh sách ở trang danh mục bên phía người dùng.
          </span>
        </div>
      ) : (
        <ul className="overflow-hidden rounded-md border">
          {children.map((child, index) => {
            const grandChildren = child.children?.length || 0

            if (compact) {
              return (
                <li key={child.id} className="border-b px-3 py-2 last:border-b-0 hover:bg-secondary/60">
                  <div className="flex items-center gap-2">
                    <FileText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                    <Link
                      to={`/admin/${child.id}`}
                      className="min-w-0 flex-1 truncate text-sm text-navy hover:text-primary hover:underline"
                    >
                      {child.title}
                    </Link>
                    {grandChildren > 0 && (
                      <Badge variant="outline" className="shrink-0 px-1.5 font-normal text-muted-foreground">
                        {grandChildren}
                      </Badge>
                    )}
                  </div>
                  <div className="-mr-1 mt-0.5 flex justify-end">{actions(child, index)}</div>
                </li>
              )
            }

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
                {actions(child, index)}
              </li>
            )
          })}
        </ul>
      )}

      {compact && addButton}
    </div>
  )
}
