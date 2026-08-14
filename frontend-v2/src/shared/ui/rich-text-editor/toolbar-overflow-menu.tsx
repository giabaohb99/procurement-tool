import { MoreHorizontal } from 'lucide-react'
import { Fragment } from 'react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import type { CollapsibleCommand } from './collapsible-toolbar-commands'

interface ToolbarOverflowMenuProps {
  /** Những lệnh không còn chỗ đứng ngoài thanh, theo đúng thứ tự gốc. */
  commands: CollapsibleCommand[]
}

/**
 * Menu "Thêm" — chứa đúng những lệnh vừa bị thu vào vì thanh công cụ hẹp.
 *
 * Không có lệnh nào bị thu thì không vẽ nút này: một nút "…" luôn hiện mà mở ra
 * trống rỗng còn khó hiểu hơn là không có.
 */
export function ToolbarOverflowMenu({ commands }: ToolbarOverflowMenuProps) {
  if (commands.length === 0) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title="Thêm lệnh"
          aria-label="Thêm lệnh"
          onMouseDown={(event) => event.preventDefault()}
        >
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        {commands.map((command, index) => (
          // Fragment chứ không bọc `div`: Radix dò các dòng menu bằng cây DOM,
          // thêm một lớp bọc là hỏng luôn việc di chuyển bằng phím mũi tên.
          <Fragment key={command.label}>
            {/* Vạch ngăn đúng chỗ đổi nhóm (canh lề ↔ phần còn lại). */}
            {index > 0 && commands[index - 1].tier !== command.tier && (
              <DropdownMenuSeparator />
            )}
            <DropdownMenuItem
              onSelect={command.run}
              className={cn(command.active && 'bg-accent')}
            >
              <command.icon className="size-4" />
              {command.label}
            </DropdownMenuItem>
          </Fragment>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
