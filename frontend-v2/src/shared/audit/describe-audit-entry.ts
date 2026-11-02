import type { AuditLogEntry } from './audit-api'

/**
 * Câu mô tả một dòng nhật ký cho khối «Hoạt động» kiểu ERPNext (duoc-CR-710):
 * «‹người› đã tạo hồ sơ này» · «‹người› đã cập nhật ‹Phòng ban›, ‹Công ty›» · «‹người› — Duyệt».
 *
 * `fieldLabels` dịch tên cột (`department_id`) ra chữ người dùng thấy ở form («Phòng ban»). Cột KHÔNG
 * có trong bảng (cột kỹ thuật như `updated_at`, nhãn chép `position`) bị bỏ — in ra chỉ làm rối dòng.
 * Nhật ký chỉ có TÊN trường đã đổi, không có giá trị cũ / mới, nên câu dừng ở mức «đã cập nhật …».
 */
export interface AuditEntryDescription {
  /** Động từ / cụm mô tả, đứng sau tên người. */
  verb: string
  /** Nhãn các trường đã đổi (đã dịch, đã bỏ trùng), in đậm sau động từ. */
  fields: string[]
}

export function describeAuditEntry(
  log: Pick<AuditLogEntry, 'action' | 'action_label' | 'changed_fields'>,
  fieldLabels: Record<string, string> = {},
  createdNoun = 'bản ghi này',
): AuditEntryDescription {
  if (log.action === 'create') return { verb: `đã tạo ${createdNoun}`, fields: [] }
  if (log.action === 'update') {
    const fields = [
      ...new Set(
        (log.changed_fields ?? '')
          .split(',')
          .map((name) => fieldLabels[name.trim()])
          .filter((label): label is string => Boolean(label)),
      ),
    ]
    return fields.length > 0
      ? { verb: 'đã cập nhật', fields }
      : { verb: 'đã chỉnh sửa', fields: [] }
  }
  //  Hành động khác (duyệt, khóa tài khoản, đặt lại mật khẩu…): giữ nhãn backend dựng sẵn.
  return { verb: `— ${log.action_label}`, fields: [] }
}

/**
 * Gộp các dòng nhật ký sinh ra từ CÙNG một lượt gọi (cùng `request_id`, cùng người) thành một dòng.
 *
 * Một lần bấm Lưu hồ sơ có thể ghi vài dòng nhật ký giống hệt nhau (vd ảnh 02/11/2026: ba dòng
 * «Cập nhật · 29/10 11:09»). ERPNext không lặp; ở đây giữ dòng MỚI NHẤT (API trả mới nhất trước) và
 * hợp danh sách trường đã đổi của cả nhóm. Dòng không có `request_id` (ghi trước bao-CR-407) giữ nguyên.
 */
export function collapseSameRequest(logs: AuditLogEntry[]): AuditLogEntry[] {
  const out: AuditLogEntry[] = []
  const indexByRequest = new Map<string, number>()
  for (const log of logs) {
    const key = log.request_id ? `${log.request_id}|${log.by}|${log.action}` : ''
    const existing = key ? indexByRequest.get(key) : undefined
    if (existing === undefined) {
      if (key) indexByRequest.set(key, out.length)
      out.push(log)
      continue
    }
    const kept = out[existing]
    const merged = new Set(
      [kept.changed_fields, log.changed_fields]
        .flatMap((text) => (text ?? '').split(','))
        .map((name) => name.trim())
        .filter(Boolean),
    )
    out[existing] = { ...kept, changed_fields: [...merged].join(', ') }
  }
  return out
}
