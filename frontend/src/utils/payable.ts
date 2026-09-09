/** Nhãn loại công nợ (`tab_payable.source_type`) — dùng chung mọi màn để thêm loại mới
 *  chỉ sửa MỘT chỗ. bao-CR-319 P5 thêm `import_cost` (nợ từng dòng chi phí lô hàng nhập khẩu). */
export const SOURCE_TYPE_LABELS: Record<string, string> = {
  goods: 'Hàng hóa',
  shipping: 'Vận chuyển',
  import_cost: 'Chi phí nhập khẩu',
}

export const SOURCE_TYPE_OPTIONS = Object.entries(SOURCE_TYPE_LABELS).map(([value, label]) => ({ value, label }))

/** Mã lạ / trống thì coi là hàng hóa — giữ đúng cách hiển thị cũ của các màn trước P5. */
export function sourceTypeLabel(code: string | undefined | null): string {
  return SOURCE_TYPE_LABELS[code || ''] || SOURCE_TYPE_LABELS.goods
}
