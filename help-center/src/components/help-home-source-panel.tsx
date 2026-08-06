import { useState } from 'react'
import { FileText, Folder, GripVertical, MessageCircleQuestion, Search } from 'lucide-react'

import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { Faq } from '@/lib/faq-api'
import { flattenTree, type HelpNode } from '@/lib/help-tree'
import { cn } from '@/lib/utils'

// Cột nguồn ở trang "Bố cục trang chủ": bài viết và câu hỏi thường gặp — KÉO sang khung bên phải
// để đưa lên trang chủ. Chỉ là nơi lấy, không sửa gì ở đây.
// Khung "Mẹo tra cứu" không dùng cột này: thẻ của nó là nội dung tự nhập, không tham chiếu gì.

/** Kiểu dữ liệu gắn vào dataTransfer khi kéo. Khung bên phải đọc lại để biết đang thả cái gì. */
export interface HomeDragPayload {
  /** `item` = phần tử ĐANG nằm trong khung (kéo để đổi thứ tự); còn lại là nguồn kéo vào. */
  kind: 'article' | 'faq' | 'item'
  id: number
  /** Chỉ có khi kind = 'item'. */
  sectionId?: number
}

export const HOME_DRAG_MIME = 'application/x-help-home'

export function setDragPayload(e: React.DragEvent, payload: HomeDragPayload): void {
  e.dataTransfer.effectAllowed = 'copyMove'
  e.dataTransfer.setData(HOME_DRAG_MIME, JSON.stringify(payload))
  // Firefox chỉ bắt đầu kéo khi dataTransfer có text/plain
  e.dataTransfer.setData('text/plain', String(payload.id))
}

export function readDragPayload(e: React.DragEvent): HomeDragPayload | null {
  try {
    return JSON.parse(e.dataTransfer.getData(HOME_DRAG_MIME)) as HomeDragPayload
  } catch {
    return null
  }
}

/** Bỏ dấu + chữ thường để lọc theo kiểu gõ không dấu. */
function fold(text: string): string {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase()
}

export default function HelpHomeSourcePanel({
  tree, faqs,
}: {
  tree: HelpNode[]
  faqs: Faq[]
}) {
  const [filter, setFilter] = useState('')
  const kw = fold(filter.trim())

  const articles = flattenTree(tree).filter(({ node }) => !kw || fold(node.title).includes(kw))
  const questions = faqs.filter((f) => !kw || fold(f.question).includes(kw))

  return (
    <Tabs defaultValue="articles" className="flex h-full flex-col">
      <TabsList className="w-full">
        <TabsTrigger value="articles" className="flex-1">Bài viết</TabsTrigger>
        <TabsTrigger value="faqs" className="flex-1">Câu hỏi</TabsTrigger>
      </TabsList>

      <div className="relative my-2">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Tìm nhanh..."
          className="h-8 pl-8 text-sm"
        />
      </div>

      <p className="mb-2 text-xs text-muted-foreground">
        Kéo một dòng sang khung bên phải để đưa lên trang chủ.
      </p>

      <TabsContent value="articles" className="mt-0 min-h-0 flex-1">
        <SourceList
          rows={articles.map(({ node, depth }) => ({
            id: node.id, label: node.title, depth, isFolder: depth === 0,
          }))}
          kind="article"
          emptyText="Không có bài viết khớp từ khóa."
        />
      </TabsContent>

      <TabsContent value="faqs" className="mt-0 min-h-0 flex-1">
        <SourceList
          rows={questions.map((f) => ({ id: f.id, label: f.question, depth: 0, isFolder: false }))}
          kind="faq"
          emptyText="Chưa có câu hỏi thường gặp nào."
        />
      </TabsContent>
    </Tabs>
  )
}

interface SourceRow {
  id: number
  label: string
  depth: number
  isFolder: boolean
}

function SourceList({
  rows, kind, emptyText,
}: {
  rows: SourceRow[]
  kind: 'article' | 'faq'
  emptyText: string
}) {
  if (rows.length === 0) {
    return (
      <p className="rounded-md border border-dashed px-3 py-6 text-center text-xs text-muted-foreground">
        {emptyText}
      </p>
    )
  }

  return (
    <ul className="h-full overflow-y-auto rounded-md border">
      {rows.map((row) => (
        <li
          key={row.id}
          draggable
          onDragStart={(e) => setDragPayload(e, { kind, id: row.id })}
          title={row.label}
          className="flex cursor-grab items-center gap-1.5 border-b px-2 py-1.5 text-sm last:border-b-0 hover:bg-secondary/60 active:cursor-grabbing"
          style={{ paddingLeft: row.depth * 12 + 8 }}
        >
          <GripVertical className="size-3.5 shrink-0 text-muted-foreground/60" />
          {kind === 'faq'
            ? <MessageCircleQuestion className="size-4 shrink-0 text-primary" strokeWidth={1.75} />
            : row.isFolder
              ? <Folder className="size-4 shrink-0 text-primary" strokeWidth={1.75} />
              : <FileText className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />}
          <span className={cn('min-w-0 flex-1 truncate text-navy', row.isFolder && 'font-medium')}>
            {row.label}
          </span>
        </li>
      ))}
    </ul>
  )
}
