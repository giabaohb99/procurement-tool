import type { Supplier } from '@/modules/production/types/supplier'

/**
 * Danh mục nền dùng chung cho mọi ô của dòng khảo sát.
 *
 * Dựng MỘT lần ở trang rồi truyền xuống: bảng có vài chục dòng × vài chục ô,
 * mỗi ô tự dò danh sách NCC là dò lại hàng nghìn lần cho một lần gõ phím.
 */
export interface SurveyCatalog {
  suppliers: Supplier[]
  supplierByCode: Map<string, Supplier>
  supplierCodes: Set<string>
  units: string[]
}

export function buildSurveyCatalog(suppliers: Supplier[], units: string[]): SurveyCatalog {
  return {
    suppliers,
    supplierByCode: new Map(suppliers.map((supplier) => [supplier.code, supplier])),
    supplierCodes: new Set(suppliers.map((supplier) => supplier.code)),
    units,
  }
}
