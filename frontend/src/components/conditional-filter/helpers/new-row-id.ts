// crypto.randomUUID() chỉ có trong secure context (https / localhost). App được truy cập qua
// http://<ip-LAN>:8080 nên phải có đường lui, nếu không bộ lọc sẽ ném lỗi ngay khi thêm dòng.
let counter = 0

export function newRowId(): string {
  const c: any = typeof crypto !== 'undefined' ? crypto : undefined
  if (c?.randomUUID) return c.randomUUID()
  counter += 1
  return `row-${counter}-${Math.random().toString(36).slice(2, 9)}`
}
