import { useEditorState, type Editor } from '@tiptap/react'
import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Bold,
  Eraser,
  Italic,
  List,
  ListOrdered,
  Quote,
  Strikethrough,
  Underline,
} from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import { LinkMenu } from './link-menu'
import { ToolbarButton, ToolbarDivider } from './toolbar-primitives'

/**
 * Thanh công cụ của `RichTextField` — tách khỏi tệp kia để mỗi tệp còn dưới
 * 200 dòng và để chỗ nào cần thanh công cụ riêng thì mượn lại được.
 *
 * ⚠️ Bắt buộc đi qua `useEditorState`. Trình soạn thảo giữ state BÊN NGOÀI
 * React nên gõ phím / di con trỏ không làm component vẽ lại — đọc thẳng
 * `editor.isActive('bold')` lúc vẽ thì nút «In đậm» không bao giờ sáng lên.
 * Cùng lý do với `use-toolbar-state.ts`.
 */
export function RichTextFieldToolbar({
  editor,
  className,
}: {
  editor: Editor
  className?: string
}) {
  const status = useEditorState({
    editor,
    selector: ({ editor: instance }) => ({
      bold: instance.isActive('bold'),
      italic: instance.isActive('italic'),
      underline: instance.isActive('underline'),
      strike: instance.isActive('strike'),
      bulletList: instance.isActive('bulletList'),
      orderedList: instance.isActive('orderedList'),
      blockquote: instance.isActive('blockquote'),
      link: instance.isActive('link'),
      alignLeft: instance.isActive({ textAlign: 'left' }),
      alignCenter: instance.isActive({ textAlign: 'center' }),
      alignRight: instance.isActive({ textAlign: 'right' }),
      alignJustify: instance.isActive({ textAlign: 'justify' }),
    }),
  })

  const align = [
    { value: 'left', icon: AlignLeft, nhan: 'Canh trái', isOn: status.alignLeft },
    { value: 'center', icon: AlignCenter, nhan: 'Canh giữa', isOn: status.alignCenter },
    { value: 'right', icon: AlignRight, nhan: 'Canh phải', isOn: status.alignRight },
    { value: 'justify', icon: AlignJustify, nhan: 'Canh đều', isOn: status.alignJustify },
  ] as const

  return (
    <div className={cn('flex flex-wrap items-center gap-0.5 bg-muted/40 px-1 py-1', className)}>
      <ToolbarButton
        icon={Bold}
        label="In đậm"
        active={status.bold}
        onClick={() => editor.chain().focus().toggleBold().run()}
      />
      <ToolbarButton
        icon={Italic}
        label="In nghiêng"
        active={status.italic}
        onClick={() => editor.chain().focus().toggleItalic().run()}
      />
      <ToolbarButton
        icon={Underline}
        label="Gạch chân"
        active={status.underline}
        onClick={() => editor.chain().focus().toggleUnderline().run()}
      />
      <ToolbarButton
        icon={Strikethrough}
        label="Gạch ngang"
        active={status.strike}
        onClick={() => editor.chain().focus().toggleStrike().run()}
      />

      <ToolbarDivider />

      <ToolbarButton
        icon={List}
        label="Danh sách dấu chấm"
        active={status.bulletList}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      />
      <ToolbarButton
        icon={ListOrdered}
        label="Danh sách đánh số"
        active={status.orderedList}
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
      />
      <ToolbarButton
        icon={Quote}
        label="Trích dẫn"
        active={status.blockquote}
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
      />
      <LinkMenu editor={editor} active={status.link} />

      <ToolbarDivider />

      {align.map((muc) => (
        <ToolbarButton
          key={muc.value}
          icon={muc.icon}
          label={muc.nhan}
          active={muc.isOn}
          onClick={() => editor.chain().focus().setTextAlign(muc.value).run()}
        />
      ))}

      <ToolbarDivider />

      {/*  Dán từ Word hay từ chính bản gốc thường kéo theo phông, cỡ chữ, màu
           nền của nguồn. Có nút gỡ định dạng thì không phải xóa đi gõ lại. */}
      <ToolbarButton
        icon={Eraser}
        label="Xóa định dạng"
        onClick={() => editor.chain().focus().unsetAllMarks().clearNodes().run()}
      />
    </div>
  )
}
