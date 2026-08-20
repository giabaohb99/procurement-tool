/**
 * Dòng khảo sát của MỘT nhà cung cấp — khớp `lines_by_supplier` của backend
 * (`modules/survey/service.py`), phục vụ `/api/survey-report/by-supplier`.
 *
 * Hai loại dòng ghép cặp theo hai khóa KHÁC NHAU:
 *  - dòng khảo sát NCC bắt theo `tax_code` (rơi về `supplier_code` khi trống);
 *  - dòng khảo sát Sản phẩm chỉ có `supplier_code`.
 * Nên phải gửi cả hai tham số, thiếu một cái là mất hẳn một nhóm.
 */

/** Dòng KSNCC — thông tin liên hệ, pháp lý của nhà cung cấp trong phiếu khảo sát. */
export interface SupplierSurveyLine {
  survey_id: number
  survey_code: string
  /** Khóa dòng, duy nhất trong phạm vi bảng dòng KSNCC. */
  line_id: number
  supplier_code: string
  supplier_name: string
  tax_code: string
  contact_date: string
  contact_person: string
  contact_phone: string
  /** Backend đã điền sẵn "Chờ duyệt" khi dòng chưa có kết quả duyệt. */
  line_approve: string
  note: string
}

/** Dòng KSSP — phương án báo giá của nhà cung cấp cho một mã hàng. */
export interface SupplierSurveyProductLine {
  survey_id: number
  survey_code: string
  line_id: number
  supplier_code: string
  /** Mã hàng nội bộ (mã VTBB/NL), không phải mã của nhà cung cấp. */
  internal_code: string
  product_name: string
  quote_unit: string
  price_by_volume: number
  moq: number
  line_approve: string
  note: string
}

export interface SupplierSurveys {
  supplier_lines: SupplierSurveyLine[]
  product_lines: SupplierSurveyProductLine[]
}
