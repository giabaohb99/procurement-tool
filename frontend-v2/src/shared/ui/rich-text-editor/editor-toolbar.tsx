import type { Editor } from '@tiptap/react'
import {
  Baseline,
  Bold,
  ChevronsUpDown,
  Highlighter,
  Italic,
  List,
  ListOrdered,
  ListTree,
  PaintBucket,
  Redo2,
  Strikethrough,
  Underline,
  Undo2,
} from 'lucide-react'

import { DropdownMenuItem } from '@/shared/ui/dropdown-menu'
import {
  collapsibleCommands,
  COLLAPSIBLE_KEYS,
  type CollapsibleKey,
} from './collapsible-toolbar-commands'
import { ImageMenu } from './image-menu'
import { LinkMenu } from './link-menu'
import { TableBorderMenu } from './table-border-menu'
import { TableMenu } from './table-menu'
import { setCellBackground } from './table-commands'
import { ColorPalette } from './color-palette'
import { LINE_HEIGHTS } from './editor-options'
import { ToolbarStyleSelects } from './toolbar-style-selects'
import { ToolbarOverflowMenu } from './toolbar-overflow-menu'
import { ToolbarButton, ToolbarDivider, ToolbarMenu } from './toolbar-primitives'
import { useToolbarDensity } from './use-toolbar-density'
import { useToolbarState } from './use-toolbar-state'

/**
 * Thanh công cụ soạn thảo, xếp theo thói quen dùng Word: hoàn tác → kiểu đoạn
 * và phông → định dạng chữ → canh lề, giãn dòng, thụt lề → danh sách → chèn.
 *
 * Thanh TỰ CO theo bề rộng thật của nó (xem `use-toolbar-density.ts`): màn hẹp
 * thì những lệnh ít dùng lui vào menu "Thêm" ở cuối thanh để tất cả còn gọn một
 * hàng, màn rộng thì bày hết ra. Thà một hàng có menu "Thêm" còn hơn hai hàng
 * nút — trang soạn thảo ăn từng dòng chiều cao.
 */
interface EditorToolbarProps {
  editor: Editor
  /** Mức phóng hiện tại, `1` = 100%. */
  zoom: number
  onZoomChange: (zoom: number) => void
  /** Cột mục lục đang mở hay không; `undefined` = trang này không có mục lục. */
  outlineOpen?: boolean
  onToggleOutline?: () => void
}

export function EditorToolbar({
  editor,
  zoom,
  onZoomChange,
  outlineOpen,
  onToggleOutline,
}: EditorToolbarProps) {
  const state = useToolbarState(editor)
  const { ref, fits } = useToolbarDensity()
  const commands = collapsibleCommands(editor, state)
  // `focus()` trước mỗi lệnh để con trỏ quay lại đúng đoạn vừa chọn.
  const run = () => editor.chain().focus()

  /** Vẽ lệnh co giãn ĐÚNG CHỖ của nó trong nhóm, hoặc không vẽ gì nếu hết chỗ. */
  const inline = (key: CollapsibleKey) => {
    const command = commands[key]
    if (!fits(command.tier)) return null
    return (
      <ToolbarButton
        icon={command.icon}
        label={command.label}
        active={command.active}
        onClick={command.run}
      />
    )
  }

  const collapsed = COLLAPSIBLE_KEYS.map((key) => commands[key]).filter(
    (command) => !fits(command.tier),
  )

  return (
    <div ref={ref} className="flex flex-wrap items-center gap-0.5 border-b bg-muted/40 px-2 py-1.5">
      {/* Nút mục lục đứng đầu thanh, tách hẳn khỏi nhóm lệnh soạn thảo: nó đổi
          cách BÀY MÀN HÌNH chứ không đụng gì tới nội dung văn bản. */}
      {outlineOpen !== undefined && onToggleOutline && (
        <>
          <ToolbarButton
            icon={ListTree}
            label={outlineOpen ? 'Ẩn mục lục' : 'Hiện mục lục'}
            active={outlineOpen}
            onClick={onToggleOutline}
          />
          <ToolbarDivider />
        </>
      )}

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

      <ToolbarStyleSelects editor={editor} state={state} zoom={zoom} onZoomChange={onZoomChange} />
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
      {inline('superscript')}
      {inline('subscript')}

      <ToolbarMenu icon={Baseline} label="Màu chữ">
        <ColorPalette
          clearLabel="Màu mặc định"
          onPick={(color) => run().setColor(color).run()}
          onClear={() => run().unsetColor().run()}
        />
      </ToolbarMenu>
      <ToolbarMenu icon={Highlighter} label="Tô nền chữ">
        <ColorPalette
          clearLabel="Bỏ tô nền"
          onPick={(color) => run().setBackgroundColor(color).run()}
          onClear={() => run().unsetBackgroundColor().run()}
        />
      </ToolbarMenu>
      {inline('clearFormat')}
      <ToolbarDivider />

      {inline('alignLeft')}
      {inline('alignCenter')}
      {inline('alignRight')}
      {inline('alignJustify')}

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
      {inline('outdent')}
      {inline('indent')}
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
      {inline('blockquote')}
      <ToolbarDivider />

      <LinkMenu editor={editor} active={state.link} />
      <ImageMenu editor={editor} />
      <TableMenu editor={editor} />
      {/* Công cụ viền và màu nền chỉ có nghĩa khi con trỏ đang trong bảng. Các
          lệnh thay đổi cấu trúc bảng nằm ở menu chuột phải ngay tại ô. */}
      {state.inTable && (
        <>
          <TableBorderMenu editor={editor} />
          <ToolbarMenu icon={PaintBucket} label="Màu nền ô">
            <ColorPalette
              clearLabel="Bỏ màu nền"
              onPick={(color) => setCellBackground(editor, color)}
              onClear={() => setCellBackground(editor, null)}
            />
          </ToolbarMenu>
        </>
      )}
      {inline('horizontalRule')}

      {/* Menu "Thêm" luôn đứng cuối thanh — chỗ mắt tìm khi thấy thiếu lệnh. */}
      <ToolbarOverflowMenu commands={collapsed} />
    </div>
  )
}
