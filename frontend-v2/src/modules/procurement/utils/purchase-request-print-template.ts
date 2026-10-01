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
