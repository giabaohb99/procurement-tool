import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import type { PurchasingPrintData } from '../types/purchasing-print'
import { printLineValues, printedTotals } from './purchase-request-print-options'

/**
 * Một dòng của bảng hàng trên tờ phiếu 003/BM/PKT, đã tính sẵn — duoc-CR-777.
 *
 * Tờ phiếu có hai nguồn dòng: dòng YCMH (mẫu thường / thuế, giá theo phương án đã chọn) và dòng
 * ĐƠN MUA HÀNG (mẫu thu mua, giá của đơn). Gom về một hình dạng để bảng chỉ có một cách vẽ.
 * `amount` là thành tiền TRƯỚC THUẾ (SL × đơn giá) — cột "Thành tiền" của khuôn cộng lại phải
 * ra đúng dòng "Tổng cộng", còn VAT nằm ở hai dòng tổng bên dưới.
 */
export interface PrintItemRow {
  key: string
  productName: string
  productCode: string
  unit: string
  /** Đơn vị báo giá lệch đơn vị dòng (H.4) — chỉ có ở dòng YCMH. */
  quoteUnit: string
  qty: number
  price: number
  amount: number
  /** TÊN kho như trên phiếu; tờ phiếu tự đổi sang mã kho lúc vẽ. */
  warehouse: string
  note: string
}

export interface PrintItemTotals {
  subtotal: number
  vat: number
  total: number
}

export interface PrintItemTable {
  rows: PrintItemRow[]
  totals: PrintItemTotals
  /**
   * Ngoại tệ thì ô tiền giữ số lẻ; VND làm tròn tới đồng như cũ. Số tiền của mẫu thu mua đã làm tròn
   * 2 số lẻ (máy chủ + `roundMoney`) nên in ra khớp bản v1 (tối đa 2 số lẻ).
   */
  fractionalMoney: boolean
}

/** Bảng hàng của mẫu thường / thuế — y hệt cách tính trước duoc-CR-777 (bao-CR-310 đợt 4). */
export function buildRequestItemTable(items: PurchaseRequestItem[]): PrintItemTable {
  const rows = items.map((item, index) => {
    const line = printLineValues(item)
    const qty = Number(item.qty) || 0
    return {
      key: String(item.id ?? `${item.product_code}-${index}`),
      productName: item.product_name,
      productCode: item.product_code,
      unit: item.unit,
      quoteUnit: line.quoteUnit,
      qty,
      price: line.price,
      amount: qty * line.price,
      warehouse: item.warehouse,
      note: item.note,
    }
  })
  return { rows, totals: printedTotals(items), fractionalMoney: false }
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100
}

/**
 * Bảng hàng của mẫu thu mua — dòng ĐƠN (SL đặt, đơn giá, VAT của đơn), tổng lấy thẳng từ máy chủ,
 * KHÔNG tính lại theo phương án của YCMH, và KHÔNG dùng `amount` của máy chủ cho cột dòng (nó đã gồm
 * VAT). Nơi giao + ghi chú dòng đơn không có nên mượn của dòng YCMH cùng mã hàng; không khớp thì trống.
 */
export function buildPurchasingItemTable(
  data: Pick<PurchasingPrintData, 'items' | 'subtotal' | 'vat' | 'total' | 'currency'>,
  requestItems: PurchaseRequestItem[],
): PrintItemTable {
  //  Khớp bản v1: so ĐÚNG chuỗi mã, trùng mã thì dòng SAU thắng; mã rỗng không mượn của ai.
  const byCode = new Map<string, PurchaseRequestItem>()
  for (const item of requestItems) {
    if (item.product_code) byCode.set(item.product_code, item)
  }
  const rows = data.items.map((line, index) => {
    const qty = Number(line.qty) || 0
    const price = Number(line.price) || 0
    const source = line.product_code ? byCode.get(line.product_code) : undefined
    return {
      key: String(line.line_id || `po-${index}`),
      productName: line.product_name,
      productCode: line.product_code,
      unit: line.unit,
      quoteUnit: '',
      qty,
      price,
      //  Cùng công thức `before` của backend (SL × giá, làm tròn 2 số lẻ) nên cộng lại khớp `subtotal`.
      amount: roundMoney(qty * price),
      warehouse: source?.warehouse ?? '',
      note: source?.note ?? '',
    }
  })
  const currency = (data.currency || 'VND').trim().toUpperCase()
  return {
    rows,
    totals: {
      subtotal: Number(data.subtotal) || 0,
      vat: Number(data.vat) || 0,
      total: Number(data.total) || 0,
    },
    fractionalMoney: currency !== '' && currency !== 'VND',
  }
}
