import type { Editor } from '@tiptap/react'
import { Table as TableIcon } from 'lucide-react'
import { Fragment } from 'react'

import { DropdownMenuItem, DropdownMenuSeparator } from '@/shared/ui/dropdown-menu'
import { tableCommands } from './table-commands'
import { ToolbarMenu } from './toolbar-primitives'

interface TableMenuProps {
  editor: Editor
  /** Con trỏ đang nằm trong một bảng — các lệnh sửa bảng mới có nghĩa. */
  inTable: boolean
}

/** Nhóm lệnh về BẢNG: chèn mới, thêm/xóa hàng cột, gộp tách ô, đổ màu ô. */
export function TableMenu({ editor, inTable }: TableMenuProps) {
  return (
    <ToolbarMenu icon={TableIcon} label="Bảng">
      {tableCommands(editor).map((command) => (
        <Fragment key={command.label}>
          {command.separatorBefore && <DropdownMenuSeparator />}
          <DropdownMenuItem
            variant={command.destructive ? 'destructive' : 'default'}
            disabled={command.needsTable && !inTable}
            onSelect={command.run}
          >
            {command.label}
          </DropdownMenuItem>
        </Fragment>
      ))}

    </ToolbarMenu>
  )
}
