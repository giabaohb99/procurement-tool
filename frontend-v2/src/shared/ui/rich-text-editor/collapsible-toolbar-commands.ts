import type { Editor } from '@tiptap/react'
import type { LucideIcon } from 'lucide-react'
import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  IndentDecrease,
  IndentIncrease,
  Minus,
  Quote,
  RemoveFormatting,
  Subscript,
  Superscript,
} from 'lucide-react'

import type { ToolbarTier } from './use-toolbar-density'
import type { ToolbarState } from './use-toolbar-state'

/**
 * Những lệnh CÓ THỂ THU GỌN của thanh công cụ.
 *
 * Khai một lần ở đây rồi vẽ ở hai chỗ — nút ngoài thanh và dòng trong menu
 * "Thêm" — để không có chuyện sửa lệnh ở nút mà quên sửa trong menu.
 */
export interface CollapsibleCommand {
  icon: LucideIcon
  label: string
  tier: ToolbarTier
  active?: boolean
  run: () => void
}

/** Thứ tự này cũng là thứ tự các dòng trong menu "Thêm". */
export const COLLAPSIBLE_KEYS = [
  'alignLeft',
  'alignCenter',
  'alignRight',
  'alignJustify',
  'superscript',
  'subscript',
  'clearFormat',
  'outdent',
  'indent',
  'blockquote',
  'horizontalRule',
] as const

export type CollapsibleKey = (typeof COLLAPSIBLE_KEYS)[number]

export function collapsibleCommands(
  editor: Editor,
  state: ToolbarState,
): Record<CollapsibleKey, CollapsibleCommand> {
  // `focus()` trước mỗi lệnh để con trỏ quay lại đúng đoạn vừa chọn.
  const run = () => editor.chain().focus()

  return {
    alignLeft: {
      icon: AlignLeft,
      label: 'Canh trái',
      tier: 'medium',
      active: state.alignLeft,
      run: () => run().setTextAlign('left').run(),
    },
    alignCenter: {
      icon: AlignCenter,
      label: 'Canh giữa',
      tier: 'medium',
      active: state.alignCenter,
      run: () => run().setTextAlign('center').run(),
    },
    alignRight: {
      icon: AlignRight,
      label: 'Canh phải',
      tier: 'medium',
      active: state.alignRight,
      run: () => run().setTextAlign('right').run(),
    },
    alignJustify: {
      icon: AlignJustify,
      label: 'Canh đều hai bên',
      tier: 'medium',
      active: state.alignJustify,
      run: () => run().setTextAlign('justify').run(),
    },

    superscript: {
      icon: Superscript,
      label: 'Chỉ số trên (m²)',
      tier: 'wide',
      active: state.superscript,
      run: () => run().toggleSuperscript().run(),
    },
    subscript: {
      icon: Subscript,
      label: 'Chỉ số dưới (H₂O)',
      tier: 'wide',
      active: state.subscript,
      run: () => run().toggleSubscript().run(),
    },
    clearFormat: {
      icon: RemoveFormatting,
      label: 'Xóa định dạng',
      tier: 'wide',
      run: () => run().unsetAllMarks().clearNodes().run(),
    },
    outdent: {
      icon: IndentDecrease,
      label: 'Giảm thụt lề',
      tier: 'wide',
      run: () => run().outdent().run(),
    },
    indent: {
      icon: IndentIncrease,
      label: 'Tăng thụt lề',
      tier: 'wide',
      run: () => run().indent().run(),
    },
    blockquote: {
      icon: Quote,
      label: 'Trích dẫn',
      tier: 'wide',
      active: state.blockquote,
      run: () => run().toggleBlockquote().run(),
    },
    horizontalRule: {
      icon: Minus,
      label: 'Đường kẻ ngang',
      tier: 'wide',
      run: () => run().setHorizontalRule().run(),
    },
  }
}
