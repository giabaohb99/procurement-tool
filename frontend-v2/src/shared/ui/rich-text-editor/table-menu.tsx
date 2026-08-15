import type { Editor } from '@tiptap/react'
import { Table as TableIcon } from 'lucide-react'

import { DropdownMenuItem, DropdownMenuSeparator } from '@/shared/ui/dropdown-menu'
import { ToolbarMenu } from './toolbar-primitives'

interface TableMenuProps {
  editor: Editor
  /** Con trỏ đang nằm trong một bảng — các lệnh sửa bảng mới có nghĩa. */
  inTable: boolean
}

/** Nhóm lệnh về BẢNG: chèn mới, thêm/xóa hàng cột, gộp tách ô. */
export function TableMenu({ editor, inTable }: TableMenuProps) {
  const run = () => editor.chain().focus()

  return (
    <ToolbarMenu icon={TableIcon} label="Bảng">
      <DropdownMenuItem
        onSelect={() => run().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
      >
        Chèn bảng 3×3
      </DropdownMenuItem>

      <DropdownMenuSeparator />

      <DropdownMenuItem disabled={!inTable} onSelect={() => run().addRowAfter().run()}>
        Thêm hàng bên dưới
      </DropdownMenuItem>
      <DropdownMenuItem disabled={!inTable} onSelect={() => run().addColumnAfter().run()}>
        Thêm cột bên phải
      </DropdownMenuItem>
      <DropdownMenuItem disabled={!inTable} onSelect={() => run().deleteRow().run()}>
        Xóa hàng
      </DropdownMenuItem>
      <DropdownMenuItem disabled={!inTable} onSelect={() => run().deleteColumn().run()}>
        Xóa cột
      </DropdownMenuItem>
      <DropdownMenuItem disabled={!inTable} onSelect={() => run().mergeOrSplit().run()}>
        Gộp / tách ô
      </DropdownMenuItem>

      <DropdownMenuSeparator />

      <DropdownMenuItem
        variant="destructive"
        disabled={!inTable}
        onSelect={() => run().deleteTable().run()}
      >
        Xóa bảng
      </DropdownMenuItem>
    </ToolbarMenu>
  )
}
