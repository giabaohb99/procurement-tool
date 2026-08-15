import { useEditorState, type Editor } from '@tiptap/react'
import { FileText, ListTree } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

interface OutlineItem {
  /** 1 · 2 · 3 — dùng để thụt lề cho thấy cấp. */
  level: number
  text: string
  /** Vị trí trong tài liệu, để bấm vào là nhảy tới. */
  pos: number
}

/** Thụt lề theo cấp tiêu đề; cấp lạ (nếu có) coi như cấp 3. */
const LEVEL_INDENT: Record<number, string> = {
  1: 'pl-3',
  2: 'pl-6',
  3: 'pl-9',
}

interface EditorOutlineProps {
  editor: Editor
  className?: string
}

/**
 * MỤC LỤC của văn bản đang soạn — liệt kê các tiêu đề, bấm vào thì nhảy tới.
 *
 * Đọc thẳng từ tài liệu chứ không lưu riêng: tiêu đề là thứ người dùng gõ ra
 * trong lúc soạn, giữ thêm một bản danh sách nữa thì sớm muộn cũng lệch.
 */
export function EditorOutline({ editor, className }: EditorOutlineProps) {
  const outline = useEditorState({
    editor,
    selector: ({ editor: instance }) => {
      const found: OutlineItem[] = []
      instance.state.doc.descendants((node, pos) => {
        if (node.type.name !== 'heading') return
        const text = node.textContent.trim()
        if (text) found.push({ level: Number(node.attrs.level) || 3, text, pos })
      })

      // Tiêu đề gần nhất đứng trước con trỏ là mục đang làm việc. Bấm mục lục
      // hay gõ tiếp trong một đoạn đều cập nhật đúng thanh đang được tô sáng.
      const cursor = instance.state.selection.from
      const active = [...found].reverse().find((item) => item.pos <= cursor)?.pos ?? null
      return { items: found, active }
    },
    // Gõ một chữ là tài liệu đổi, nhưng mục lục chỉ đổi khi tiêu đề đổi — so
    // sánh nội dung để khỏi vẽ lại khung này theo từng phím.
    equalityFn: (a, b) => JSON.stringify(a) === JSON.stringify(b),
  })

  /** `pos + 1` = vào bên TRONG tiêu đề, đặt đúng vào node thì con trỏ nằm ngoài. */
  function goTo(pos: number) {
    editor
      .chain()
      .focus()
      .setTextSelection(pos + 1)
      .scrollIntoView()
      .run()
  }

  return (
    <nav className={cn('min-h-full bg-muted/70 p-3', className)} aria-label="Mục lục văn bản">
      <div className="mb-3 flex items-center gap-2 px-2">
        <ListTree className="size-4 text-primary" />
        <p className="text-sm font-semibold text-navy dark:text-foreground">Mục lục tài liệu</p>
        {outline.items.length > 0 && (
          <span className="ml-auto text-xs text-muted-foreground tabular-nums">
            {outline.items.length} mục
          </span>
        )}
      </div>

      {outline.items.length === 0 ? (
        <p className="rounded-lg border border-dashed bg-background/60 px-3 py-4 text-xs leading-relaxed text-muted-foreground">
          Các tiêu đề bạn thêm vào văn bản sẽ hiện ở đây.
        </p>
      ) : (
        <div className="space-y-1">
          {outline.items.map((item) => {
            const active = item.pos === outline.active
            return (
              <button
                key={`${item.pos}-${item.text}`}
                type="button"
                onClick={() => goTo(item.pos)}
                title={item.text}
                aria-current={active ? 'location' : undefined}
                className={cn(
                  'group relative flex w-full items-center gap-2 rounded-xl py-2 pr-3 text-left text-sm transition-colors',
                  'hover:bg-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                  LEVEL_INDENT[item.level] ?? LEVEL_INDENT[3],
                  active ? 'bg-primary/15 font-medium text-primary' : 'text-muted-foreground',
                  item.level === 1 && !active && 'font-medium text-foreground',
                )}
              >
                {item.level === 1 ? (
                  <FileText className="size-4 shrink-0" />
                ) : (
                  <span
                    aria-hidden
                    className={cn(
                      'h-5 w-0.5 shrink-0 rounded-full bg-border',
                      active && 'bg-primary',
                    )}
                  />
                )}
                <span className="truncate">{item.text}</span>
              </button>
            )
          })}
        </div>
      )}
    </nav>
  )
}
