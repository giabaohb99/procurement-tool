export interface ConcurrentCompanyOption {
  id: number
  label: string
}

/**
 * Công ty chọn được cho một dòng kiêm nhiệm loại **Công ty** (duoc-CR-756): mọi công ty trong danh mục TRỪ công ty
 * hiện tại của hồ sơ — backend chặn 400 "Công ty kiêm nhiệm trùng công ty chính". `keepId` = công ty của dòng đang sửa,
 * luôn giữ lại (kể cả khi trùng công ty chính vì pháp nhân đã đổi sau đó) để ô không hiện trống với dữ liệu cũ.
 */
export function buildConcurrentCompanyOptions(
  companies: readonly { id: number; name: string }[],
  primaryCompanyId: number,
  keepId = 0,
): ConcurrentCompanyOption[] {
  return companies
    .filter((c) => c.id !== primaryCompanyId || (keepId > 0 && c.id === keepId))
    .map((c) => ({ id: c.id, label: c.name }))
    .sort((a, b) => a.label.localeCompare(b.label, 'vi'))
}
