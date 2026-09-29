// Hàm thuần của mục «Pháp lý» (Tra cứu thị trường) — bảng duyệt hóa chất theo văn bản.

/** Ô tìm + ô chọn văn bản → tham số API. `list_code` chỉ gửi khi là số (backend đòi `int`). */
export function buildRegulationParams(search: string, listCode: string): Record<string, string> {
  const params: Record<string, string> = {}
  if (search.trim()) params.q = search.trim()
  if (/^\d+$/.test(listCode)) params.list_code = listCode
  return params
}

/**
 * Câu bảng rỗng phân biệt «chưa nạp danh mục» với «bộ lọc loại hết». Danh mục nạp bằng script
 * (dữ liệu bên thứ ba, không nằm trong repo) hoặc thêm tay ở mục «Cấu hình».
 */
export function resolveRegulationEmptyMessage(catalogTotal: number): string {
  return catalogTotal > 0
    ? 'Không có hóa chất nào khớp — thử đổi từ khóa hoặc chọn «Tất cả văn bản».'
    : 'Chưa có danh mục hóa chất theo văn bản — nhờ người phụ trách nạp danh mục hoặc thêm ở mục «Cấu hình».'
}
