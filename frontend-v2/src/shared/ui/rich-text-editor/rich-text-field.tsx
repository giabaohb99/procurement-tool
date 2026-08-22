import { EditorContent, useEditor, useEditorState, type Editor } from '@tiptap/react'
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
  Underline,
} from 'lucide-react'
import { useEffect, useRef } from 'react'

import { cn } from '@/shared/utils/cn'
import { contentExtensions } from './content-extensions'
import { ToolbarButton, ToolbarDivider } from './toolbar-primitives'

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
    onUpdate: ({ editor: instance }) => changeRef.current(instance.getHTML()),
    editorProps: {
      //  `doc-rich-field` khai ở `index.css`, dùng CHUNG bộ luật hiển thị với
      //  khối xem trước — soạn xong bấm xem trước phải ra đúng một hình.
      attributes: { class: 'doc-rich-field' },
    },
  })

  if (!editor) return null

  return <ThanOSoan editor={editor} placeholder={placeholder} className={className} />
}

/**
 * Tách phần thân ra vì `useEditorState` cần một `Editor` chắc chắn có thật, mà
 * `useEditor` thì trả `null` ở lần vẽ đầu — không thể gọi hook sau một câu
 * `return null`.
 */
function ThanOSoan({
  editor,
  placeholder,
  className,
}: {
  editor: Editor
  placeholder?: string
  className?: string
}) {
  //  ⚠️ Bắt buộc đi qua `useEditorState`. Trình soạn thảo giữ state BÊN NGOÀI
  //  React nên gõ phím / di con trỏ không làm component vẽ lại — đọc thẳng
  //  `editor.isActive('bold')` lúc vẽ thì nút "In đậm" không bao giờ sáng lên,
  //  và chữ gợi ý không bao giờ tắt. Cùng lý do với `use-toolbar-state.ts`.
  const trangThai = useEditorState({
    editor,
    selector: ({ editor: instance }) => ({
      rong: instance.isEmpty,
      bold: instance.isActive('bold'),
      italic: instance.isActive('italic'),
      underline: instance.isActive('underline'),
      bulletList: instance.isActive('bulletList'),
      orderedList: instance.isActive('orderedList'),
      alignLeft: instance.isActive({ textAlign: 'left' }),
      alignCenter: instance.isActive({ textAlign: 'center' }),
      alignRight: instance.isActive({ textAlign: 'right' }),
      alignJustify: instance.isActive({ textAlign: 'justify' }),
    }),
  })

  const canhLe = [
    { giaTri: 'left', icon: AlignLeft, nhan: 'Canh trái', dangBat: trangThai.alignLeft },
    { giaTri: 'center', icon: AlignCenter, nhan: 'Canh giữa', dangBat: trangThai.alignCenter },
    { giaTri: 'right', icon: AlignRight, nhan: 'Canh phải', dangBat: trangThai.alignRight },
    { giaTri: 'justify', icon: AlignJustify, nhan: 'Canh đều', dangBat: trangThai.alignJustify },
  ] as const

  return (
    <div className={cn('overflow-hidden rounded-md border bg-card', className)}>
      <div className="flex flex-wrap items-center gap-0.5 border-b bg-muted/40 px-1 py-1">
        <ToolbarButton
          icon={Bold}
          label="In đậm"
          active={trangThai.bold}
          onClick={() => editor.chain().focus().toggleBold().run()}
        />
        <ToolbarButton
          icon={Italic}
          label="In nghiêng"
          active={trangThai.italic}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        />
        <ToolbarButton
          icon={Underline}
          label="Gạch chân"
          active={trangThai.underline}
          onClick={() => editor.chain().focus().toggleUnderline().run()}
        />

        <ToolbarDivider />

        <ToolbarButton
          icon={List}
          label="Danh sách dấu chấm"
          active={trangThai.bulletList}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        />
        <ToolbarButton
          icon={ListOrdered}
          label="Danh sách đánh số"
          active={trangThai.orderedList}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        />

        <ToolbarDivider />

        {canhLe.map((muc) => (
          <ToolbarButton
            key={muc.giaTri}
            icon={muc.icon}
            label={muc.nhan}
            active={muc.dangBat}
            onClick={() => editor.chain().focus().setTextAlign(muc.giaTri).run()}
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

      {/*  Chữ gợi ý vẽ đè bằng React thay vì kéo thêm `@tiptap/extension-
           placeholder` cho đúng một dòng chữ. `pointer-events-none` để bấm vào
           chỗ chữ gợi ý vẫn là bấm vào vùng gõ bên dưới. */}
      <div className="relative">
        {trangThai.rong && placeholder && (
          <p className="pointer-events-none absolute top-2.5 left-3 text-sm text-muted-foreground">
            {placeholder}
          </p>
        )}
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}
