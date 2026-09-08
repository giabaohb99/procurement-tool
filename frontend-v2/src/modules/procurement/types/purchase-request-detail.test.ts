import { describe, expect, it } from 'vitest'

import { isClosed, isDispatched, isEditable } from './purchase-request-detail'

/**
 * bao-CR-315 — lỗi thật đã xảy ra: màn YCMH bày `request_date` ra dưới nhãn
 * "Ngày tiếp nhận" ngay từ lúc phiếu còn là nháp, nên người lập tưởng thu mua đã
 * nhận việc. Chừng nào phiếu chưa qua bước điều phối thì cột đó chỉ là ngày lập
 * phiếu. Đừng xóa bộ test này khi thêm trạng thái mới — thêm dòng vào đây.
 */
describe('isDispatched', () => {
  it('rejects every status before dispatch, including the approved step', () => {
    for (const status of ['draft', 'submitted', 'approved', 'rejected', 'cancelled']) {
      expect(isDispatched(status)).toBe(false)
    }
  })

  it('accepts dispatch and every status after it', () => {
    for (const status of ['dispatched', 'processing', 'purchasing', 'purchased', 'completed', 'done']) {
      expect(isDispatched(status)).toBe(true)
    }
  })

  it('treats unknown or blank status as not dispatched', () => {
    expect(isDispatched('')).toBe(false)
    expect(isDispatched('DISPATCHED')).toBe(false)
    expect(isDispatched(' dispatched ')).toBe(false)
    expect(isDispatched('trang_thai_la')).toBe(false)
  })

  /**
   * Phiếu đã hoàn thành thì vừa "đã tiếp nhận" vừa "đã chốt" — hai luật soi hai
   * việc khác nhau, đảo một bên là hỏng bên kia.
   */
  it('overlaps with isClosed only on the finished statuses', () => {
    expect(isDispatched('completed') && isClosed('completed')).toBe(true)
    expect(isDispatched('done') && isClosed('done')).toBe(true)
    expect(isClosed('cancelled')).toBe(true)
    expect(isDispatched('cancelled')).toBe(false)
  })

  /** Phiếu còn sửa được thì chắc chắn chưa ai tiếp nhận. */
  it('never overlaps with isEditable', () => {
    for (const status of ['draft', 'rejected']) {
      expect(isEditable(status)).toBe(true)
      expect(isDispatched(status)).toBe(false)
    }
  })
})
