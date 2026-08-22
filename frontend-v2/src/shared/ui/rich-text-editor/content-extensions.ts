import { Subscript } from '@tiptap/extension-subscript'
import { Superscript } from '@tiptap/extension-superscript'
import { TableKit } from '@tiptap/extension-table'
import { TextAlign } from '@tiptap/extension-text-align'
import { TextStyleKit } from '@tiptap/extension-text-style'
import StarterKit from '@tiptap/starter-kit'

import { ImageWithSize } from './image-size-extension'
import { KeepSelectionVisible } from './keep-selection-visible-extension'
import { ParagraphFormat } from './paragraph-format-extension'
import { SpreadsheetPaste } from './spreadsheet-paste-extension'
import {
  TableCellWithBackground,
  TableHeaderWithBackground,
} from './table-cell-background-extension'
import { TableWithColumnResizing } from './table-column-resizing-extension'
import { TableRowWithHeight } from './table-row-resizing-extension'

/**
 * LƯỢC ĐỒ NỘI DUNG dùng chung — mọi thứ trừ phần dàn trang giấy A4.
 *
 * Tách ra vì lược đồ quyết định **cái gì sống sót khi dán**: Tiptap vứt bỏ mọi
 * nút không có trong lược đồ. Ô soạn nào thiếu `TableKit` là dán một bảng vào
 * mất trắng cả bảng, thiếu `TextStyleKit` là mất phông và cỡ chữ — mà người dùng
 * không được báo gì cả, họ dán xong tưởng xong việc.
 *
 * Nên hai chỗ soạn thảo (trang soạn văn bản và ô rich text trong hộp thoại) phải
 * dùng CHUNG danh sách này. Chép tay hai bản là chuyện sớm muộn lệch nhau, và
 * lệch ở đây thì hỏng dữ liệu chứ không phải hỏng giao diện.
 *
 * `PaginationPlus` cố ý KHÔNG nằm ở đây: nó chia trang giấy, chỉ trang soạn thảo
 * toàn màn hình mới cần.
 */
export function contentExtensions() {
  return [
    // StarterKit v3 đã gồm sẵn Bold/Italic/Underline/Strike, tiêu đề, danh sách,
    // trích dẫn, đường kẻ ngang, LIÊN KẾT và lịch sử hoàn tác.
    StarterKit,
    // Phông, cỡ chữ, màu chữ, màu nền chữ.
    TextStyleKit,
    // Chỉ số trên / dưới — cần cho ký hiệu m², số mũ trong phụ lục.
    Subscript,
    Superscript,
    // Excel đính kèm cả bảng lẫn ảnh xem trước; ưu tiên bảng để dán vào các ô
    // đang bôi đen thay vì biến vùng Excel thành một tấm hình.
    SpreadsheetPaste,
    ImageWithSize.configure({ inline: false, allowBase64: true }),
    // Giữ vệt bôi đen khi bấm sang thanh công cụ — nếu không, mở một ô chọn là
    // vùng đã bôi biến mất trước mắt và người dùng tưởng bị mất chọn.
    KeepSelectionVisible,
    // Giãn dòng + thụt lề đầu dòng, xem `paragraph-format-extension.ts`.
    ParagraphFormat,
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
    // Tắt ô / ô tiêu đề / hàng mặc định để thay bằng bản có thêm MÀU NỀN
    // (`table-cell-background-extension.ts`) và KÉO CAO HÀNG
    // (`table-row-resizing-extension.ts`).
    // Tắt luôn cả bảng mặc định: phần kéo cột dựng sẵn làm bảng phình quá khổ
    // giấy, thay bằng bản kéo cột kiểu Word ở `table-column-resizing-extension.ts`.
    TableKit.configure({
      table: false,
      tableCell: false,
      tableHeader: false,
      tableRow: false,
    }),
    // `resizable: false` để tắt phần kéo cột dựng sẵn, nhưng vẫn giữ nguyên phần
    // còn lại của bảng (vùng chọn ô, `<colgroup>` giữ bề rộng cột).
    TableWithColumnResizing.configure({ resizable: false }),
    TableCellWithBackground,
    TableHeaderWithBackground,
    TableRowWithHeight,
  ]
}
