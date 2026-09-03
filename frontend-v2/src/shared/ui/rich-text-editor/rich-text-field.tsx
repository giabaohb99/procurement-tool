import { EditorContent, useEditor, useEditorState, type Editor } from '@tiptap/react'
import { useEffect, useImperativeHandle, useRef } from 'react'

import { cn } from '@/shared/utils/cn'
import { contentExtensions } from './content-extensions'
import { RichTextFieldToolbar } from './rich-text-field-toolbar'

/**
 * Cần chọc vào trình soạn thảo từ ngoài (nút emoji của diễn đàn chèn chữ vào
 * đúng chỗ con trỏ — CR-261) thì đi qua handle này, KHÔNG lộ cả `Editor` ra —
 * lộ editor là mời gọi code ngoài gọi thẳng API tiptap rồi khó đổi ruột.
 */
export interface RichTextFieldHandle {
  insertText: (text: string) => void
}

interface RichTextFieldProps {
  /**
   * HTML ban đầu. Như `RichTextEditor`, chỉ đọc MỘT LẦN lúc dựng — bám theo prop
   * thì mỗi lần gõ xong nội dung lại đổ ngược vào và con trỏ nhảy về đầu. Cần
   * nạp lại giá trị khác thì đổi `key` của component.
   */
  defaultValue: string
  onChange: (html: string) => void
  /** Chữ gợi ý khi ô còn rỗng. */
  placeholder?: string
  /**
   * Thanh công cụ nằm trên hay dưới vùng gõ. Đặt `bottom` cho những ô nhỏ nằm
   * lẫn trong một danh sách thuộc tính (ô mô tả của công việc): thanh nút đứng
   * trên đầu thì mắt đọc phải vượt qua nó mới tới nội dung.
   */
  toolbarPosition?: 'top' | 'bottom'
  /** Đặt con trỏ vào CUỐI nội dung ngay khi dựng — cho ô chỉ hiện lúc bấm sửa. */
  autoFocus?: boolean
  /** Nhận `RichTextFieldHandle` để chèn chữ từ ngoài (xem chú thích ở interface). */
  handleRef?: React.Ref<RichTextFieldHandle>
  className?: string
}

/**
 * Ô nhập RICH TEXT gọn, dùng trong hộp thoại và biểu mẫu.
 *
 * Khác `RichTextEditor` ở chỗ **không phải trang giấy**: không A4, không thước
 * kẻ, không chia trang, không cột mục lục — chỉ một khung cuộn được với thanh
 * công cụ tối thiểu. Nhét `RichTextEditor` vào hộp thoại rộng 672px là nhét một
 * tờ giấy A4 (794px) vào chỗ hẹp hơn nó.
 *
 * ⚠️ **Vì sao những ô lưu HTML không được dùng `<Textarea>`.** Ô kiểu này lưu
 * vào cột `content_html` rồi được vẽ lại bằng `dangerouslySetInnerHTML`. Dán
 * nội dung đã định dạng vào một `<textarea>` thì trình duyệt chỉ giữ lại CHỮ
 * TRƠN, và hậu quả không dừng ở chuyện mất đậm/nghiêng:
 *
 * - **mất luôn ngắt đoạn** — xuống dòng trong chữ trơn không phải là `<p>`, nên
 *   ba đoạn dán vào ra một khối chữ liền mạch lúc hiển thị;
 * - **mất bảng** — trích một điều khoản có bảng phụ cấp thì bảng bốc hơi;
 * - **`<` và `&` trong bài bị đọc thành thẻ** — gõ "a < b" là hỏng phần hiển thị
 *   từ chỗ đó trở đi.
 *
 * Lược đồ nội dung dùng CHUNG với trình soạn thảo chính (`contentExtensions`),
 * nên thứ dán được ở trang soạn thảo thì dán được ở đây, không lệch.
 */
export function RichTextField({
  defaultValue,
  onChange,
  placeholder,
  toolbarPosition = 'top',
  autoFocus = false,
  handleRef,
  className,
}: RichTextFieldProps) {
  //  `onUpdate` của Tiptap đóng băng closure từ lần dựng đầu — giữ hàm mới nhất
  //  trong ref. Gán trong `useEffect` chứ không gán thẳng lúc vẽ: sờ vào
  //  `ref.current` giữa lúc render là thứ `react-hooks` chặn, mà `onUpdate` chỉ
  //  chạy khi người dùng gõ nên lúc đó effect đã chạy xong từ lâu.
  const changeRef = useRef(onChange)
  useEffect(() => {
    changeRef.current = onChange
  }, [onChange])

  const editor = useEditor({
    extensions: contentExtensions(),
    content: defaultValue,
    autofocus: autoFocus ? 'end' : false,
    onUpdate: ({ editor: instance }) => changeRef.current(instance.getHTML()),
    editorProps: {
      //  `doc-rich-field` khai ở `index.css`, dùng CHUNG bộ luật hiển thị với
      //  khối xem trước — soạn xong bấm xem trước phải ra đúng một hình.
      attributes: { class: 'doc-rich-field' },
    },
  })

  //  Phải đứng TRƯỚC `return null` — hook không được nằm sau một lối ra sớm.
  //  `focus()` trước khi chèn: bấm nút ngoài làm editor mất focus, không kéo
  //  lại thì chữ rơi vào vị trí con trỏ đã chết.
  useImperativeHandle(
    handleRef,
    () => ({
      insertText: (text: string) => {
        editor?.chain().focus().insertContent(text).run()
      },
    }),
    [editor],
  )

  if (!editor) return null

  return (
    <ComposerBody
      editor={editor}
      placeholder={placeholder}
      toolbarPosition={toolbarPosition}
      className={className}
    />
  )
}

/**
 * Tách phần thân ra vì `useEditorState` cần một `Editor` chắc chắn có thật, mà
 * `useEditor` thì trả `null` ở lần vẽ đầu — không thể gọi hook sau một câu
 * `return null`.
 */
function ComposerBody({
  editor,
  placeholder,
  toolbarPosition,
  className,
}: {
  editor: Editor
  placeholder?: string
  toolbarPosition: 'top' | 'bottom'
  className?: string
}) {
  //  Chỉ theo dõi ĐÚNG cờ rỗng ở đây; trạng thái của từng nút nằm trong thanh
  //  công cụ. Trình soạn thảo giữ state ngoài React nên không đi qua
  //  `useEditorState` thì chữ gợi ý không bao giờ tắt.
  const rong = useEditorState({ editor, selector: ({ editor: e }) => e.isEmpty })

  const toolbar = (
    <RichTextFieldToolbar
      editor={editor}
      className={toolbarPosition === 'bottom' ? 'border-t' : 'border-b'}
    />
  )

  return (
    <div className={cn('overflow-hidden rounded-md border bg-card', className)}>
      {toolbarPosition === 'top' && toolbar}

      {/*  Chữ gợi ý vẽ đè bằng React thay vì kéo thêm `@tiptap/extension-
           placeholder` cho đúng một dòng chữ. `pointer-events-none` để bấm vào
           chỗ chữ gợi ý vẫn là bấm vào vùng gõ bên dưới. */}
      <div className="relative">
        {rong && placeholder && (
          <p className="pointer-events-none absolute top-2.5 left-3 text-sm text-muted-foreground">
            {placeholder}
          </p>
        )}
        <EditorContent editor={editor} />
      </div>

      {toolbarPosition === 'bottom' && toolbar}
    </div>
  )
}

