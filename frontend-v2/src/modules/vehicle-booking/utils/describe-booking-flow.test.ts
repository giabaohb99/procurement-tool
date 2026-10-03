import { describe, expect, it } from 'vitest'

import { describeBookingFlow } from './describe-booking-flow'

describe('describeBookingFlow', () => {
  it('says nothing when the ticket never entered the approval engine', () => {
    expect(describeBookingFlow(null)).toBeNull()
    expect(describeBookingFlow(undefined)).toBeNull()
  })

  it('names the configured flow', () => {
    expect(describeBookingFlow({ flow_id: 4, flow_name: 'Đặt xe 2 lớp', flow_version: 1 })).toBe(
      'Theo luồng «Đặt xe 2 lớp»',
    )
  })

  it('adds the version once the flow has been edited', () => {
    expect(describeBookingFlow({ flow_id: 4, flow_name: 'Đặt xe 2 lớp', flow_version: 3 })).toBe(
      'Theo luồng «Đặt xe 2 lớp» (bản 3)',
    )
  })

  it('marks a ticket copied from the old app instead of pointing at a flow that does not exist', () => {
    //  Phiếu nạp từ app cũ có phiên flow_id = 0 — không có luồng nào mang số đó
    //  ở màn cấu hình, ghi «Luồng #0» là bảo người đọc đi tìm một thứ không có.
    expect(
      describeBookingFlow({ flow_id: 0, flow_name: 'Quy trình đặt xe - 003', flow_version: 1 }),
    ).toBe('Theo quy trình bên app cũ «Quy trình đặt xe - 003»')
    expect(describeBookingFlow({ flow_id: 0, flow_name: '', flow_version: 1 })).toBe(
      'Theo quy trình bên app cũ',
    )
  })

  it('falls back to the flow id when the snapshot lost its name', () => {
    expect(describeBookingFlow({ flow_id: 9, flow_name: '  ', flow_version: 1 })).toBe(
      'Theo luồng «Luồng #9»',
    )
  })
})
