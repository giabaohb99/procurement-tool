import { describe, expect, it } from 'vitest'

import type { AuditLogEntry } from '@/shared/audit'
import { extractSealStopReason } from './extract-seal-reason'

/** Một dòng nhật ký tối thiểu. */
function entry(patch: Partial<AuditLogEntry>): AuditLogEntry {
  return {
    id: 1,
    action: 'update',
    action_label: 'Cập nhật',
    entity_id: 8,
    by: 'Trần Trưởng Phòng',
    at: '2026-09-18T09:00:00',
    ...patch,
  }
}

describe('extractSealStopReason', () => {
  it('pulls the reason out of the audit sentence the backend builds', () => {
    const found = extractSealStopReason([
      entry({ action: 'cancel', message: 'Từ chối yêu cầu — Lý do: Chưa đính kèm thư mời' }),
    ])

    expect(found).toEqual({
      reason: 'Chưa đính kèm thư mời',
      by: 'Trần Trưởng Phòng',
      at: '2026-09-18T09:00:00',
    })
  })

  it('ignores an ordinary edit logged under the same action', () => {
    //  Backend ghi «Yêu cầu chỉnh sửa» dưới action `update` — đúng action mà mọi
    //  lần sửa phiếu bình thường cũng dùng. Soi theo action là bắt nhầm ngay.
    expect(
      extractSealStopReason([entry({ action: 'update', message: 'Cập nhật yêu cầu DD008' })]),
    ).toBeNull()
  })

  it('takes the LATEST block, not the first one in history', () => {
    //  Phiếu bị trả về, sửa, gửi lại rồi bị trả lần nữa: lý do đang có hiệu lực là
    //  lý do mới nhất. Nhật ký trả về mới-nhất-trước.
    const found = extractSealStopReason([
      entry({ id: 3, message: 'Yêu cầu chỉnh sửa — Lý do: Thiếu chữ ký lần hai' }),
      entry({ id: 2, message: 'Cập nhật yêu cầu DD008' }),
      entry({ id: 1, message: 'Yêu cầu chỉnh sửa — Lý do: Sai loại con dấu' }),
    ])

    expect(found?.reason).toBe('Thiếu chữ ký lần hai')
  })

  it('returns null when the blocking entry carries no reason', () => {
    //  Dòng ghi từ bản cũ (trước khi bắt buộc nhập lý do) — không được trả về chuỗi
    //  rỗng, vì màn hình gác bằng chính giá trị này để quyết định có vẽ khung hay không.
    expect(extractSealStopReason([entry({ message: 'Từ chối yêu cầu' })])).toBeNull()
    expect(extractSealStopReason([entry({ message: 'Từ chối yêu cầu — Lý do:    ' })])).toBeNull()
  })

  it('survives an empty, missing or message-less log', () => {
    expect(extractSealStopReason([])).toBeNull()
    expect(extractSealStopReason(undefined)).toBeNull()
    expect(extractSealStopReason([entry({ message: undefined })])).toBeNull()
  })

  it('keeps a reason that itself contains the separator', () => {
    //  Người dùng gõ được dấu gạch dài vào ô lý do; cắt ở dấu ĐẦU TIÊN mới đúng,
    //  cắt ở dấu cuối thì mất nửa câu của họ.
    const found = extractSealStopReason([
      entry({ message: 'Từ chối yêu cầu — Lý do: Sai mẫu — dùng mẫu 02 nhé' }),
    ])

    expect(found?.reason).toBe('Sai mẫu — dùng mẫu 02 nhé')
  })
})
