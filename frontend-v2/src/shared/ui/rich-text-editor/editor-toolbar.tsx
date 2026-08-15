import type { Editor } from '@tiptap/react'
import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Baseline,
  Bold,
  ChevronsUpDown,
  IndentDecrease,
  IndentIncrease,
  Italic,
  List,
  ListOrdered,
  Highlighter,
  Minus,
  Quote,
  Redo2,
  RemoveFormatting,
  Strikethrough,
  Subscript,
  Superscript,
  Underline,
  Undo2,
} from 'lucide-react'

import { DropdownMenuItem } from '@/shared/ui/dropdown-menu'
import { ImageMenu } from './image-menu'
import { LinkMenu } from './link-menu'
import { TableMenu } from './table-menu'
import {
  BLOCK_STYLES,
  FONT_FAMILIES,
  FONT_SIZES,
  HIGHLIGHT_COLORS,
  INHERIT,
  LINE_HEIGHTS,
  TEXT_COLORS,
  ZOOM_LEVELS,
} from './editor-options'
import {
  ColorSwatches,
  ToolbarButton,
  ToolbarDivider,
  ToolbarMenu,
  ToolbarSelect,
} from './toolbar-primitives'
import { useToolbarState } from './use-toolbar-state'

/**
 * Thanh công cụ soạn thảo, xếp theo thói quen dùng Word: hoàn tác → kiểu đoạn
 * và phông → định dạng chữ → canh lề, giãn dòng, thụt lề → danh sách → chèn.
 */
interface EditorToolbarProps {
  editor: Editor
  /** Mức phóng hiện tại, `1` = 100%. */
  zoom: number
  onZoomChange: (zoom: number) => void
}

export function EditorToolbar({ editor, zoom, onZoomChange }: EditorToolbarProps) {
  const state = useToolbarState(editor)
  // `focus()` trước mỗi lệnh để con trỏ quay lại đúng đoạn vừa chọn.
  const run = () => editor.chain().focus()

  function setBlockStyle(value: string) {
    if (value === 'paragraph') run().setParagraph().run()
    else run().toggleHeading({ level: Number(value) as 1 | 2 | 3 }).run()
  }

  return (
    <div className="flex flex-wrap items-center gap-0.5 border-b bg-muted/40 px-2 py-1.5">
      <ToolbarButton
        icon={Undo2}
        label="Hoàn tác (Ctrl+Z)"
        disabled={!state.canUndo}
        onClick={() => run().undo().run()}
      />
      <ToolbarButton
        icon={Redo2}
        label="Làm lại (Ctrl+Y)"
        disabled={!state.canRedo}
        onClick={() => run().redo().run()}
      />
      <ToolbarDivider />

      <ToolbarSelect
        label="Mức phóng"
        className="w-20"
        value={String(zoom)}
        onValueChange={(value) => onZoomChange(Number(value))}
        options={ZOOM_LEVELS.map((level) => ({
          label: `${Math.round(Number(level) * 100)}%`,
          value: level,
        }))}
      />
      <ToolbarDivider />

      <ToolbarSelect
        label="Kiểu đoạn"
        className="w-32"
        value={state.blockStyle}
        onValueChange={setBlockStyle}
        options={BLOCK_STYLES}
      />
      <ToolbarSelect
        label="Phông chữ"
        className="w-40"
        previewFont
        value={state.fontFamily}
        onValueChange={(value) =>
          value === INHERIT
            ? run().unsetFontFamily().run()
            : run().setFontFamily(value).run()
        }
        options={[{ label: 'Phông mặc định', value: INHERIT }, ...FONT_FAMILIES]}
      />
      <ToolbarSelect
        label="Cỡ chữ"
        className="w-22"
        value={state.fontSize}
        onValueChange={(value) =>
          value === INHERIT ? run().unsetFontSize().run() : run().setFontSize(value).run()
        }
        options={[
          { label: 'Cỡ gốc', value: INHERIT },
          ...FONT_SIZES.map((size) => ({ label: size.replace('pt', ''), value: size })),
        ]}
      />
      <ToolbarDivider />

      <ToolbarButton
        icon={Bold}
        label="In đậm (Ctrl+B)"
        active={state.bold}
        onClick={() => run().toggleBold().run()}
      />
      <ToolbarButton
        icon={Italic}
        label="In nghiêng (Ctrl+I)"
        active={state.italic}
        onClick={() => run().toggleItalic().run()}
      />
      <ToolbarButton
        icon={Underline}
        label="Gạch chân (Ctrl+U)"
        active={state.underline}
        onClick={() => run().toggleUnderline().run()}
      />
      <ToolbarButton
        icon={Strikethrough}
        label="Gạch ngang"
        active={state.strike}
        onClick={() => run().toggleStrike().run()}
      />
      <ToolbarButton
        icon={Superscript}
        label="Chỉ số trên (m²)"
        active={state.superscript}
        onClick={() => run().toggleSuperscript().run()}
      />
      <ToolbarButton
        icon={Subscript}
        label="Chỉ số dưới (H₂O)"
        active={state.subscript}
        onClick={() => run().toggleSubscript().run()}
      />

      <ToolbarMenu icon={Baseline} label="Màu chữ">
        <ColorSwatches
          colors={TEXT_COLORS}
          clearLabel="Màu mặc định"
          onPick={(color) => run().setColor(color).run()}
          onClear={() => run().unsetColor().run()}
        />
      </ToolbarMenu>
      <ToolbarMenu icon={Highlighter} label="Tô nền chữ">
        <ColorSwatches
          colors={HIGHLIGHT_COLORS}
          clearLabel="Bỏ tô nền"
          onPick={(color) => run().setBackgroundColor(color).run()}
          onClear={() => run().unsetBackgroundColor().run()}
        />
      </ToolbarMenu>
      <ToolbarButton
        icon={RemoveFormatting}
        label="Xóa định dạng"
        onClick={() => run().unsetAllMarks().clearNodes().run()}
      />
      <ToolbarDivider />

      <ToolbarButton
        icon={AlignLeft}
        label="Canh trái"
        active={state.alignLeft}
        onClick={() => run().setTextAlign('left').run()}
      />
      <ToolbarButton
        icon={AlignCenter}
        label="Canh giữa"
        active={state.alignCenter}
        onClick={() => run().setTextAlign('center').run()}
      />
      <ToolbarButton
        icon={AlignRight}
        label="Canh phải"
        active={state.alignRight}
        onClick={() => run().setTextAlign('right').run()}
      />
      <ToolbarButton
        icon={AlignJustify}
        label="Canh đều hai bên"
        active={state.alignJustify}
        onClick={() => run().setTextAlign('justify').run()}
      />

      <ToolbarMenu icon={ChevronsUpDown} label="Giãn dòng">
        {LINE_HEIGHTS.map((option) => (
          <DropdownMenuItem
            key={option.value}
            onSelect={() => run().setLineHeight(option.value).run()}
          >
            {option.label}
          </DropdownMenuItem>
        ))}
        <DropdownMenuItem onSelect={() => run().setLineHeight(null).run()}>
          Giãn dòng mặc định
        </DropdownMenuItem>
      </ToolbarMenu>
      <ToolbarButton
        icon={IndentDecrease}
        label="Giảm thụt lề"
        onClick={() => run().outdent().run()}
      />
      <ToolbarButton
        icon={IndentIncrease}
        label="Tăng thụt lề"
        onClick={() => run().indent().run()}
      />
      <ToolbarDivider />

      <ToolbarButton
        icon={List}
        label="Danh sách dấu chấm"
        active={state.bulletList}
        onClick={() => run().toggleBulletList().run()}
      />
      <ToolbarButton
        icon={ListOrdered}
        label="Danh sách đánh số"
        active={state.orderedList}
        onClick={() => run().toggleOrderedList().run()}
      />
      <ToolbarButton
        icon={Quote}
        label="Trích dẫn"
        active={state.blockquote}
        onClick={() => run().toggleBlockquote().run()}
      />
      <ToolbarDivider />

      <LinkMenu editor={editor} active={state.link} />
      <ImageMenu editor={editor} />
      <TableMenu editor={editor} inTable={state.inTable} />
      <ToolbarButton
        icon={Minus}
        label="Đường kẻ ngang"
        onClick={() => run().setHorizontalRule().run()}
      />


    </div>
  )
}
