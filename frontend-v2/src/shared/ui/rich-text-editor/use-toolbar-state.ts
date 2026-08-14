import { useEditorState, type Editor } from '@tiptap/react'

import { INHERIT } from './editor-options'

/**
 * Trạng thái các nút trên thanh công cụ (đang đậm? canh giữa? phông gì?).
 *
 * Dùng `useEditorState` thay vì đọc thẳng `editor.isActive(...)` khi vẽ: trình
 * soạn thảo giữ state bên ngoài React nên gõ phím không làm component vẽ lại —
 * không có hook này thì nút "In đậm" không bao giờ sáng lên.
 */
export function useToolbarState(editor: Editor) {
  return useEditorState({
    editor,
    selector: ({ editor: instance }) => ({
      bold: instance.isActive('bold'),
      italic: instance.isActive('italic'),
      underline: instance.isActive('underline'),
      strike: instance.isActive('strike'),
      subscript: instance.isActive('subscript'),
      superscript: instance.isActive('superscript'),
      link: instance.isActive('link'),
      // Địa chỉ của liên kết đang đứng — menu chuột phải cần để mở ra tab mới.
      linkHref: (instance.getAttributes('link').href as string | undefined) ?? '',
      // Có đang bôi đen chữ nào không: cắt / sao chép mà không chọn gì thì vô
      // nghĩa, phải làm mờ dòng lệnh đi.
      hasSelection: !instance.state.selection.empty,
      bulletList: instance.isActive('bulletList'),
      orderedList: instance.isActive('orderedList'),
      blockquote: instance.isActive('blockquote'),
      inTable: instance.isActive('table'),

      alignLeft: instance.isActive({ textAlign: 'left' }),
      alignCenter: instance.isActive({ textAlign: 'center' }),
      alignRight: instance.isActive({ textAlign: 'right' }),
      alignJustify: instance.isActive({ textAlign: 'justify' }),

      // `paragraph` là mặc định; ba mức tiêu đề trả về chính số mức để đổ
      // thẳng vào ô select.
      blockStyle: instance.isActive('heading', { level: 1 })
        ? '1'
        : instance.isActive('heading', { level: 2 })
          ? '2'
          : instance.isActive('heading', { level: 3 })
            ? '3'
            : 'paragraph',

      fontFamily: instance.getAttributes('textStyle').fontFamily ?? INHERIT,
      fontSize: instance.getAttributes('textStyle').fontSize ?? INHERIT,

      canUndo: instance.can().undo(),
      canRedo: instance.can().redo(),
    }),
  })
}

export type ToolbarState = ReturnType<typeof useToolbarState>
