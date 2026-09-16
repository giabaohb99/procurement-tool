import type { PurchaseRequestItem } from '../types/purchase-request-detail'

/**
 * bao-CR-310 đợt 4 (H.6 doc 03) — phần TÍNH của hai bản in theo phương án:
 *
 * - Bản A (phiếu đề xuất, mục F): từng dòng in GIÁ / %VAT của phương án ĐÃ CHỌN,
 *   dòng chưa chọn giữ giá đề xuất. Phương án 0 chụp đúng giá dòng gốc nên phiếu
 *   chưa ai đụng tới in ra y như cũ. Ô NCC chung KHÔNG lấy theo phương án (rà
 *   lại vòng 3): mục đó là "NCC do bộ phận đề xuất", chỉ in thứ nhập trên phiếu.
 * - Bản B (phiếu đề xuất tách theo NCC): gom dòng ĐÃ CHỌN phương án theo NCC,
 *   mỗi NCC MỘT TỜ PHIẾU y mẫu 003/BM/PKT — chỉ lọc dòng và điền tên NCC vào ô
 *   NCC, không đẻ bố cục riêng (khách bác ba lần, chốt 15/09). Cách gom soi
 *   gương nút tạo đơn backend (`generate_orders`),
 *   nhưng KHÔNG bỏ dòng đã lên ĐMH: bản in là bản lưu/ký, tạo đơn xong vẫn
 *   phải in lại được (góp ý khách 15/09); chặn tạo trùng là việc của nút gom.
 *
 * NCC bị backend che khi thiếu `supplier:read` (trả chuỗi rỗng) — mọi hàm ở đây
 * chỉ việc nhận chuỗi rỗng, không tự suy danh tính.
 */

/** Dòng ngày kiểu văn thư của khuôn 003/BM/PKT — dùng chung cho cả hai bản in. */
export function formatVietnameseLongDate(value: string): string {
  if (!value) return 'Ngày ........ tháng ........ năm ........'
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `Ngày ${day} tháng ${month} năm ${year}`
}

/** Giá / %VAT / đơn vị báo giá của MỘT DÒNG theo phương án đã chọn (bản A). */
export interface PrintLineValues {
  price: number
  vatPct: number
  /** Đơn vị NCC báo giá KHÁC đơn vị của dòng — H.4: bản in ghi cả hai, rỗng = trùng nhau. */
  quoteUnit: string
}

/** CR-058: VAT của phương án bỏ trống (0) thì rơi về VAT của dòng — cùng luật nút gom. */
export function printLineValues(item: PurchaseRequestItem): PrintLineValues {
  const chosen = item.chosen_option ?? null
  if (!chosen) {
    return { price: Number(item.price) || 0, vatPct: Number(item.vat_pct) || 0, quoteUnit: '' }
  }
  const quoteUnit = (chosen.snap_quote_unit || '').trim()
  const lineUnit = (item.unit || '').trim()
  return {
    price: Number(chosen.snap_price_by_volume) || 0,
    vatPct: Number(chosen.snap_vat) || Number(item.vat_pct) || 0,
    // So KHÔNG phân biệt hoa thường: "Cái" của báo giá và "cái" của dòng là một
    // đơn vị — in kèm "(báo giá: Cái)" chỉ làm gãy dòng ô ĐVT (góp ý khách 15/09).
    quoteUnit:
      quoteUnit && quoteUnit.toLowerCase() !== lineUnit.toLowerCase() ? quoteUnit : '',
  }
}

/**
 * Một dòng trên MỘT TỜ của bản B.
 *
 * Chỉ giữ phần TÍNH TIỀN (để cộng tổng cho ô tick NCC trên thanh công cụ) và
 * `item` gốc — tờ in là khuôn phiếu đề xuất dùng chung, nó tự đọc `item` bằng
 * `printLineValues`. Bốn trường cũ (đơn vị báo giá, tên NCC gọi, thời gian /
 * nơi giao theo cam kết NCC) đã gỡ ở rà lại vòng 4 vì mẫu 003/BM/PKT không có
 * ô nào cho chúng.
 */
export interface SupplierPrintLine {
  item: PurchaseRequestItem
  price: number
  vatPct: number
  /** qty × price × (1 + vatPct/100) — tiền GỒM VAT của dòng. */
  amount: number
}

/** Một trang bản B = một NCC (trang cuối có thể là nhóm CHƯA CÓ NCC). */
export interface SupplierPrintGroup {
  /** Khóa bền cho ô tick — rỗng với nhóm chưa có NCC. */
  key: string
  supplierCode: string
  supplierName: string
  lines: SupplierPrintLine[]
  subtotal: number
  vatAmount: number
  total: number
}

export interface SupplierPrintPlan {
  groups: SupplierPrintGroup[]
  /** Số dòng bị bỏ qua — nói thành lời trên thanh công cụ thay vì im lặng. */
  skipped: { noChosen: number; cancelled: number }
}

/**
 * Gom dòng theo NCC cho bản B: bỏ dòng hủy và dòng không chọn phương án; còn
 * lại gom theo NCC của phương án đã chọn, dòng chưa có NCC dồn vào MỘT nhóm
 * cuối. KHÁC nút gom MỘT chỗ có chủ đích (góp ý khách 15/09): dòng đã nằm
 * trên ĐMH (kể cả đơn nháp — CR-074 đổi `line_status` ngay lúc lập) VẪN IN,
 * vì đây là bản lưu/ký chứ không phải lệnh tạo đơn — bản đầu soi gương cả
 * luật đó nên khách vừa tạo đơn xong là bản in ra 0 trang. Phương án chọn
 * không đổi sau khi lên đơn nên các trang vẫn khớp các đơn đã tạo.
 */
export function buildSupplierPrintPlan(items: PurchaseRequestItem[]): SupplierPrintPlan {
  const groups = new Map<string, SupplierPrintGroup>()
  const skipped = { noChosen: 0, cancelled: 0 }

  for (const item of items) {
    if (!item.product_name) continue
    if (item.line_status === 'cancelled') {
      skipped.cancelled += 1
      continue
    }
    const chosen = item.chosen_option
    if (!chosen) {
      skipped.noChosen += 1
      continue
    }

    const key =
      chosen.supplier_code || chosen.supplier_name
        ? `${chosen.supplier_code}|${chosen.supplier_name}`
        : ''
    let group = groups.get(key)
    if (!group) {
      group = {
        key,
        supplierCode: chosen.supplier_code,
        supplierName: chosen.supplier_name,
        lines: [],
        subtotal: 0,
        vatAmount: 0,
        total: 0,
      }
      groups.set(key, group)
    }

    const { price, vatPct } = printLineValues(item)
    const qty = Number(item.qty) || 0
    const amount = qty * price * (1 + vatPct / 100)
    group.lines.push({ item, price, vatPct, amount })
    group.subtotal += qty * price
    group.total += amount
  }

  const list = [...groups.values()]
  for (const group of list) {
    group.vatAmount = group.total - group.subtotal
  }
  // NCC có tên xếp theo tên; nhóm CHƯA CÓ NCC (key rỗng) luôn đứng cuối —
  // đúng vị trí "một đơn nháp riêng không NCC" của nút gom.
  list.sort((a, b) => {
    if (!a.key) return 1
    if (!b.key) return -1
    return (a.supplierName || a.supplierCode).localeCompare(
      b.supplierName || b.supplierCode,
      'vi',
    )
  })
  return { groups: list, skipped }
}

/** Tổng tiền của các dòng ĐANG IN trên bản A — "Thành tiền, tổng cộng: tính lại theo giá đang in". */
export function printedTotals(items: PurchaseRequestItem[]): {
  subtotal: number
  vat: number
  total: number
} {
  let subtotal = 0
  let total = 0
  for (const item of items) {
    const { price, vatPct } = printLineValues(item)
    const qty = Number(item.qty) || 0
    subtotal += qty * price
    total += qty * price * (1 + vatPct / 100)
  }
  return { subtotal, vat: total - subtotal, total }
}
