// Mục «Thuốc BVTV» của Tra cứu thị trường (29/09/2026) — khớp `pesticide_service` backend.

/**
 * Tình trạng đăng ký — mã SỐ theo luật R2, khớp `PesticideStatus` ở
 * `backend/app/modules/customs/constants.py`. Gõ tay vì `gen_status_ts.py` chỉ sinh bộ mã CHUỖI.
 */
export const PESTICIDE_STATUS = {
  unknown: 0,
  active: 1,
  expired: 2,
  inUse: 3,
} as const

/**
 * Hoạt chất CẤM (TT 75/2025) mà thuốc chứa — backend khớp theo TÊN hoạt chất
 * (`banned_ingredient_match.py`), chỉ để tham khảo. Nguồn đã bỏ thuốc cấm nên thường rỗng.
 */
export interface CustomsPesticideBanned {
  id: number
  name: string
  cas_no: string
  banned_year: number | null
  legal_basis: string
}

export interface CustomsPesticide {
  id: number
  source_id: number
  trade_name: string
  active_ingredient: string
  concentration: string
  pest_group: string
  sector: string
  registrant: string
  registration_no: string
  registered_on: string | null
  expires_on: string | null
  status: number
  status_label: string
  toxicity: string
  resistance: string
  source_url: string
  /** Câu mô tả của trang nguồn (duoc-CR-495) — thuốc tự thêm thì người nhập tự viết. */
  summary: string
  use_count: number
  /** Thuốc người dùng tự thêm trên màn (duoc-CR-490) — nạp lại danh mục giữ nó. */
  is_manual: boolean
  banned: CustomsPesticideBanned[]
}

export interface CustomsPesticideUse {
  id: number
  crop: string
  pest: string
  dosage: string
  pre_harvest_interval: string
  usage: string
}

export interface CustomsPesticideDetail extends CustomsPesticide {
  uses: CustomsPesticideUse[]
}

export interface CustomsPesticideList {
  total: number
  items: CustomsPesticide[]
}

export interface CustomsPesticideOptions {
  total: number
  last_loaded_at: string | null
  statuses: { value: number; label: string; count: number }[]
  pest_groups: { value: string; count: number }[]
  sectors: { value: string; count: number }[]
  /** Số thuốc tự thêm trên màn — nạp lại giữ chúng. */
  manual_count: number
  /** Số hoạt chất cấm đem ra đối chiếu — 0 = CHƯA nạp danh sách cấm (khác «không thuốc nào dính»). */
  banned_rules: number
  /** Số thuốc có ít nhất một hoạt chất cấm. */
  banned_count: number
}

export interface CustomsPesticideImportResult {
  pesticides: number
  uses: number
  /** Thuốc tự thêm được giữ lại qua lần nạp. */
  kept_manual: number
  /** Thuốc từ nguồn không còn trong tệp mới — bị xóa cùng tệp đính kèm (duoc-CR-494). */
  dropped: number
  retag: { total: number; tagged: number; technical: number }
}

/** Một dòng phạm vi sử dụng khi thêm / sửa — chưa có id (backend thay TOÀN BỘ phạm vi mỗi lần lưu). */
export type CustomsPesticideUseInput = Omit<CustomsPesticideUse, 'id'>

/**
 * Thân POST / PATCH `/api/customs/pesticides` — khớp `PesticideIn` ở
 * `backend/app/modules/customs/pesticide_schema.py`. Sửa là gửi ĐỦ cả bản ghi lẫn phạm vi.
 */
export interface CustomsPesticideInput {
  trade_name: string
  active_ingredient: string
  concentration: string
  pest_group: string
  sector: string
  registrant: string
  registration_no: string
  registered_on: string | null
  expires_on: string | null
  status: number
  toxicity: string
  resistance: string
  source_url: string
  summary: string
  uses: CustomsPesticideUseInput[]
}
