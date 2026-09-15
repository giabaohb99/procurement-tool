import type { PermissionMeta, RolePermissionRow } from '@/modules/hr/types/role'
import { permissionField } from '@/modules/hr/types/role'

/**
 * Đọc/ghi một TẬP Ô của ma trận phân quyền (`entities × actions`).
 *
 * Màn Phân quyền có tới sáu cỡ "chọn hết" khác nhau — một ô, cả dòng entity,
 * một hành động của cả phân hệ, cả phân hệ, một cột của cả bảng, và cả bảng.
 * Tất cả đều là CÙNG một phép toán trên một tập ô, nên chỉ khai ở đây một lần:
 * sáu bản chép sẽ lệch nhau ở đúng chỗ khó thấy nhất (dòng chưa từng được tick
 * nên chưa có trong `rows`).
 */

/** Dòng của một entity; chưa cấp quyền gì thì trả dòng rỗng phạm vi mặc định. */
export function emptyRow(entity: string): RolePermissionRow {
  return { entity, scope: 'own' }
}

/**
 * Trạng thái ba mức của một tập ô: bật đủ / bật một phần / tắt.
 *
 * ⚠️ Tập RỖNG trả `false`, không phải `true`. Kiểu "mọi phần tử đều bật" của
 * `every` đúng một cách vô nghĩa với mảng rỗng, và ô tiêu đề sẽ hiện dấu tick
 * cho một phân hệ không có mục con nào — bấm vào thì không có gì xảy ra.
 */
export function cellsState(
  rows: Record<string, RolePermissionRow>,
  entities: string[],
  actions: string[],
): boolean | 'indeterminate' {
  const total = entities.length * actions.length
  if (total === 0) return false

  let on = 0
  for (const entity of entities) {
    const row = rows[entity]
    if (!row) continue
    for (const action of actions) if (row[permissionField(action)]) on += 1
  }

  if (on === 0) return false
  if (on === total) return true
  return 'indeterminate'
}

/**
 * Bật (hoặc tắt) một tập ô. Trả về bản ghi MỚI — state của React phải đổi tham
 * chiếu mới vẽ lại.
 *
 * Entity chưa có dòng nào thì tạo dòng mới với phạm vi mặc định `own`; cột
 * "Phạm vi" của các dòng đang có được giữ nguyên, bật/tắt quyền không đụng tới
 * phạm vi đã đặt.
 */
export function setCells(
  rows: Record<string, RolePermissionRow>,
  entities: string[],
  actions: string[],
  turnOn: boolean,
): Record<string, RolePermissionRow> {
  const next = { ...rows }
  for (const entity of entities) {
    const row = { ...(next[entity] ?? emptyRow(entity)) }
    for (const action of actions) row[permissionField(action)] = turnOn
    next[entity] = row
  }
  return next
}

/**
 * Bấm một lần vào ô/nút "chọn hết" của một tập ô: chưa bật ĐỦ thì bật hết,
 * đang bật đủ thì tắt hết. Nửa vời cũng bật cho đủ — người bấm vào một ô đang
 * hiện dấu gạch muốn "cho hết", chứ không muốn mất cả những ô đã tick.
 */
export function toggleCells(
  rows: Record<string, RolePermissionRow>,
  entities: string[],
  actions: string[],
): Record<string, RolePermissionRow> {
  return setCells(rows, entities, actions, cellsState(rows, entities, actions) !== true)
}

/**
 * Ép state ma trận về payload gửi lên backend.
 *
 * Dòng KHÔNG bật hành động nào bị loại — backend hiểu là "vai trò không có
 * quyền gì trên entity đó", giữ lại chỉ tạo rác trong bảng phân quyền.
 */
export function toPermissionPayload(
  meta: PermissionMeta,
  rows: Record<string, RolePermissionRow>,
): RolePermissionRow[] {
  const actionKeys = meta.actions.map((action) => action.key)

  return meta.entities
    .map((entity) => {
      const row = rows[entity.key] ?? emptyRow(entity.key)
      const payload: RolePermissionRow = {
        entity: entity.key,
        scope: row.scope || 'own',
      }
      for (const action of actionKeys) {
        payload[permissionField(action)] = !!row[permissionField(action)]
      }
      return payload
    })
    .filter((row) => actionKeys.some((action) => row[permissionField(action)]))
}
