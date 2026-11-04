/**
 * Chuẩn hóa bảng cha–con về MỘT FOREST không vòng.
 *
 * Cha không nằm trong `ids`, bằng `0`, hoặc tự trỏ vào mình → `0` (nút gốc).
 * Gặp vòng (A→B→A, dữ liệu nhập tay hoàn toàn có thể ra thế) thì CẮT một cạnh —
 * cạnh của nút có id nhỏ nhất trong vòng, để kết quả ổn định giữa các lần vẽ —
 * thay vì để đệ quy vô hạn treo trình duyệt.
 */
export function resolveParents(
  ids: readonly number[],
  parentOf: ReadonlyMap<number, number>,
): Map<number, number> {
  const members = new Set(ids)
  const resolved = new Map<number, number>()
  for (const id of ids) {
    const parent = parentOf.get(id) ?? 0
    resolved.set(id, parent !== id && members.has(parent) ? parent : 0)
  }
  for (const start of [...ids].sort((a, b) => a - b)) {
    // Mỗi lần cắt gỡ một cạnh nên vòng lặp ngoài chắc chắn dừng.
    for (;;) {
      const path: number[] = []
      const seen = new Set<number>()
      let cursor = start
      while (cursor !== 0 && !seen.has(cursor)) {
        seen.add(cursor)
        path.push(cursor)
        cursor = resolved.get(cursor) ?? 0
      }
      if (cursor === 0) break
      const cycle = path.slice(path.indexOf(cursor))
      resolved.set(Math.min(...cycle), 0)
    }
  }
  return resolved
}
