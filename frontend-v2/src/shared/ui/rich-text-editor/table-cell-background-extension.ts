import { TableCell, TableHeader } from '@tiptap/extension-table'

/**
 * Thêm MÀU NỀN cho ô bảng.
 *
 * Tiptap dựng sẵn ô bảng chỉ với `colspan`, `rowspan`, `colwidth` — không có
 * chỗ nào giữ màu, nên phải nới thêm một thuộc tính. Màu ghi thẳng vào
 * `style` của ô để dán sang Word hay in ra vẫn còn.
 *
 * Đổ màu chạy bằng `setCellAttribute`, mà lệnh đó áp cho MỌI ô đang chọn — nên
 * bôi đen cả hàng hay cả cột rồi đổ màu là ăn hết một lượt, đúng như Word.
 */
function withBackgroundColor<T extends typeof TableCell | typeof TableHeader>(cell: T) {
  return cell.extend({
    addAttributes() {
      return {
        ...this.parent?.(),
        backgroundColor: {
          default: null,
          parseHTML: (element) => element.style.backgroundColor || null,
          renderHTML: (attributes) =>
            attributes.backgroundColor
              ? { style: `background-color: ${attributes.backgroundColor}` }
              : {},
        },
      }
    },
  })
}

export const TableCellWithBackground = withBackgroundColor(TableCell)
export const TableHeaderWithBackground = withBackgroundColor(TableHeader)
