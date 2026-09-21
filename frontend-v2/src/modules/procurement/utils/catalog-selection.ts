/** Nhãn dán cho giá trị đang lưu trên phiếu mà danh mục không có (bao-CR-372). */
export const OUT_OF_CATALOG_SUFFIX = ' (ngoài danh mục)'

/**
 * bao-CR-372 (port v2): giá trị đang lưu trên phiếu mà KHÔNG có trong danh mục vẫn phải
 * thấy được. `tab_product.item_group` là chuỗi tự do (không khóa ngoại), prod có 678/6877
 * sản phẩm mang phân loại ngoài danh mục — ô Select chỉ vẽ được giá trị khớp một option,
 * giá trị lạ bị nuốt thành "-- Phân loại --" trong khi popup Chi tiết dòng vẫn hiện chữ.
 *
 * Luật: khớp bỏ hoa/thường thì lấy ĐÚNG cách viết của danh mục; không khớp thì chèn thêm
 * một option mang nhãn "(ngoài danh mục)". Danh mục RỖNG nghĩa là chưa tải xong, không
 * phải "ngoài danh mục" — vẫn chèn option để chữ không biến mất nhưng KHÔNG dán nhãn,
 * kẻo lần vẽ đầu của mọi phiếu cũ đều gắn nhãn sai rồi mới tự sửa, người dùng kịp đọc.
 */
export function resolveCatalogSelection(
  value: string,
  options: { value: string; label: string }[],
): { selected: string; options: { value: string; label: string }[] } {
  const current = String(value ?? '').trim()
  if (!current) return { selected: '', options }
  const normalized = current.toLowerCase()
  const match = options.find((option) => option.value.trim().toLowerCase() === normalized)
  if (match) return { selected: match.value, options }
  const label = options.length > 0 ? `${current}${OUT_OF_CATALOG_SUFFIX}` : current
  return { selected: current, options: [{ value: current, label }, ...options] }
}
