/**
 * Bộ lọc khối «Thêm phương án từ kết quả khảo sát» của màn Xử lý khảo sát — bao-CR-487.
 *
 * Ba ô: NCC (nhiều), phân loại (nhiều), từ khóa. Trong CÙNG một ô nhiều giá trị là HOẶC,
 * hai ô khác nhau là VÀ. Backend đòi ÍT NHẤT một tiêu chí — không thì trả rỗng chứ không
 * quét cả kho khảo sát; nút «Bỏ lọc» xóa cả ba ô một phát, rồi màn hình quay về câu nhắc.
 */
export interface AvailableLinesFilter {
  supplierCodes: string[]
  itemGroups: string[]
  search: string
}

/** Phân loại mặc định khi mở khối = phân loại của dòng YCBG (giống bản v1); dòng không có thì rỗng. */
export function defaultItemGroups(lineGroup: string | null | undefined): string[] {
  const group = (lineGroup || '').trim()
  return group ? [group] : []
}

export function hasAvailableLinesCriteria(filter: AvailableLinesFilter): boolean {
  return (
    filter.supplierCodes.length > 0 || filter.itemGroups.length > 0 || filter.search.trim().length > 0
  )
}

/** Ô phân loại đang đúng bằng phân loại của dòng — nút «Về phân loại dòng» ẩn đi khi đó. */
export function isLineGroupOnly(itemGroups: string[], lineGroup: string | null | undefined): boolean {
  const wanted = defaultItemGroups(lineGroup)
  return itemGroups.length === wanted.length && wanted.every((group) => itemGroups.includes(group))
}
