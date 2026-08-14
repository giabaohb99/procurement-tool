import type { Editor } from '@tiptap/react'
import {
  Bold,
  ClipboardPaste,
  ClipboardType,
  Copy,
  Italic,
  Link2Off,
  RemoveFormatting,
  Scissors,
  SquareArrowOutUpRight,
  Table as TableIcon,
  Underline,
} from 'lucide-react'
import { Fragment, type ReactNode } from 'react'

import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuLabel,
  ContextMenuSeparator,
  ContextMenuShortcut,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from '@/shared/ui/context-menu'
import { cn } from '@/shared/utils/cn'
import { ColorPalette } from './color-palette'
import { copySelection, cutSelection, pasteFromClipboard } from './editor-clipboard'
import { setCellBackground, tableCommands } from './table-commands'
import { useToolbarState } from './use-toolbar-state'

interface EditorContextMenuProps {
  editor: Editor
  children: ReactNode
}

/**
 * MENU CHUỘT PHẢI trong trang giấy, theo đúng thứ tự người dùng Word đã quen:
 * cắt / chép / dán → định dạng nhanh → liên kết → bảng.
 *
 * Có menu này thì mấy việc hay làm không phải chạy lên thanh công cụ ở tận đầu
 * trang — soạn tới cuối trang thứ ba mà đổi một chữ sang in đậm cũng phải kéo
 * mắt lên đỉnh màn hình là mệt.
 *
 * Đổi lại, menu gốc của trình duyệt (gợi ý chính tả) không còn — vì vậy các
 * lệnh trong đây phải phủ được đúng những việc thường dùng.
 */
export function EditorContextMenu({ editor, children }: EditorContextMenuProps) {
  const state = useToolbarState(editor)
  const run = () => editor.chain().focus()

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>{children}</ContextMenuTrigger>

      {/* Bề ngang TỰ CO theo nội dung, chỉ chặn mức tối thiểu: bảng màu rộng
          hơn một dòng lệnh, đóng khung cứng là nó thò hẳn ra ngoài mép menu. */}
      <ContextMenuContent className="w-auto min-w-60">
        <ContextMenuItem disabled={!state.hasSelection} onSelect={() => cutSelection(editor)}>
          <Scissors className="size-4" />
          Cắt
          <ContextMenuShortcut>Ctrl+X</ContextMenuShortcut>
        </ContextMenuItem>
        <ContextMenuItem disabled={!state.hasSelection} onSelect={() => copySelection(editor)}>
          <Copy className="size-4" />
          Sao chép
          <ContextMenuShortcut>Ctrl+C</ContextMenuShortcut>
        </ContextMenuItem>
        <ContextMenuItem onSelect={() => pasteFromClipboard(editor)}>
          <ClipboardPaste className="size-4" />
          Dán
          <ContextMenuShortcut>Ctrl+V</ContextMenuShortcut>
        </ContextMenuItem>
        <ContextMenuItem onSelect={() => pasteFromClipboard(editor, { plain: true })}>
          <ClipboardType className="size-4" />
          Dán chữ thuần
          <ContextMenuShortcut>Ctrl+⇧+V</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuSeparator />

        <ContextMenuItem
          className={cn(state.bold && 'bg-accent')}
          onSelect={() => run().toggleBold().run()}
        >
          <Bold className="size-4" />
          In đậm
          <ContextMenuShortcut>Ctrl+B</ContextMenuShortcut>
        </ContextMenuItem>
        <ContextMenuItem
          className={cn(state.italic && 'bg-accent')}
          onSelect={() => run().toggleItalic().run()}
        >
          <Italic className="size-4" />
          In nghiêng
          <ContextMenuShortcut>Ctrl+I</ContextMenuShortcut>
        </ContextMenuItem>
        <ContextMenuItem
          className={cn(state.underline && 'bg-accent')}
          onSelect={() => run().toggleUnderline().run()}
        >
          <Underline className="size-4" />
          Gạch chân
          <ContextMenuShortcut>Ctrl+U</ContextMenuShortcut>
        </ContextMenuItem>
        <ContextMenuItem onSelect={() => run().unsetAllMarks().clearNodes().run()}>
          <RemoveFormatting className="size-4" />
          Xóa định dạng
        </ContextMenuItem>

        {/* Hai lệnh liên kết chỉ hiện khi con trỏ đang đứng trong một liên kết —
            bày sẵn lúc không có gì để mở / để gỡ chỉ tổ dài menu. */}
        {state.link && (
          <>
            <ContextMenuSeparator />
            <ContextMenuItem
              disabled={!state.linkHref}
              onSelect={() => window.open(state.linkHref, '_blank', 'noopener,noreferrer')}
            >
              <SquareArrowOutUpRight className="size-4" />
              Mở liên kết
            </ContextMenuItem>
            <ContextMenuItem
              onSelect={() => run().extendMarkRange('link').unsetLink().run()}
            >
              <Link2Off className="size-4" />
              Gỡ liên kết
            </ContextMenuItem>
          </>
        )}

        <ContextMenuSeparator />

        <ContextMenuSub>
          <ContextMenuSubTrigger>
            <TableIcon className="size-4" />
            Bảng
          </ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-56">
            {tableCommands(editor).map((command) => (
              <Fragment key={command.label}>
                {command.separatorBefore && <ContextMenuSeparator />}
                <ContextMenuItem
                  variant={command.destructive ? 'destructive' : 'default'}
                  disabled={command.needsTable && !state.inTable}
                  onSelect={command.run}
                >
                  {command.label}
                </ContextMenuItem>
              </Fragment>
            ))}

          </ContextMenuSubContent>
        </ContextMenuSub>

        {/* Bảng màu nằm THẲNG trong menu chính, không nhét vào menu con "Bảng":
            kẻ xong bảng thì tô màu là việc bấm liên tục, mỗi lần phải rê qua
            một lớp menu nữa là mất thêm một nhịp. Bôi đen cả hàng / cả cột rồi
            đổ màu là ăn hết một lượt — lệnh đổi thuộc tính ô áp cho mọi ô đang
            chọn. */}
        {state.inTable && (
          <>
            <ContextMenuSeparator />
            <ContextMenuLabel className="text-muted-foreground">Màu nền ô</ContextMenuLabel>
            <ColorPalette
              clearLabel="Bỏ màu nền"
              onPick={(color) => setCellBackground(editor, color)}
              onClear={() => setCellBackground(editor, null)}
            />
          </>
        )}
      </ContextMenuContent>
    </ContextMenu>
  )
}
