// Hàm thuần của hộp thêm / sửa thuốc BVTV (duoc-CR-490) — dựng giá trị form, dựng thân gửi API.

import {
  PESTICIDE_STATUS,
  type CustomsPesticideDetail,
  type CustomsPesticideInput,
  type CustomsPesticideUseInput,
} from '../types/customs-pesticide'

/**
 * Trần độ dài — khớp ĐÚNG `_LIMITS` / `_USE_LIMITS` của `backend/.../customs/pesticide_reader.py`
 * (cũng là `String(n)` của model). Chặn sẵn ở ô nhập để người dùng không gõ xong mới ăn 422.
 */
export const PESTICIDE_LIMITS = {
  trade_name: 255,
  active_ingredient: 500,
  concentration: 100,
  pest_group: 100,
  sector: 100,
  registrant: 255,
  registration_no: 60,
  toxicity: 500,
  source_url: 255,
  resistance: 20_000,
  summary: 20_000,
} as const

export const PESTICIDE_USE_LIMITS = {
  crop: 255,
  pest: 255,
  dosage: 255,
  pre_harvest_interval: 255,
  usage: 20_000,
} as const

/** Ô chọn tình trạng — nhãn khớp `PESTICIDE_STATUS_LABELS` backend; «Chưa rõ» để cuối. */
export const PESTICIDE_STATUS_OPTIONS = [
  { value: PESTICIDE_STATUS.active, label: 'Còn hiệu lực' },
  { value: PESTICIDE_STATUS.expired, label: 'Hết hiệu lực' },
  { value: PESTICIDE_STATUS.inUse, label: 'Đang sử dụng' },
  { value: PESTICIDE_STATUS.unknown, label: 'Chưa rõ' },
] as const

/** Trần số dòng phạm vi của một thuốc — khớp `MAX_USES_PER_RECORD` backend. */
export const MAX_PESTICIDE_USES = 500

export function emptyPesticideUse(): CustomsPesticideUseInput {
  return { crop: '', pest: '', dosage: '', pre_harvest_interval: '', usage: '' }
}

export function emptyPesticideInput(): CustomsPesticideInput {
  return {
    trade_name: '',
    active_ingredient: '',
    concentration: '',
    pest_group: '',
    sector: '',
    registrant: '',
    registration_no: '',
    registered_on: null,
    expires_on: null,
    status: PESTICIDE_STATUS.active,
    toxicity: '',
    resistance: '',
    source_url: '',
    summary: '',
    uses: [],
  }
}

/** Chi tiết thuốc → giá trị form sửa. `null` từ backend (cột TEXT cũ) thành chuỗi rỗng. */
export function toPesticideInput(detail: CustomsPesticideDetail): CustomsPesticideInput {
  return {
    trade_name: detail.trade_name ?? '',
    active_ingredient: detail.active_ingredient ?? '',
    concentration: detail.concentration ?? '',
    pest_group: detail.pest_group ?? '',
    sector: detail.sector ?? '',
    registrant: detail.registrant ?? '',
    registration_no: detail.registration_no ?? '',
    registered_on: detail.registered_on || null,
    expires_on: detail.expires_on || null,
    status: detail.status,
    toxicity: detail.toxicity ?? '',
    resistance: detail.resistance ?? '',
    source_url: detail.source_url ?? '',
    summary: detail.summary ?? '',
    uses: detail.uses.map((use) => ({
      crop: use.crop ?? '',
      pest: use.pest ?? '',
      dosage: use.dosage ?? '',
      pre_harvest_interval: use.pre_harvest_interval ?? '',
      usage: use.usage ?? '',
    })),
  }
}

function trimUse(use: CustomsPesticideUseInput): CustomsPesticideUseInput {
  return {
    crop: use.crop.trim(),
    pest: use.pest.trim(),
    dosage: use.dosage.trim(),
    pre_harvest_interval: use.pre_harvest_interval.trim(),
    usage: use.usage.trim(),
  }
}

/**
 * Giá trị form → thân gửi API: cắt khoảng trắng, ngày rỗng thành `null` (FastAPI không nhận
 * chuỗi rỗng cho `date`), bỏ dòng phạm vi TRỐNG HẲN — người dùng bấm «Thêm dòng» rồi bỏ đó là
 * chuyện thường, lưu một dòng trắng lên danh mục thì bảng phạm vi có một hàng ma.
 */
export function buildPesticidePayload(input: CustomsPesticideInput): CustomsPesticideInput {
  return {
    ...input,
    trade_name: input.trade_name.trim(),
    active_ingredient: input.active_ingredient.trim(),
    concentration: input.concentration.trim(),
    pest_group: input.pest_group.trim(),
    sector: input.sector.trim(),
    registrant: input.registrant.trim(),
    registration_no: input.registration_no.trim(),
    registered_on: input.registered_on?.trim() || null,
    expires_on: input.expires_on?.trim() || null,
    toxicity: input.toxicity.trim(),
    resistance: input.resistance.trim(),
    source_url: input.source_url.trim(),
    summary: input.summary.trim(),
    uses: input.uses.map(trimUse).filter((use) => Object.values(use).some((value) => value !== '')),
  }
}

/**
 * Lỗi chặn lưu, kiểm ở giao diện TRƯỚC khi gửi (backend vẫn kiểm lại y hệt). Trả câu đầu tiên
 * gặp phải, hoặc `null` khi hợp lệ.
 */
export function validatePesticideInput(input: CustomsPesticideInput): string | null {
  const body = buildPesticidePayload(input)
  if (!body.trade_name) return 'Nhập tên thuốc.'
  if (!body.active_ingredient) return 'Nhập hoạt chất.'
  if (body.source_url && !/^https?:\/\//i.test(body.source_url)) {
    return 'Đường dẫn nguồn phải bắt đầu bằng http:// hoặc https://'
  }
  if (body.registered_on && body.expires_on && body.expires_on < body.registered_on) {
    return 'Ngày hết hạn đăng ký phải sau ngày cấp.'
  }
  if (body.uses.length > MAX_PESTICIDE_USES) {
    return `Tối đa ${MAX_PESTICIDE_USES} dòng phạm vi sử dụng.`
  }
  return null
}
