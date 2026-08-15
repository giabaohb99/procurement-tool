import { TableCell, TableHeader } from '@tiptap/extension-table'

/**
 * Thêm MÀU NỀN và VIỀN TỪNG CẠNH cho ô bảng.
 *
 * Tiptap dựng sẵn ô bảng chỉ với `colspan`, `rowspan`, `colwidth` — không có
 * chỗ nào giữ màu hay kiểu viền riêng, nên phải nới thêm thuộc tính. Tất cả
 * được ghi thẳng vào `style` của ô để dán sang Word hay in ra vẫn còn.
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
        borderTop: cellBorderAttribute('border-top'),
        borderRight: cellBorderAttribute('border-right'),
        borderBottom: cellBorderAttribute('border-bottom'),
        borderLeft: cellBorderAttribute('border-left'),
      }
    },
  })
}

/** Một cạnh viền lưu bằng đúng cú pháp CSS, ví dụ `2px dashed #1e293b`. */
function cellBorderAttribute(property: string) {
  const domProperty = property.replace(/-([a-z])/g, (_, letter: string) => letter.toUpperCase()) as
    'borderTop' | 'borderRight' | 'borderBottom' | 'borderLeft'

  return {
    default: null,
    parseHTML: (element: HTMLElement) => element.style[domProperty] || null,
    renderHTML: (attributes: Record<string, string | null>) => {
      const value = attributes[domProperty]
      return value ? { style: `${property}: ${value}` } : {}
    },
  }
}

export const TableCellWithBackground = withBackgroundColor(TableCell)
export const TableHeaderWithBackground = withBackgroundColor(TableHeader)
