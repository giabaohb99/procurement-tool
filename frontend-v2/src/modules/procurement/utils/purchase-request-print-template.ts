/**
 * Ô chọn «Mẫu in» của bản in Phiếu đề xuất mua hàng — bao-CR-546.
 *
 * Thay hai nhóm nút bật/tắt cũ («Có chữ ký | Không chữ ký» và «Mẫu thường | Mẫu thuế»): nhóm
 * chữ ký biến mất khi chọn Mẫu thuế nên thanh nút nhảy, đại ca chê trông như giao diện cũ. Đại
 * ca chốt BA mẫu cố định trong một ô chọn; mỗi mẫu quy về đúng cặp cờ tờ phiếu đã dùng.
 */
export const PRINT_TEMPLATES = [
  { value: 'normal-signed', label: 'Mẫu thường – có chữ ký', taxMode: false, showSignature: true },
  { value: 'normal-unsigned', label: 'Mẫu thường – không chữ ký', taxMode: false, showSignature: false },
  //  Mẫu thuế để trống MỌI ô ký và thông tin người đề xuất — cờ chữ ký không còn nghĩa.
  { value: 'tax', label: 'Mẫu thuế', taxMode: true, showSignature: false },
] as const

export type PrintTemplateValue = (typeof PRINT_TEMPLATES)[number]['value']

export const DEFAULT_PRINT_TEMPLATE: PrintTemplateValue = 'normal-signed'

/** Mẫu in → hai cờ của tờ phiếu. Giá trị lạ (ô chọn trả chuỗi) thì về mẫu mặc định. */
export function resolvePrintTemplate(value: string): { taxMode: boolean; showSignature: boolean } {
  const found =
    PRINT_TEMPLATES.find((template) => template.value === value) ??
    PRINT_TEMPLATES.find((template) => template.value === DEFAULT_PRINT_TEMPLATE)
  return { taxMode: Boolean(found?.taxMode), showSignature: Boolean(found?.showSignature) }
}

/** Ô chọn trả chuỗi — chỉ nhận đúng ba giá trị khai ở trên. */
export function isPrintTemplateValue(value: string): value is PrintTemplateValue {
  return PRINT_TEMPLATES.some((template) => template.value === value)
}

/**
 * bao-CR-574 (đại ca chốt 03/10/2026) — ô «Mẫu in» gom luôn việc TÁCH THEO NHÀ CUNG CẤP.
 *
 * Trước đây nút «In phiếu» mở bản nào là do quyền người bấm (CR-420), còn chuyển bản phải bấm một
 * nút lẻ trên thanh công cụ. Nay nút luôn mở phiếu chung; người có quyền xem NCC thấy thêm nhóm
 * «Tách theo nhà cung cấp» trong cùng ô chọn, đủ ba mẫu. Một lựa chọn = (kiểu bản in, mẫu).
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

/** Mẫu đọc từ URL (`?mau=`); thiếu hoặc lạ thì về mẫu mặc định. */
export function readPrintTemplateParam(value: string | null): PrintTemplateValue {
  return value && isPrintTemplateValue(value) ? value : DEFAULT_PRINT_TEMPLATE
}
