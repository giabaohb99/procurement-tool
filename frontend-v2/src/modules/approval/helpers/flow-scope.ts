/**
 * "Luồng này áp cho phiếu nào" — đọc/ghi giữa BỘ CHỌN và chuỗi điều kiện JSON.
 *
 * Backend nhận điều kiện dạng JSON (`condition_service.py`) vì nó phải nhận được
 * mọi loại chứng từ, kể cả loại chưa tồn tại lúc viết. Nhưng **không ai bắt người
 * khai luồng gõ JSON** — họ chọn "Loại văn bản: Quy chế, Quy trình", và tệp này
 * dịch qua lại.
 *
 * Ba lựa chọn, cố ý dừng ở ba: quá ba thì bộ chọn lại thành một trình soạn điều
 * kiện, đúng thứ vừa bỏ đi. Ai cần điều kiện phức tạp hơn (theo số tiền, theo
 * pháp nhân) thì khai ở phần rẽ nhánh của từng BƯỚC.
 */
export type FlowScopeKind = 'all' | 'doc_type' | 'document'

export interface FlowScope {
  kind: FlowScopeKind
  /** Id loại văn bản hoặc id văn bản, tùy `kind`. Rỗng khi `kind = 'all'`. */
  ids: number[]
}

/** Tên ô trên phiếu ứng với từng lựa chọn — phải khớp `approval_bridge.boi_canh`. */
const FIELD_OF: Record<Exclude<FlowScopeKind, 'all'>, string> = {
  doc_type: 'doc_type_id',
  document: 'id',
}

export const SCOPE_LABELS: Record<FlowScopeKind, string> = {
  all: 'Tất cả văn bản',
  doc_type: 'Chỉ một số loại văn bản',
  document: 'Chỉ một số văn bản cụ thể',
}

/** Chuỗi điều kiện → trạng thái bộ chọn. Không đọc được thì coi như «tất cả». */
export function parseScope(condition: string): FlowScope {
  if (!(condition || '').trim()) return { kind: 'all', ids: [] }

  let rows: unknown
  try {
    rows = JSON.parse(condition)
  } catch {
    //  Điều kiện gõ tay từ bản cũ hoặc hỏng: đừng nuốt mất, nhưng cũng đừng làm
    //  bộ chọn hiện sai. Người gọi kiểm `laDieuKienNangCao` để bày cảnh báo.
    return { kind: 'all', ids: [] }
  }
  if (!Array.isArray(rows) || rows.length !== 1) return { kind: 'all', ids: [] }

  const row = rows[0] as { field?: string; op?: string; value?: unknown }
  if (row.op !== 'in') return { kind: 'all', ids: [] }

  const kind = (Object.keys(FIELD_OF) as Exclude<FlowScopeKind, 'all'>[]).find(
    (key) => FIELD_OF[key] === row.field,
  )
  if (!kind) return { kind: 'all', ids: [] }

  const ids = Array.isArray(row.value)
    ? row.value.map(Number).filter((id) => Number.isFinite(id) && id > 0)
    : []
  return ids.length > 0 ? { kind, ids } : { kind: 'all', ids: [] }
}

/** Trạng thái bộ chọn → chuỗi điều kiện gửi lên backend. */
export function buildScopeCondition(scope: FlowScope): string {
  //  Chưa chọn cái nào thì coi như «tất cả»: gửi `in: []` là điều kiện không bao
  //  giờ khớp, và luồng lặng lẽ không bao giờ chạy.
  if (scope.kind === 'all' || scope.ids.length === 0) return ''
  return JSON.stringify([{ field: FIELD_OF[scope.kind], op: 'in', value: scope.ids }])
}

/**
 * Điều kiện này có nằm ngoài thứ bộ chọn diễn tả được không.
 *
 * Có thì màn hình phải nói ra và **không được lặng lẽ ghi đè** — người khai
 * trước đó có thể đã gõ tay một điều kiện đúng mà bộ chọn chưa hiểu.
 */
export function laDieuKienNangCao(condition: string): boolean {
  if (!(condition || '').trim()) return false
  return buildScopeCondition(parseScope(condition)) !== condition
}
