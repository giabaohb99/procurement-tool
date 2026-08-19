import { useEditorState, type Editor } from '@tiptap/react'
import { FileText, ListTree } from 'lucide-react'
import { memo, useCallback, useMemo } from 'react'

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
  // Chỉ lấy hai thứ RẺ để so sánh. ProseMirror dựng `doc` MỚI mỗi lần nội dung
  // đổi và giữ nguyên `doc` cũ khi chỉ di chuyển con trỏ, nên so bằng tham
  // chiếu là đủ — khỏi phải duyệt cả cây tài liệu (và `JSON.stringify` nó) ở
  // mỗi lần gõ phím, thứ trở nên rất nặng với tài liệu nhập từ tệp Word dài.
  const { doc, cursor } = useEditorState({
    editor,
    selector: ({ editor: instance }) => ({
      doc: instance.state.doc,
      cursor: instance.state.selection.from,
    }),
    equalityFn: (a, b) => a.doc === b?.doc && a.cursor === b?.cursor,
  })

  const items = useMemo(() => {
    const found: OutlineItem[] = []
    doc.descendants((node, pos) => {
      // Đoạn văn / tiêu đề là khối chứa CHỮ: không có tiêu đề nào nằm bên trong
      // nữa, chui vào duyệt tiếp từng ký tự chỉ tổ mất thời gian.
      if (!node.isTextblock) return true
      if (node.type.name !== 'heading') return false
      const text = node.textContent.trim()
      if (text) found.push({ level: Number(node.attrs.level) || 3, text, pos })
      return false
    })
    return found
  }, [doc])

  // Tiêu đề gần nhất đứng trước con trỏ là mục đang làm việc. Bấm mục lục hay
  // gõ tiếp trong một đoạn đều cập nhật đúng thanh đang được tô sáng.
  const active = useMemo(() => {
    let found: number | null = null
    for (const item of items) {
      if (item.pos > cursor) break
      found = item.pos
    }
    return found
  }, [items, cursor])

  /**
   * Nhảy tới tiêu đề: đặt con trỏ vào đó rồi CUỘN TRANG GIẤY tới nơi.
   *
   * `pos + 1` = vào bên TRONG tiêu đề, đặt đúng vào node thì con trỏ nằm ngoài.
   *
   * Phải tự cuộn bằng DOM thay vì dùng `.scrollIntoView()` của ProseMirror: lệnh
   * đó cuộn theo con trỏ, mà văn bản đã ban hành thì mở ở chế độ CHỈ ĐỌC —
   * `contenteditable="false"` nên trình duyệt không đặt được con trỏ, lệnh thành
   * ra không làm gì và bấm mục lục chỉ thấy dòng sáng lên chứ trang không nhúc
   * nhích. `Element.scrollIntoView` thì không phụ thuộc con trỏ, lại tự đi qua
   * mọi lớp cuộn lồng nhau và hiểu đúng khung đang phóng to (`zoom`).
   */
  const goTo = useCallback(
    (pos: number) => {
      editor
        .chain()
        .focus()
        .setTextSelection(pos + 1)
        .run()

      const node = editor.view.nodeDOM(pos)
      if (!(node instanceof HTMLElement)) {
        // Không lấy được thẻ (tiêu đề chưa dựng xong DOM) thì thử cách của
        // ProseMirror — có còn hơn không.
        editor.commands.scrollIntoView()
        return
      }
      // Chờ hết khung hình hiện tại: `focus()` ở trên có thể khiến trình duyệt
      // tự cuộn về vùng soạn thảo, cuộn của mình phải chạy sau để không bị đè.
      requestAnimationFrame(() => {
        node.scrollIntoView({ behavior: 'smooth', block: 'center' })
      })
    },
    [editor],
  )

  return (
    <nav className={cn('min-h-full bg-muted/70 p-3', className)} aria-label="Mục lục văn bản">
      <div className="mb-3 flex items-center gap-2 px-2">
        <ListTree className="size-4 text-primary" />
        <p className="text-sm font-semibold text-navy dark:text-foreground">Mục lục tài liệu</p>
        {items.length > 0 && (
          <span className="ml-auto text-xs text-muted-foreground tabular-nums">
            {items.length} mục
          </span>
        )}
      </div>

      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed bg-background/60 px-3 py-4 text-xs leading-relaxed text-muted-foreground">
          Các tiêu đề bạn thêm vào văn bản sẽ hiện ở đây.
        </p>
      ) : (
        <div className="space-y-1">
          {items.map((item) => (
            <OutlineRow
              key={`${item.pos}-${item.text}`}
              item={item}
              active={item.pos === active}
              onSelect={goTo}
            />
          ))}
        </div>
      )}
    </nav>
  )
}

interface OutlineRowProps {
  item: OutlineItem
  active: boolean
  onSelect: (pos: number) => void
}

/**
 * Một dòng mục lục.
 *
 * Bọc `memo` vì văn bản dài có hàng trăm tiêu đề, mà mỗi lần con trỏ nhích là
 * cả danh sách được vẽ lại — chỉ có ĐÚNG HAI dòng thật sự đổi (dòng vừa rời đi
 * và dòng vừa tới).
 */
const OutlineRow = memo(function OutlineRow({ item, active, onSelect }: OutlineRowProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(item.pos)}
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
          className={cn('h-5 w-0.5 shrink-0 rounded-full bg-border', active && 'bg-primary')}
        />
      )}
      <span className="truncate">{item.text}</span>
    </button>
  )
})
