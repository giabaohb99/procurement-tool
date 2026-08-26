import { describe, expect, it } from 'vitest'

import { engineRowStatus } from './engine-row-status'

describe('engineRowStatus', () => {
  it('tắt công tắc = đi đường duyệt cũ', () => {
    expect(engineRowStatus(0, false).label).toBe('Đường duyệt cũ')
    expect(engineRowStatus(3, false).label).toBe('Đường duyệt cũ')
  })

  it('tắt mà đã khai luồng thì nói rõ luồng đang nằm im', () => {
    expect(engineRowStatus(3, false).hint).toMatch(/Đã khai 3 luồng nhưng chưa bật/)
  })

  it('bật nhưng CHƯA khai luồng nào thì không được báo là đang chạy', () => {
    //  `bat_dau()` không tìm được luồng thì trả None và phiếu đi đường cũ.
    //  Báo "đang chạy" ở đây là để người quản trị ngồi chờ một thứ không xảy ra.
    const status = engineRowStatus(0, true)

    expect(status.tone).toBe('idle')
    expect(status.label).toBe('Bật nhưng chưa có luồng')
  })

  it('bật + có luồng mới là đang chạy bộ máy mới', () => {
    const status = engineRowStatus(2, true)

    expect(status.tone).toBe('running')
    expect(status.hint).toMatch(/2 luồng/)
  })
})
