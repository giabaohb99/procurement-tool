import type { AuditLogEntry } from '@/shared/audit'

/** Lý do phiếu bị chặn, kèm ai nói và nói lúc nào. */
export interface SealStopReason {
  reason: string
  by: string
  at: string
}

/**
 * Dấu nối backend dùng khi ghép lý do vào câu nhật ký
 * (`seal_request/controller.py::_with_reason`): `"<hành động> — Lý do: <lý do>"`.
 *
 * ⚠️ Gạch ngang dài `—` (em dash), KHÔNG phải gạch nối `-`. Gõ nhầm ký tự là hàm
 * này lặng lẽ không khớp gì cả và màn hình mất hẳn lý do mà chẳng có lỗi nào.
 */
const REASON_MARK = ' — Lý do: '

/**
 * Câu nhật ký của các bước LÙI/CHẶN. Phải soi theo câu chứ không theo `action`:
 * backend ghi «Yêu cầu chỉnh sửa» dưới action `update` — đúng action mà mọi lần
 * sửa phiếu bình thường cũng dùng.
 */
const STOP_PREFIXES = ['Từ chối', 'Yêu cầu chỉnh sửa']

/**
 * Moi LÝ DO bị từ chối / bị trả về ra khỏi nhật ký thao tác.
 *
 * ⚠️ Vì sao phải moi từ nhật ký: lý do **không có cột riêng** trên phiếu. Backend
 * cố ý không ghi nó vào `note` — ô Ghi chú chỉ giữ chữ của người TẠO phiếu, ghi
 * đè vào đó thì người ta sửa phiếu xong là lý do biến mất (xem chú thích trong
 * `seal_request/service.py::return_seal`). Nơi duy nhất còn giữ là câu nhật ký
 * `_with_reason` và thư thông báo.
 *
 * Trả về lượt GẦN NHẤT: một phiếu có thể bị trả về, sửa, gửi lại rồi bị trả lần
 * nữa — lý do đang có hiệu lực là lý do mới nhất, lý do cũ thuộc về nhật ký.
 *
 * Hàm THUẦN. `null` = không tìm thấy (nhật ký chưa tải xong, dòng ghi từ bản cũ
 * chưa có lý do, hoặc người xem không được đọc nhật ký).
 */
export function extractSealStopReason(entries: AuditLogEntry[] | undefined): SealStopReason | null {
  if (!entries?.length) return null

  for (const entry of entries) {
    const message = entry.message ?? ''
    if (!STOP_PREFIXES.some((prefix) => message.startsWith(prefix))) continue

    const at = message.indexOf(REASON_MARK)
    if (at === -1) continue

    const reason = message.slice(at + REASON_MARK.length).trim()
    if (!reason) continue

    return { reason, by: entry.by ?? '', at: entry.at ?? '' }
  }

  return null
}
