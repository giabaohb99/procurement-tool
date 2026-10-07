// bao-CR-608 — hộp SỬA một dòng hàng màn «Giá thị trường» (đại ca 07/10/2026).
//
// Biểu mẫu giữ mọi ô dạng CHUỖI (đúng thứ người dùng gõ), lúc lưu mới đổi sang số / ngày và chỉ
// gửi ô ĐÃ ĐỔI (PATCH `/api/customs/lines/{id}`). Gửi đủ mọi ô thì lần nào lưu cũng ghi lại doanh
// nghiệp / đối tác và đóng băng hoạt chất suy ra thành «do người nhập».
//
// Bốn ô suy ra / tự tính (hoạt chất, hàm lượng, hai giá VND): ô TRỐNG = để hệ thống suy ra / tính
// (giá trị đang suy ra hiện ở chữ mờ); gõ chữ / số = giá trị do người nhập, «Gắn lại nhãn» không ghi đè.
//
// Trần độ dài khớp `String(n)` của `tab_customs_line` / `tab_customs_party` — khớp schema
// `CustomsLineUpdate` ở backend; backend vẫn chặn lại bằng 422 nếu lệch.
import type { CustomsLine } from '../types/customs'

export type CustomsLineFieldKind = 'text' | 'integer' | 'decimal' | 'date' | 'transport'

export type CustomsLineEditKey =
  | 'reg_date'
  | 'office_code'
  | 'line_no'
  | 'import_country'
  | 'importer_tax_code'
  | 'importer_name'
  | 'partner_name'
  | 'origin_country'
  | 'product_name'
  | 'hs_code'
  | 'active_ingredient'
  | 'formulation'
  | 'quantity'
  | 'unit_code'
  | 'price_usd'
  | 'adj_price_usd'
  | 'price_nt'
  | 'adj_price_nt'
  | 'currency'
  | 'fx_rate'
  | 'usd_rate'
  | 'price_vnd_flat'
  | 'price_vnd_line_tax'
  | 'contract_no'
  | 'contract_date'
  | 'incoterm'
  | 'transport_mode'
  | 'rate_import'
  | 'tax_import'
  | 'rate_vat'
  | 'tax_vat'
  | 'rate_excise'
  | 'tax_excise'
  | 'rate_safeguard'
  | 'tax_safeguard'
  | 'tax_environment'

export interface CustomsLineField {
  key: CustomsLineEditKey
  label: string
  kind: CustomsLineFieldKind
  maxLength?: number
  required?: boolean
  /** Ô suy ra / tự tính: để trống = hệ thống tự làm. */
  derived?: boolean
}

export type CustomsLineForm = Record<CustomsLineEditKey, string>

/** Phương tiện vận chuyển — khớp `TransportMode` + `TRANSPORT_LABELS` ở backend (mã VNACCS). */
export const CUSTOMS_TRANSPORT_OPTIONS = [
  { value: '1', label: 'Đường không' },
  { value: '2', label: 'Đường biển (container)' },
  { value: '3', label: 'Đường biển (hàng rời, lỏng...)' },
  { value: '4', label: 'Đường bộ (xe tải)' },
  { value: '9', label: 'Khác' },
] as const

const text = (key: CustomsLineEditKey, label: string, maxLength: number, extra?: Partial<CustomsLineField>) => ({
  key,
  label,
  kind: 'text' as const,
  maxLength,
  ...extra,
})
const decimal = (key: CustomsLineEditKey, label: string, extra?: Partial<CustomsLineField>) => ({
  key,
  label,
  kind: 'decimal' as const,
  ...extra,
})

/** Sáu nhóm như hộp chi tiết dòng. */
export const CUSTOMS_LINE_FORM_GROUPS: { title: string; fields: CustomsLineField[] }[] = [
  {
    title: 'Tờ khai',
    fields: [
      { key: 'reg_date', label: 'Ngày đăng ký', kind: 'date', required: true },
      text('office_code', 'Nơi mở tờ khai', 10),
      { key: 'line_no', label: 'Số thứ tự hàng', kind: 'integer' },
      text('import_country', 'Nước nhận hàng', 2),
    ],
  },
  {
    title: 'Doanh nghiệp',
    fields: [
      text('importer_tax_code', 'Mã số thuế doanh nghiệp', 14),
      text('importer_name', 'Doanh nghiệp', 255),
      text('partner_name', 'Đối tác (bên bán)', 255),
      text('origin_country', 'Nước xuất xứ', 2),
    ],
  },
  {
    title: 'Hàng hóa',
    fields: [
      text('product_name', 'Tên hàng', 255, { required: true }),
      text('hs_code', 'Mã HS', 8),
      text('active_ingredient', 'Hoạt chất', 255, { derived: true }),
      text('formulation', 'Hàm lượng / dạng', 40, { derived: true }),
      decimal('quantity', 'Lượng'),
      text('unit_code', 'Đơn vị tính', 4),
    ],
  },
  {
    title: 'Giá',
    fields: [
      decimal('price_usd', 'Đơn giá khai báo (USD)'),
      decimal('adj_price_usd', 'Đơn giá điều chỉnh (USD)'),
      decimal('price_nt', 'Đơn giá nguyên tệ khai báo'),
      decimal('adj_price_nt', 'Đơn giá nguyên tệ điều chỉnh'),
      text('currency', 'Nguyên tệ', 3),
      decimal('fx_rate', 'Tỷ giá nguyên tệ'),
      decimal('usd_rate', 'Tỷ giá USD'),
      decimal('price_vnd_flat', 'Đơn giá VND (thuế NK 7%)', { derived: true }),
      decimal('price_vnd_line_tax', 'Đơn giá VND (theo thuế suất XNK)', { derived: true }),
    ],
  },
  {
    title: 'Hợp đồng & vận chuyển',
    fields: [
      text('contract_no', 'Số hợp đồng', 40),
      { key: 'contract_date', label: 'Ngày hợp đồng', kind: 'date' },
      text('incoterm', 'Điều kiện giao hàng', 3),
      { key: 'transport_mode', label: 'Phương tiện vận chuyển', kind: 'transport' },
    ],
  },
  {
    title: 'Thuế',
    fields: [
      decimal('rate_import', 'Thuế suất XNK (%)'),
      decimal('tax_import', 'Thuế XNK'),
      decimal('rate_vat', 'Thuế suất VAT (%)'),
      decimal('tax_vat', 'Thuế VAT'),
      decimal('rate_excise', 'Thuế suất TTĐB (%)'),
      decimal('tax_excise', 'Thuế TTĐB'),
      decimal('rate_safeguard', 'Thuế suất tự vệ (%)'),
      decimal('tax_safeguard', 'Thuế tự vệ'),
      decimal('tax_environment', 'Thuế môi trường'),
    ],
  },
]

export const CUSTOMS_LINE_FIELDS: CustomsLineField[] = CUSTOMS_LINE_FORM_GROUPS.flatMap((group) => group.fields)

/** Ô suy ra đang lấy giá trị do người nhập (tệp hoặc tay) hay do hệ thống. */
function isUserValue(line: CustomsLine, key: CustomsLineEditKey): boolean {
  if (key === 'active_ingredient') return Boolean(line.active_ingredient_from_file)
  if (key === 'formulation') return Boolean(line.formulation_from_file)
  if (key === 'price_vnd_flat') return Boolean(line.price_vnd_flat_from_file)
  if (key === 'price_vnd_line_tax') return Boolean(line.price_vnd_line_tax_from_file)
  return true
}

function show(value: unknown): string {
  return value === null || value === undefined ? '' : String(value)
}

/** Dòng → giá trị ban đầu của biểu mẫu. Ô suy ra mà hệ thống đang tự làm thì để TRỐNG. */
export function toCustomsLineForm(line: CustomsLine): CustomsLineForm {
  const form = {} as CustomsLineForm
  for (const field of CUSTOMS_LINE_FIELDS) {
    const raw = line[field.key as keyof CustomsLine]
    form[field.key] = field.derived && !isUserValue(line, field.key) ? '' : show(raw)
  }
  return form
}

/** Giá trị hệ thống đang suy ra / tính cho ô suy ra (hiện ở chữ mờ khi ô trống). */
export function derivedPlaceholder(line: CustomsLine, key: CustomsLineEditKey): string {
  if (isUserValue(line, key)) return ''
  const value = show(line[key as keyof CustomsLine])
  return value ? `Tự động: ${value}` : 'Tự động'
}

/**
 * Chuỗi số → số. Nhận dấu chấm hoặc dấu phẩy làm dấu thập phân (không nhận dấu ngăn nghìn).
 * Rỗng → null; không đọc được → NaN.
 */
export function parseCustomsNumber(value: string): number | null {
  const raw = value.replace(/\s/g, '')
  if (!raw) return null
  const normalized = raw.includes(',') && !raw.includes('.') ? raw.replace(',', '.') : raw
  return /^\d+(\.\d+)?$/.test(normalized) ? Number(normalized) : Number.NaN
}

/**
 * Biểu mẫu → thân PATCH chỉ gồm ô ĐÃ ĐỔI so với lúc mở. → `{ patch, error }`; `error` khác null
 * thì không gửi. Ô chữ rỗng = để trống (riêng ô suy ra rỗng = trả về cho hệ thống).
 */
export function buildCustomsLinePatch(
  initial: CustomsLineForm,
  form: CustomsLineForm,
): { patch: Record<string, string | number | null>; error: string | null } {
  const patch: Record<string, string | number | null> = {}
  for (const field of CUSTOMS_LINE_FIELDS) {
    const value = form[field.key].trim()
    if (field.required && !value) return { patch: {}, error: `Chưa nhập «${field.label}»` }
    if (value === initial[field.key].trim()) continue
    if (field.kind === 'text') {
      patch[field.key] = value
    } else if (field.kind === 'date') {
      patch[field.key] = value || null
    } else if (field.kind === 'transport') {
      patch[field.key] = value ? Number(value) : null
    } else {
      const number = parseCustomsNumber(value)
      if (Number.isNaN(number)) return { patch: {}, error: `«${field.label}» phải là số không âm` }
      if (field.kind === 'integer' && number !== null && !Number.isInteger(number)) {
        return { patch: {}, error: `«${field.label}» phải là số nguyên` }
      }
      patch[field.key] = number
    }
  }
  return { patch, error: null }
}
