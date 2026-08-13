import { useEditorState, type Editor } from '@tiptap/react'

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
  1: 'pl-2',
  2: 'pl-5',
  3: 'pl-8',
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
  const items = useEditorState({
    editor,
    selector: ({ editor: instance }) => {
      const found: OutlineItem[] = []
      instance.state.doc.descendants((node, pos) => {
        if (node.type.name !== 'heading') return
        const text = node.textContent.trim()
        if (text) found.push({ level: Number(node.attrs.level) || 3, text, pos })
      })
      return found
    },
    // Gõ một chữ là tài liệu đổi, nhưng mục lục chỉ đổi khi tiêu đề đổi — so
    // sánh nội dung để khỏi vẽ lại khung này theo từng phím.
    equalityFn: (a, b) => JSON.stringify(a) === JSON.stringify(b),
  })

  /** `pos + 1` = vào bên TRONG tiêu đề, đặt đúng vào node thì con trỏ nằm ngoài. */
  function goTo(pos: number) {
    editor.chain().focus().setTextSelection(pos + 1).scrollIntoView().run()
  }

  return (
    // Cùng nền xám với vùng đặt trang giấy: để nền trắng thì khung mục lục
    // trông như một tờ giấy thứ hai nằm cạnh bản thảo.
    <nav className={cn('space-y-1 bg-muted p-3', className)} aria-label="Mục lục văn bản">
      <p className="px-2 pb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        Mục lục
      </p>

      {items.length === 0 ? (
        <p className="px-2 text-xs text-muted-foreground italic">
          Các tiêu đề bạn thêm vào văn bản sẽ hiện ở đây.
        </p>
      ) : (
        items.map((item) => (
          <button
            key={`${item.pos}-${item.text}`}
            type="button"
            onClick={() => goTo(item.pos)}
            title={item.text}
            className={cn(
              'block w-full truncate rounded-md py-1.5 pr-2 text-left text-sm text-muted-foreground',
              'hover:bg-accent hover:text-foreground',
              LEVEL_INDENT[item.level] ?? LEVEL_INDENT[3],
              item.level === 1 && 'font-medium text-foreground',
            )}
          >
            {item.text}
          </button>
        ))
      )}
    </nav>
  )
}
