// Hàm thuần của mục «Thuốc BVTV» (Tra cứu thị trường).

/** Mục «Tất cả …» của hai ô chọn. Không dùng chuỗi rỗng: Radix Select cấm `value=""`. */
export const ALL_PESTICIDE_OPTIONS = 'all'

interface PesticideFilters {
  q: string
  /** Mã tình trạng dạng chuỗi (từ ô chọn); `all` / rỗng = mọi tình trạng. */
  status: string
  pestGroup: string
  /** `only` = chỉ thuốc có hoạt chất cấm; giá trị khác = không lọc. */
  banned?: string
}

/** Giá trị «chỉ thuốc có hoạt chất cấm» của ô chọn lọc hoạt chất cấm. */
export const BANNED_ONLY = 'only'

/** Bộ lọc → tham số API. Ô trống KHÔNG gửi (`status=` rỗng thì FastAPI trả 422 vì đòi số). */
export function buildPesticideParams({
  q,
  status,
  pestGroup,
  banned,
}: PesticideFilters): Record<string, string> {
  const params: Record<string, string> = {}
  if (q.trim()) params.q = q.trim()
  if (/^\d+$/.test(status)) params.status = status
  if (pestGroup && pestGroup !== ALL_PESTICIDE_OPTIONS) params.pest_group = pestGroup
  if (banned === BANNED_ONLY) params.banned_only = 'true'
  return params
}

/**
 * Nhãn mục «Có hoạt chất cấm» của ô lọc. Chưa nạp danh sách cấm thì phải nói ra — không thì
 * «(0)» đọc thành «đã đối chiếu, danh mục sạch», trong khi thật ra chưa đối chiếu gì.
 */
export function formatBannedFilterLabel(bannedRules: number, bannedCount: number): string {
  if (bannedRules <= 0) return 'Có hoạt chất cấm (chưa có danh sách cấm)'
  return `Có hoạt chất cấm (${bannedCount.toLocaleString('vi-VN')})`
}

/**
 * Câu bảng rỗng phân biệt «chưa có danh mục» với «bộ lọc loại hết» — một câu chung thì người
 * vừa gõ nhầm một chữ đọc ra «chưa có dữ liệu» và tin là vậy.
 *
 * `bannedRules` chỉ truyền khi đang lọc «Có hoạt chất cấm». Rỗng lúc đó là KẾT QUẢ TỐT (danh mục
 * không lọt thuốc cấm), phải nói thẳng ra — trừ khi chưa có danh sách cấm để mà đối chiếu.
 */
export function resolvePesticideEmptyMessage(
  catalogTotal: number,
  canImport: boolean,
  bannedRules?: number,
): string {
  if (catalogTotal > 0) {
    if (bannedRules === undefined) {
      return 'Không có thuốc nào khớp bộ lọc — thử bỏ lọc tình trạng hoặc đổi từ khóa.'
    }
    return bannedRules > 0
      ? 'Không thuốc nào trong bộ lọc đang chọn chứa hoạt chất cấm theo TT 75/2025 (khớp theo tên hoạt chất).'
      : 'Chưa có danh sách hoạt chất cấm để đối chiếu — danh sách này nạp cùng danh mục pháp lý (mục «Pháp lý»).'
  }
  return canImport
    ? 'Chưa có danh mục thuốc BVTV. Bấm «Nạp danh mục» để tải tệp thuoc-bvtv.json / .xlsx.'
    : 'Chưa có danh mục thuốc BVTV — nhờ người phụ trách nạp tệp danh mục.'
}
