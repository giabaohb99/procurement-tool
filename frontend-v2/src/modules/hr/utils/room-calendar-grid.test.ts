import { describe, expect, it } from 'vitest'

import {
  blockingOnly,
  buildDayBlocks,
  DAY_END_HOUR,
  DAY_START_HOUR,
  buildRowBars,
  dimBands,
  dimBandsX,
  formatSlotHour,
  halfHourSlots,
  HOUR_HEIGHT,
  hourLabels,
  isOnDay,
  LUNCH_START_HOUR,
  nowLineLeft,
  nowLineTop,
  rowHeightFor,
  WORK_START_HOUR,
} from './room-calendar-grid'
import { ROOM_BOOKING_STATUS, type RoomBooking } from '../types/room'

const DAY = new Date(2026, 8, 10) // 10/09/2026

function booking(overrides: Partial<RoomBooking> = {}): RoomBooking {
  return {
    id: 1,
    code: 'PH001',
    room_id: 1,
    room_name: 'Phòng 301',
    room_code: 'P301',
    company_id: 1,
    department_id: 1,
    requester_employee_id: 1,
    requester_name: 'Nguyễn Văn An',
    title: 'Họp giao ban',
    purpose: '',
    start_at: '2026-09-10T09:00:00',
    end_at: '2026-09-10T10:00:00',
    attendee_count: 0,
    status: ROOM_BOOKING_STATUS.APPROVED,
    status_label: 'Đã duyệt',
    approval_instance_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

describe('blockingOnly', () => {
  it('chỉ giữ phiếu ĐANG GIỮ phòng — chờ duyệt và đã duyệt', () => {
    //  ⚠️ Vẽ nháp/hủy/từ chối lên lịch là người xem tưởng phòng đã kín rồi đi
    //  đặt phòng khác, trong khi phòng đang trống.
    const rows = [
      booking({ id: 1, status: ROOM_BOOKING_STATUS.DRAFT }),
      booking({ id: 2, status: ROOM_BOOKING_STATUS.PENDING }),
      booking({ id: 3, status: ROOM_BOOKING_STATUS.APPROVED }),
      booking({ id: 4, status: ROOM_BOOKING_STATUS.REJECTED }),
      booking({ id: 5, status: ROOM_BOOKING_STATUS.CANCELLED }),
      booking({ id: 6, status: ROOM_BOOKING_STATUS.RETURNED }),
    ]
    expect(blockingOnly(rows).map((b) => b.id)).toEqual([2, 3])
  })
})

describe('isOnDay', () => {
  it('nhận phiếu trong đúng ngày', () => {
    expect(isOnDay(booking(), DAY)).toBe(true)
  })

  it('bỏ phiếu của ngày khác', () => {
    expect(isOnDay(booking({ start_at: '2026-09-11T09:00:00', end_at: '2026-09-11T10:00:00' }), DAY))
      .toBe(false)
  })

  it('phiếu VẮT QUA nửa đêm hiện ở CẢ HAI ngày', () => {
    const acrossMidnight = booking({ start_at: '2026-09-10T22:00:00', end_at: '2026-09-11T01:00:00' })
    expect(isOnDay(acrossMidnight, DAY)).toBe(true)
    expect(isOnDay(acrossMidnight, new Date(2026, 8, 11))).toBe(true)
  })

  it('kết thúc ĐÚNG lúc nửa đêm thì không tính sang hôm sau', () => {
    //  23:00–00:00 là cuộc họp của hôm nay, không phải của ngày mai.
    const endsAtMidnight = booking({ start_at: '2026-09-10T23:00:00', end_at: '2026-09-11T00:00:00' })
    expect(isOnDay(endsAtMidnight, new Date(2026, 8, 11))).toBe(false)
  })
})

describe('buildDayBlocks', () => {
  it('đặt khối đúng vị trí theo giờ', () => {
    const [block] = buildDayBlocks([booking()], DAY)
    //  9:00 cách mốc 7:00 hai tiếng.
    expect(block.top).toBe(2 * HOUR_HEIGHT)
    expect(block.height).toBe(HOUR_HEIGHT)
    expect(block.widthPercent).toBe(100)
  })

  it('cuộc họp NGẮN vẫn cao tối thiểu 24px để đọc được chữ', () => {
    const [block] = buildDayBlocks(
      [booking({ start_at: '2026-09-10T09:00:00', end_at: '2026-09-10T09:10:00' })],
      DAY,
    )
    expect(block.height).toBe(24)
  })

  it('hai phiếu CHỒNG GIỜ xếp cạnh nhau, mỗi khối một nửa cột', () => {
    //  Chồng đè lên nhau thì cái dưới biến mất và người xem không biết là có nó.
    const blocks = buildDayBlocks(
      [
        booking({ id: 1, start_at: '2026-09-10T09:00:00', end_at: '2026-09-10T10:00:00' }),
        booking({ id: 2, start_at: '2026-09-10T09:30:00', end_at: '2026-09-10T10:30:00' }),
      ],
      DAY,
    )
    expect(blocks).toHaveLength(2)
    expect(blocks.every((b) => b.widthPercent === 50)).toBe(true)
    expect(blocks.map((b) => b.leftPercent)).toEqual([0, 50])
  })

  it('hai ca NỐI TIẾP nhau vẫn chiếm trọn bề ngang', () => {
    //  9-10h và 10-11h không chồng nhau; chia đôi cột ở đây là bóp hình vô cớ.
    const blocks = buildDayBlocks(
      [
        booking({ id: 1, start_at: '2026-09-10T09:00:00', end_at: '2026-09-10T10:00:00' }),
        booking({ id: 2, start_at: '2026-09-10T10:00:00', end_at: '2026-09-10T11:00:00' }),
      ],
      DAY,
    )
    expect(blocks.every((b) => b.widthPercent === 100)).toBe(true)
  })

  it('họp SỚM hơn giờ mở lưới thì kẹp vào mép trên, không trồi ra ngoài', () => {
    const [block] = buildDayBlocks(
      [booking({ start_at: '2026-09-10T05:00:00', end_at: '2026-09-10T08:00:00' })],
      DAY,
    )
    expect(block.top).toBe(0)
    expect(block.height).toBe(HOUR_HEIGHT) // chỉ phần 7:00–8:00 nằm trong lưới
  })

  it('họp MUỘN hơn giờ đóng lưới thì cắt ở mép dưới', () => {
    const [block] = buildDayBlocks(
      [booking({ start_at: '2026-09-10T19:00:00', end_at: '2026-09-10T23:00:00' })],
      DAY,
    )
    expect(block.top + block.height).toBe((DAY_END_HOUR - DAY_START_HOUR) * HOUR_HEIGHT)
  })

  it('danh sách rỗng thì trả rỗng, không nổ', () => {
    expect(buildDayBlocks([], DAY)).toEqual([])
  })
})

describe('hourLabels', () => {
  it('chạy từ giờ mở tới giờ đóng, có đệm số 0', () => {
    const labels = hourLabels()
    expect(labels[0]).toBe('07:00')
    expect(labels[labels.length - 1]).toBe('20:00')
    expect(labels).toHaveLength(DAY_END_HOUR - DAY_START_HOUR + 1)
  })
})


describe('nowLineTop', () => {
  it('đặt vạch «bây giờ» đúng vị trí khi đang xem HÔM NAY', () => {
    const top = nowLineTop(DAY, new Date(2026, 8, 10, 13, 40))
    //  13:40 cách mốc 7:00 đúng 6 giờ 40 phút.
    expect(top).toBeCloseTo((6 + 40 / 60) * HOUR_HEIGHT, 5)
  })

  it('xem NGÀY KHÁC thì không vẽ vạch — nếu không, mọi ngày đều có một vạch đỏ vô nghĩa', () => {
    expect(nowLineTop(new Date(2026, 8, 11), new Date(2026, 8, 10, 13, 40))).toBeNull()
  })

  it('giờ nằm NGOÀI khung lưới thì không vẽ', () => {
    //  5 giờ sáng: vẽ ra là vạch nằm đè lên đầu cột.
    expect(nowLineTop(DAY, new Date(2026, 8, 10, 5, 0))).toBeNull()
    expect(nowLineTop(DAY, new Date(2026, 8, 10, 22, 0))).toBeNull()
  })
})

describe('dimBands', () => {
  it('tô mờ ba vùng: trước giờ làm, nghỉ trưa, sau giờ làm', () => {
    const bands = dimBands()
    expect(bands).toHaveLength(3)
    expect(bands[0].top).toBe(0)
    expect(bands[0].height).toBe((WORK_START_HOUR - DAY_START_HOUR) * HOUR_HEIGHT)
    expect(bands[1].top).toBe((LUNCH_START_HOUR - DAY_START_HOUR) * HOUR_HEIGHT)
  })

  it('vùng cuối kết thúc ĐÚNG mép dưới lưới, không tràn ra ngoài', () => {
    const last = dimBands()[2]
    expect(last.top + last.height).toBe((DAY_END_HOUR - DAY_START_HOUR) * HOUR_HEIGHT)
  })
})

describe('halfHourSlots + formatSlotHour', () => {
  it('chia NỬA TIẾNG một ô — họp 30 phút là chuyện thường', () => {
    const slots = halfHourSlots()
    expect(slots[0]).toBe(DAY_START_HOUR)
    expect(slots[1]).toBe(DAY_START_HOUR + 0.5)
    expect(slots).toHaveLength((DAY_END_HOUR - DAY_START_HOUR) * 2)
  })

  it('ô cuối KHÔNG chạm giờ đóng lưới — đặt lúc 20:00 là đặt ngoài lưới', () => {
    expect(Math.max(...halfHourSlots())).toBe(DAY_END_HOUR - 0.5)
  })

  it('đổi giờ thập phân thành nhãn đọc được', () => {
    //  ⚠️ Ghép thẳng `9.5` vào chuỗi giờ thì ra `9.5:00` — một giờ không tồn tại,
    //  và ô `datetime-local` nhận nó xong bỏ trống trơn.
    expect(formatSlotHour(9.5)).toBe('09:30')
    expect(formatSlotHour(7)).toBe('07:00')
    expect(formatSlotHour(19.5)).toBe('19:30')
  })
})


/**
 * ── TRỤC NGANG (mỗi phòng một hàng) ─────────────────────────────────────────
 * Tính bằng PHẦN TRĂM để lưới tự lấp đầy bề ngang khung — bản px cũ khoá ở
 * 13 × 84px nên màn 2.289px chừa một nghìn pixel trắng bên phải.
 */
describe('buildRowBars', () => {
  it('đặt thanh đúng vị trí theo % bề ngang lưới', () => {
    const [bar] = buildRowBars([booking()], DAY)
    //  9:00–10:00 trên lưới 7:00–20:00 (780 phút): bắt đầu ở 120/780, dài 60/780.
    expect(bar.leftPercent).toBeCloseTo((120 / 780) * 100, 5)
    expect(bar.widthPercent).toBeCloseTo((60 / 780) * 100, 5)
    expect(bar.heightPercent).toBe(100)
  })

  it('cuộc họp NGẮN vẫn rộng tối thiểu 1.5% — hẹp hơn thì mất cả viền', () => {
    const [bar] = buildRowBars(
      [booking({ start_at: '2026-09-10T09:00:00', end_at: '2026-09-10T09:10:00' })],
      DAY,
    )
    expect(bar.widthPercent).toBe(1.5)
  })

  it('hai phiếu CHỒNG GIỜ chia đôi chiều cao hàng, không đè lên nhau', () => {
    const bars = buildRowBars(
      [
        booking({ id: 1, start_at: '2026-09-10T09:00:00', end_at: '2026-09-10T10:00:00' }),
        booking({ id: 2, start_at: '2026-09-10T09:30:00', end_at: '2026-09-10T10:30:00' }),
      ],
      DAY,
    )
    expect(bars.every((b) => b.heightPercent === 50)).toBe(true)
    expect(bars.map((b) => b.topPercent)).toEqual([0, 50])
  })

  it('bỏ phiếu KHÔNG giữ phòng, y như bản trục dọc', () => {
    expect(buildRowBars([booking({ status: ROOM_BOOKING_STATUS.CANCELLED })], DAY)).toEqual([])
  })
})

describe('rowHeightFor', () => {
  it('ÍT phòng thì hàng DÀY — bốn phòng mà hàng mỏng là lưới cao 210px giữa khung rỗng', () => {
    expect(rowHeightFor(4)).toBeGreaterThan(rowHeightFor(20))
    expect(rowHeightFor(1)).toBe(rowHeightFor(4))
  })

  it('NHIỀU phòng thì hàng MỎNG để lọt nhiều dòng vào một màn', () => {
    expect(rowHeightFor(20)).toBeLessThanOrEqual(48)
    //  Không mỏng hơn nữa: dưới 48px thì hai dòng chữ trong khối phiếu bị cắt.
    expect(rowHeightFor(200)).toBe(rowHeightFor(20))
  })
})

describe('dimBandsX + nowLineLeft', () => {
  it('ba vùng mờ phủ đúng phần ngoài giờ làm, tính bằng %', () => {
    const bands = dimBandsX()
    expect(bands).toHaveLength(3)
    expect(bands[0].leftPercent).toBe(0)
    //  7:00–8:00 là 60/780 bề ngang.
    expect(bands[0].widthPercent).toBeCloseTo((60 / 780) * 100, 5)
  })

  it('vùng cuối chạm ĐÚNG mép phải, không tràn ra ngoài', () => {
    const last = dimBandsX()[2]
    expect(last.leftPercent + last.widthPercent).toBeCloseTo(100, 5)
  })

  it('vạch «bây giờ» đặt theo % và biến mất ở ngày khác', () => {
    expect(nowLineLeft(DAY, new Date(2026, 8, 10, 13, 40))).toBeCloseTo((400 / 780) * 100, 5)
    expect(nowLineLeft(new Date(2026, 8, 11), new Date(2026, 8, 10, 13, 40))).toBeNull()
  })
})
