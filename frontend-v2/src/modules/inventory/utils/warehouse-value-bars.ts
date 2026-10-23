import type { InventoryByWarehouse } from '@/modules/procurement/api/procurement-dashboard-api'
import type { ChartDatum } from '@/shared/ui/chart'

/** Cột gom các kho nhỏ ngoài top. */
export const OTHER_LABEL = 'Khác'
/** Dòng tồn không có mã kho — máy chủ gom vào `warehouse_code = ""`. */
export const UNASSIGNED_LABEL = 'Chưa gán kho'

function labelOf(row: InventoryByWarehouse): string {
  if (!row.warehouse_code) return UNASSIGNED_LABEL
  return row.warehouse_name.trim() || row.warehouse_code
}

/**
 * Dữ liệu cho biểu đồ *Giá trị tồn theo kho* (kh-NT2-8, NF-22) từ khóa
 * `kpi_inv_by_warehouse` của `/api/dashboard/overview`.
 *
 * - Giữ `top` kho lớn nhất, phần còn lại gộp thành một cột *Khác* — trừ khi chỉ dư
 *   đúng một kho, lúc đó vẽ luôn kho đó (gộp một kho vào *Khác* là giấu tên mà không gọn).
 * - Tổng các cột luôn bằng tổng giá trị tồn (máy chủ cam kết bằng `kpi.inv_value`).
 * - Bỏ kho giá trị ≤ 0: cột dài 0 vô ích, giá trị âm là dữ liệu hỏng và làm vỡ trục.
 * - Hai kho trùng tên thì kèm mã: trục danh mục gộp nhãn trùng thành một dòng.
 */
export function buildWarehouseValueBars(
  rows: InventoryByWarehouse[] | undefined,
  top: number,
): ChartDatum[] {
  const positive = (rows ?? []).filter((row) => row.value > 0).sort((a, b) => b.value - a.value)
  if (positive.length === 0) return []

  const keep = Math.max(1, top)
  const shown = positive.length - keep <= 1 ? positive : positive.slice(0, keep)
  const rest = positive.slice(shown.length)

  const counts = new Map<string, number>()
  for (const row of shown) counts.set(labelOf(row), (counts.get(labelOf(row)) ?? 0) + 1)

  const bars: ChartDatum[] = shown.map((row) => {
    const label = labelOf(row)
    return {
      label: (counts.get(label) ?? 0) > 1 && row.warehouse_code ? `${label} (${row.warehouse_code})` : label,
      value: row.value,
    }
  })
  if (rest.length > 0) {
    bars.push({ label: OTHER_LABEL, value: rest.reduce((sum, row) => sum + row.value, 0) })
  }
  return bars
}
