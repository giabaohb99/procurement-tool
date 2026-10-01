// duoc-CR-490 (bê từ bản v2 `frontend-v2/src/modules/procurement/utils/customs-pesticide.ts`) —
// hàm thuần của mục «Thuốc BVTV» (Tra cứu thị trường, bản cũ). Bản v2 chưa có form thêm/sửa/xóa
// nên các hàm chuyển đổi form ↔ API (cuối tệp) là thiết kế RIÊNG của bản cũ, khớp
// `backend/app/modules/customs/pesticide_schema.py`.

/** Tình trạng đăng ký — mã SỐ theo luật R2, khớp `PesticideStatus` backend. */
export const PESTICIDE_STATUS = {
  unknown: 0,
  active: 1,
  expired: 2,
  inUse: 3,
} as const

/** Thứ tự hiện trong ô CHỌN của form thêm/sửa. */
export const PESTICIDE_STATUS_OPTIONS = [
  { value: '1', label: 'Còn hiệu lực' },
  { value: '2', label: 'Hết hiệu lực' },
  { value: '3', label: 'Đang sử dụng' },
  { value: '0', label: 'Chưa rõ' },
]

/** Lớp `.badge.*` (xem index.css) theo tình trạng — dùng ở bảng danh sách + hộp chi tiết. */
export function pesticideStatusBadgeClass(status: number): string {
  if (status === PESTICIDE_STATUS.active) return 'ok'
  if (status === PESTICIDE_STATUS.inUse) return 'info'
  return 'gray' // Hết hiệu lực · Chưa rõ
}

/** Giá trị "chỉ thuốc có hoạt chất cấm" của ô lọc — khác rỗng nghĩa là có lọc. */
export const BANNED_ONLY = 'banned_only'

export type PesticideFilters = {
  q: string
  /** '' = mọi tình trạng. */
  status: string
  pestGroup: string
  /** Lĩnh vực (chuỗi gốc của nguồn); '' = mọi lĩnh vực (01/10/2026). */
  sector?: string
  /** '' | BANNED_ONLY. */
  banned: string
}

/** Mặc định lọc «Còn hiệu lực» (đại ca chốt 29/09) — thuốc hết hiệu lực vẫn có, bỏ lọc là thấy. */
export const DEFAULT_PESTICIDE_FILTERS: PesticideFilters = {
  q: '', status: String(PESTICIDE_STATUS.active), pestGroup: '', banned: '',
}

/** Bộ lọc → tham số API. Ô trống KHÔNG gửi (`status=` rỗng thì FastAPI trả 422 vì đòi số). */
export function buildPesticideParams(f: PesticideFilters): Record<string, string> {
  const out: Record<string, string> = {}
  if (f.q.trim()) out.q = f.q.trim()
  if (/^\d+$/.test(f.status)) out.status = f.status
  if (f.pestGroup) out.pest_group = f.pestGroup
  if (f.sector) out.sector = f.sector
  if (f.banned === BANNED_ONLY) out.banned_only = 'true'
  return out
}

/**
 * Nhãn mục «Có hoạt chất cấm» của ô lọc. `bannedRules` chưa có (đang tải ô lọc) → nói trơn,
 * đừng vội bảo «chưa có danh sách cấm». Bằng 0 mới thật sự là CHƯA nạp danh sách cấm.
 */
export function formatBannedFilterLabel(bannedRules?: number, bannedCount?: number): string {
  if (bannedRules === undefined) return 'Có hoạt chất cấm'
  if (bannedRules <= 0) return 'Có hoạt chất cấm (chưa có danh sách cấm)'
  return `Có hoạt chất cấm (${(bannedCount ?? 0).toLocaleString('vi-VN')})`
}

/**
 * Câu bảng rỗng phân biệt «chưa có danh mục» với «bộ lọc loại hết» — một câu chung thì người
 * vừa gõ nhầm một chữ đọc ra «chưa có dữ liệu» và tin là vậy.
 *
 * `bannedRules` chỉ truyền khi đang lọc «Có hoạt chất cấm»: rỗng lúc đó là KẾT QUẢ TỐT (danh mục
 * không lọt thuốc cấm), phải nói thẳng — trừ khi chưa có danh sách cấm để mà đối chiếu.
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

// ── Form thêm / sửa (bản v2 chưa có, thiết kế riêng cho bản cũ) ─────────────────────────────
// Trần chữ khớp ĐÚNG `_LIMITS` / `_USE_LIMITS` ở `backend/.../customs/pesticide_reader.py` —
// lệch thì chuỗi quá dài đi thẳng xuống MySQL, ra lỗi 500 thay vì câu «tối đa n ký tự».
export const PESTICIDE_FIELD_LIMITS = {
  trade_name: 255, active_ingredient: 500, concentration: 100, pest_group: 100, sector: 100,
  registrant: 255, registration_no: 60, toxicity: 500, source_url: 255,
} as const

export const PESTICIDE_USE_FIELD_LIMITS = {
  crop: 255, pest: 255, dosage: 255, pre_harvest_interval: 255,
} as const

export type PesticideUseForm = {
  id?: number
  crop: string
  pest: string
  dosage: string
  pre_harvest_interval: string
  usage: string
}

export type PesticideForm = {
  trade_name: string
  active_ingredient: string
  concentration: string
  pest_group: string
  sector: string
  registrant: string
  registration_no: string
  registered_on: string
  expires_on: string
  status: string
  toxicity: string
  resistance: string
  source_url: string
  /** duoc-CR-495 — câu mô tả của trang nguồn / người nhập tự viết. */
  summary: string
  uses: PesticideUseForm[]
}

export function blankPesticideForm(): PesticideForm {
  return {
    trade_name: '', active_ingredient: '', concentration: '', pest_group: '', sector: '',
    registrant: '', registration_no: '', registered_on: '', expires_on: '',
    status: String(PESTICIDE_STATUS.active), toxicity: '', resistance: '', source_url: '', summary: '', uses: [],
  }
}

/** Bản ghi API (GET chi tiết) → form sửa được. */
export function pesticideToForm(p: any): PesticideForm {
  return {
    trade_name: p.trade_name || '',
    active_ingredient: p.active_ingredient || '',
    concentration: p.concentration || '',
    pest_group: p.pest_group || '',
    sector: p.sector || '',
    registrant: p.registrant || '',
    registration_no: p.registration_no || '',
    registered_on: p.registered_on || '',
    expires_on: p.expires_on || '',
    status: String(p.status ?? PESTICIDE_STATUS.active),
    toxicity: p.toxicity || '',
    resistance: p.resistance || '',
    source_url: p.source_url || '',
    summary: p.summary || '',
    uses: (p.uses || []).map((u: any) => ({
      id: u.id, crop: u.crop || '', pest: u.pest || '', dosage: u.dosage || '',
      pre_harvest_interval: u.pre_harvest_interval || '', usage: u.usage || '',
    })),
  }
}

/** Form → thân JSON gửi POST/PATCH. Dòng phạm vi trống hoàn toàn thì bỏ, đỡ ghi rác. */
export function pesticideFormToPayload(f: PesticideForm) {
  return {
    trade_name: f.trade_name.trim(),
    active_ingredient: f.active_ingredient.trim(),
    concentration: f.concentration.trim(),
    pest_group: f.pest_group.trim(),
    sector: f.sector.trim(),
    registrant: f.registrant.trim(),
    registration_no: f.registration_no.trim(),
    registered_on: f.registered_on || null,
    expires_on: f.expires_on || null,
    status: Number(f.status) || 0,
    toxicity: f.toxicity.trim(),
    resistance: f.resistance.trim(),
    source_url: f.source_url.trim(),
    summary: f.summary.trim(),
    uses: f.uses
      .filter((u) => u.crop.trim() || u.pest.trim() || u.dosage.trim() || u.pre_harvest_interval.trim() || u.usage.trim())
      .map((u) => ({
        crop: u.crop.trim(), pest: u.pest.trim(), dosage: u.dosage.trim(),
        pre_harvest_interval: u.pre_harvest_interval.trim(), usage: u.usage.trim(),
      })),
  }
}

/**
 * Lỗi 422 → câu người đọc được. Lỗi nghiệp vụ (`HTTPException`) nằm thẳng ở `message`; lỗi kiểm
 * dữ liệu Pydantic thì `message` chỉ là "Dữ liệu không hợp lệ" chung chung, câu thật nằm rải
 * trong `details` (mảng `{msg,...}`, tiền tố "Value error, " của validator tự viết phải bỏ đi).
 */
export function extractPesticideErrorMessage(e: any, fallback = 'Lỗi khi lưu'): string {
  const err = e?.response?.data?.error
  if (!err) return fallback
  const details = err.details
  if (Array.isArray(details) && details.length) {
    const msgs = details
      .map((d: any) => String(d?.msg || '').replace(/^Value error,\s*/, ''))
      .filter(Boolean)
    if (msgs.length) return msgs.join('; ')
  }
  return err.message || fallback
}

/**
 * Query string mở mục «Thuốc BVTV» từ cột tra cứu của trang chi tiết (01/10/2026, đồng bộ bản v2).
 * Ép `pstatus=all`: số đếm của «Tra cứu nhanh» tính trên MỌI tình trạng.
 */
export function buildPesticideListSearch(f: { q?: string; pestGroup?: string; sector?: string }): string {
  const p = new URLSearchParams({ pstatus: 'all' })
  if (f.q?.trim()) p.set('pq', f.q.trim())
  if (f.pestGroup) p.set('pgroup', f.pestGroup)
  if (f.sector) p.set('psector', f.sector)
  return p.toString()
}
