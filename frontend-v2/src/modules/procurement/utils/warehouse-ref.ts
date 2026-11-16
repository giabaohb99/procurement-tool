import type { WarehouseOption } from '../api/purchase-request-support-api'

/**
 * bao-CR-759 — dòng YCMH lưu cả MÃ kho (`warehouse_code`) lẫn TÊN kho (`warehouse`).
 *
 * Dòng cũ (trước CR-759) và dòng do trợ lý AI lập chỉ có TÊN; máy chủ suy mã lúc lưu, nhưng
 * dữ liệu đang cầm trên màn hình có thể chưa qua lượt lưu đó — nên chỗ nào CẦN MÃ (tạo ĐMH
 * từ YCMH) phải ưu tiên mã của dòng rồi mới rơi về tra theo tên, cùng luật với máy chủ:
 * khớp ĐÚNG tên, trùng tên thì lấy kho đứng trước trong danh mục.
 */
export function resolveWarehouseCode(
  warehouses: readonly WarehouseOption[],
  line: { warehouse_code?: string; warehouse?: string },
): string {
  const code = (line.warehouse_code ?? '').trim()
  if (code) return code
  const name = (line.warehouse ?? '').trim()
  if (!name) return ''
  return warehouses.find((option) => (option.name ?? '').trim() === name)?.code ?? ''
}

/** Chọn kho theo TÊN trên ô chọn của dòng YCMH -> cặp giá trị ghi vào dòng (tên + mã). */
export function resolveWarehouseByName(
  warehouses: readonly WarehouseOption[],
  name: string,
): { warehouse: string; warehouse_code: string } {
  return { warehouse: name, warehouse_code: resolveWarehouseCode(warehouses, { warehouse: name }) }
}
