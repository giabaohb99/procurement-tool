import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ChevronDown, ChevronUp, FilePlus2, FileText, FolderInput, MoreHorizontal, Pencil,
  SquareArrowOutUpRight, Trash2,
} from 'lucide-react'

import MoveArticleDialog from '@/components/move-article-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  createArticle, deleteArticle, levelLabel, renameArticle, reorderSibling,
} from '@/lib/help-article-actions'
import type { HelpNode } from '@/lib/help-tree'
import { cn } from '@/lib/utils'

// Danh sách bài viết CON của bài đang mở.
// compact = true: dạng cột hẹp (sidebar trang soạn bài) — tiêu đề 1 dòng, nút thao tác xuống dưới.
// Mỗi bài con chuyển được sang mục cha khác ngay tại đây, khỏi phải mở bài đó ra rồi mới chuyển.

const MAX_DEPTH = 2

export default function HelpChildArticles({
  parent, depth, tree, onChanged, compact = false,
}: {
  parent: HelpNode
  /** Độ sâu của CHÍNH bài đang mở (0 = mục gốc). */
  depth: number
  /** Cây ĐẦY ĐỦ — hộp thoại chuyển bài cần để liệt kê mục cha hợp lệ. */
  tree: HelpNode[]
  onChanged: () => Promise<void> | void
  compact?: boolean
}) {
  /** Bài con đang mở hộp thoại chuyển mục cha. */
  const [moving, setMoving] = useState<HelpNode | null>(null)
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

  // Chỉ để LỘ hai nút đổi thứ tự (thao tác hay dùng nhất, cần bấm liên tục); phần còn lại gom vào
  // menu "…" — giống dòng ở bảng cây /admin. Bày cả 5 nút ra thì cột phải hẹp không đủ chỗ,
  // tiêu đề bị đẩy xuống hàng riêng, đọc danh sách rất rối.
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

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="size-7" title="Thao tác khác">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-52">
          <DropdownMenuItem asChild>
            <Link to={`/admin/${child.id}`}>
              <SquareArrowOutUpRight /> Mở bài viết
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => run(() => renameArticle(child))}>
            <Pencil /> Đổi tiêu đề
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setMoving(child)}>
            <FolderInput /> Chọn mục cha khác
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onClick={() => run(() => deleteArticle(child))}>
            <Trash2 /> Xóa
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
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

            // Cùng một bố cục MỘT hàng cho cả hai kiểu; chỉ khác lề và nhãn của badge
            return (
              <li
                key={child.id}
                className={cn(
                  'flex items-center gap-2 border-b last:border-b-0 hover:bg-secondary/60',
                  compact ? 'py-1 pl-3 pr-1.5' : 'gap-3 px-4 py-1.5',
                )}
              >
                <FileText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                <Link
                  to={`/admin/${child.id}`}
                  title={child.title}
                  className="min-w-0 flex-1 truncate text-sm text-navy hover:text-primary hover:underline"
                >
                  {child.title}
                </Link>
                {grandChildren > 0 && (
                  <Badge variant="outline" className="shrink-0 px-1.5 font-normal text-muted-foreground">
                    {compact ? grandChildren : `${grandChildren} bài chi tiết`}
                  </Badge>
                )}
                {actions(child, index)}
              </li>
            )
          })}
        </ul>
      )}

      {compact && addButton}

      {moving && (
        <MoveArticleDialog
          tree={tree}
          node={moving}
          open
          onOpenChange={(next) => { if (!next) setMoving(null) }}
          onMoved={onChanged}
        />
      )}
    </div>
  )
}
