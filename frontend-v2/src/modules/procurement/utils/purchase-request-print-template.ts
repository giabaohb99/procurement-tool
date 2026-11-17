/**
 * Ô chọn "Mẫu in" của bản in Phiếu đề xuất mua hàng — bao-CR-546.
 *
 * Thay hai nhóm nút bật/tắt cũ ("Có chữ ký | Không chữ ký" và "Mẫu thường | Mẫu thuế"): nhóm
 * chữ ký biến mất khi chọn Mẫu thuế nên thanh nút nhảy, đại ca chê trông như giao diện cũ. Đại
 * ca chốt BA mẫu cố định trong một ô chọn; mỗi mẫu quy về đúng cặp cờ tờ phiếu đã dùng.
 */
export const PRINT_TEMPLATES = [
  { value: 'normal-signed', label: 'Mẫu thường – có chữ ký', taxMode: false, showSignature: true },
  { value: 'normal-unsigned', label: 'Mẫu thường – không chữ ký', taxMode: false, showSignature: false },
  //  Mẫu thuế để trống MỌI ô ký và thông tin người đề xuất — cờ chữ ký không còn nghĩa.
  { value: 'tax', label: 'Mẫu thuế', taxMode: true, showSignature: false },
] as const

/**
 * duoc-CR-777 (anh Được chốt 17/11/2026) — hai mẫu THU MUA, CHỈ có ở bản in YCMH mở từ ĐƠN MUA HÀNG
 * (`fromPo`), và chỉ khi người in đọc được đơn đó (đường `purchasing-print` trả dữ liệu). Người đề
 * xuất = người đang in, trưởng phòng = quản lý trực tiếp của họ, bảng hàng = dòng của đơn. Cố ý tách
 * khỏi `PRINT_TEMPLATES`: danh sách kia còn dùng cho nhóm "Tách theo NCC" và trang in theo NCC —
 * hai mẫu này không được lọt sang đó.
 */
export const PURCHASING_PRINT_TEMPLATES = [
  { value: 'purchasing-signed', label: 'Mẫu thu mua – có chữ ký', taxMode: false, showSignature: true },
  { value: 'purchasing-unsigned', label: 'Mẫu thu mua – không chữ ký', taxMode: false, showSignature: false },
] as const

const ALL_PRINT_TEMPLATES = [...PRINT_TEMPLATES, ...PURCHASING_PRINT_TEMPLATES]

export type PrintTemplateValue = (typeof ALL_PRINT_TEMPLATES)[number]['value']

export interface PrintTemplateOption {
  value: PrintTemplateValue
  label: string
  taxMode: boolean
  showSignature: boolean
}

export const DEFAULT_PRINT_TEMPLATE: PrintTemplateValue = 'normal-signed'

/** Mẫu in → hai cờ của tờ phiếu. Giá trị lạ (ô chọn trả chuỗi) thì về mẫu mặc định. */
export function resolvePrintTemplate(value: string): { taxMode: boolean; showSignature: boolean } {
  const found =
    ALL_PRINT_TEMPLATES.find((template) => template.value === value) ??
    ALL_PRINT_TEMPLATES.find((template) => template.value === DEFAULT_PRINT_TEMPLATE)
  return { taxMode: Boolean(found?.taxMode), showSignature: Boolean(found?.showSignature) }
}

/** Ô chọn trả chuỗi — chỉ nhận đúng các giá trị khai ở trên (ba mẫu chung + hai mẫu thu mua). */
export function isPrintTemplateValue(value: string): value is PrintTemplateValue {
  return ALL_PRINT_TEMPLATES.some((template) => template.value === value)
}

/** duoc-CR-777 — mẫu đang chọn có phải một trong hai mẫu thu mua không. */
export function isPurchasingPrintTemplate(value: string): boolean {
  return PURCHASING_PRINT_TEMPLATES.some((template) => template.value === value)
}

/**
 * duoc-CR-777 — danh sách mẫu của ô chọn: ba mẫu chung, thêm hai mẫu thu mua khi `purchasing`
 * (bản in mở từ đơn + có quyền đọc đơn + lệnh `purchasing-print` đã trả dữ liệu).
 */
export function listPrintTemplates(purchasing: boolean): readonly PrintTemplateOption[] {
  //  duoc-CR-777 (anh Được chốt 17/11/2026): in từ ĐMH mà dùng được Mẫu thu mua thì hai mẫu đó đứng ĐẦU danh sách.
  return purchasing ? [...PURCHASING_PRINT_TEMPLATES, ...PRINT_TEMPLATES] : PRINT_TEMPLATES
}

/**
 * Mẫu chọn sẵn khi người dùng CHƯA chọn gì (không có `?mau=` trên URL, chưa đổi ô chọn): luôn là *Mẫu thường – có
 * chữ ký*, kể cả khi dùng được Mẫu thu mua (bao-CR-779, đại ca chốt 17/11/2026: Mẫu thu mua vẫn đứng đầu danh sách
 * nhưng phải tự chọn, vì mẫu đó in chữ ký quản lý trực tiếp dù người này chưa duyệt gì trên phiếu).
 */
export function defaultPrintTemplate(): PrintTemplateValue {
  return DEFAULT_PRINT_TEMPLATE
}

/**
 * duoc-CR-777 — mẫu THỰC áp: đang chọn mẫu thu mua (vd `?mau=purchasing-signed` trên URL) mà dữ liệu
 * thu mua không có (đang nạp, 403/404, không có quyền) thì về mẫu mặc định, để ô chọn không trống
 * và tờ phiếu không in nửa nọ nửa kia.
 */
export function resolveAvailablePrintTemplate(
  value: PrintTemplateValue,
  purchasingAvailable: boolean,
): PrintTemplateValue {
  return isPurchasingPrintTemplate(value) && !purchasingAvailable ? DEFAULT_PRINT_TEMPLATE : value
}

/**
 * bao-CR-574 (đại ca chốt 03/10/2026) — ô "Mẫu in" gom luôn việc TÁCH THEO NHÀ CUNG CẤP.
 *
 * Trước đây nút "In phiếu" mở bản nào là do quyền người bấm (CR-420), còn chuyển bản phải bấm một
 * nút lẻ trên thanh công cụ. Nay nút luôn mở phiếu chung; người có quyền xem NCC thấy thêm nhóm
 * "Tách theo nhà cung cấp" trong cùng ô chọn, đủ ba mẫu. Một lựa chọn = (kiểu bản in, mẫu).
 */
export const PRINT_LAYOUTS = [
  { value: 'common', label: 'Phiếu chung' },
  { value: 'supplier', label: 'Tách theo nhà cung cấp' },
] as const

export type PrintLayout = (typeof PRINT_LAYOUTS)[number]['value']

/** Tham số trên URL mang mẫu đang chọn sang trang in kia khi đổi kiểu bản in. */
export const PRINT_TEMPLATE_PARAM = 'mau'

const CHOICE_SEPARATOR = ':'

/** Một lựa chọn trong ô — chuỗi vì ô chọn chỉ nhận chuỗi. */
export function encodePrintChoice(layout: PrintLayout, template: PrintTemplateValue): string {
  return `${layout}${CHOICE_SEPARATOR}${template}`
}

/** Giải ngược `encodePrintChoice`; chuỗi lạ thì `null` để ô chọn bỏ qua, không đoán. */
export function decodePrintChoice(
  value: string,
): { layout: PrintLayout; template: PrintTemplateValue } | null {
  const [layout, template, ...rest] = value.split(CHOICE_SEPARATOR)
  if (rest.length > 0 || template === undefined) return null
  if (!PRINT_LAYOUTS.some((option) => option.value === layout)) return null
  if (!isPrintTemplateValue(template)) return null
  return { layout: layout as PrintLayout, template }
}

/**
 * Mẫu đọc từ URL (`?mau=`); thiếu hoặc lạ thì về mẫu mặc định. duoc-CR-777: hai mẫu thu mua CHỈ
 * nhận khi `allowPurchasing` (bản in mở từ đơn) — trang in YCMH thường và trang in theo NCC coi
 * chúng là giá trị lạ.
 */
export function readPrintTemplateParam(
  value: string | null,
  { allowPurchasing = false }: { allowPurchasing?: boolean } = {},
): PrintTemplateValue {
  if (!value || !isPrintTemplateValue(value)) return DEFAULT_PRINT_TEMPLATE
  if (!allowPurchasing && isPurchasingPrintTemplate(value)) return DEFAULT_PRINT_TEMPLATE
  return value
}
