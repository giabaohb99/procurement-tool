import { describe, expect, it } from 'vitest'

import { GRID_MINUTES } from './room-calendar-grid'
import {
  clampRoomIndex,
  clampToGrid,
  draggedRange,
  isInsideGrid,
  isRealDrag,
  MIN_DURATION_MINUTES,
  minutesFromDeltaX,
  snapMinutes,
} from './room-drag'

const DAY = new Date(2026, 8, 10) // 10/09/2026 — ngày mà lưới đang vẽ
const START = '2026-09-10T09:00:00'
const END = '2026-09-10T10:00:00'

describe('snapMinutes', () => {
  it('hút về mốc 15 phút gần nhất', () => {
    expect(snapMinutes(7)).toBe(0)
    expect(snapMinutes(8)).toBe(15)
    expect(snapMinutes(22)).toBe(15)
    expect(snapMinutes(23)).toBe(30)
  })

  it('kéo ngược cũng hút, không chỉ kéo tới', () => {
    expect(snapMinutes(-8)).toBe(-15)
    expect(Math.abs(snapMinutes(-7))).toBe(0)
  })

  it('không nhân đôi khi đã đúng mốc', () => {
    expect(snapMinutes(30)).toBe(30)
    expect(snapMinutes(0)).toBe(0)
  })
})

describe('minutesFromDeltaX', () => {
  it('kéo hết bề ngang hàng = trọn khung giờ của lưới', () => {
    expect(minutesFromDeltaX(1000, 1000)).toBe(GRID_MINUTES)
  })

  it('bề ngang 0 thì trả 0 chứ không chia cho 0', () => {
    //  Hàng chưa gắn vào DOM (lượt vẽ đầu) có `offsetWidth = 0`. Không chặn thì
    //  ra `Infinity` và cuộc họp nhảy tới năm 275760.
    expect(minutesFromDeltaX(120, 0)).toBe(0)
    expect(Number.isFinite(minutesFromDeltaX(120, 0))).toBe(true)
  })

  it('không kéo thì không đổi giờ', () => {
    expect(minutesFromDeltaX(0, 900)).toBe(0)
  })
})

describe('draggedRange — kéo cả khối', () => {
  it('dời cả hai đầu, giữ nguyên độ dài', () => {
    const out = draggedRange(START, END, 'move', 120)
    expect(out.start).toBe('2026-09-10T11:00')
    expect(out.end).toBe('2026-09-10T12:00')
  })

  it('kéo lùi cũng giữ nguyên độ dài', () => {
    const out = draggedRange(START, END, 'move', -90)
    expect(out.start).toBe('2026-09-10T07:30')
    expect(out.end).toBe('2026-09-10T08:30')
  })
})

describe('draggedRange — kéo mép', () => {
  it('mép phải kéo ra thì chỉ giờ kết thúc đổi', () => {
    const out = draggedRange(START, END, 'resize-end', 30)
    expect(out.start).toBe('2026-09-10T09:00')
    expect(out.end).toBe('2026-09-10T10:30')
  })

  it('mép trái kéo ra thì chỉ giờ bắt đầu đổi', () => {
    const out = draggedRange(START, END, 'resize-start', -30)
    expect(out.start).toBe('2026-09-10T08:30')
    expect(out.end).toBe('2026-09-10T10:00')
  })

  it('mép trái KHÔNG vượt qua mép phải', () => {
    //  Kéo quá tay là chuyện của nửa giây đầu mọi thao tác resize. Không kẹp thì
    //  phiếu gửi lên với `end <= start` và người dùng ăn lỗi đỏ trước khi thả chuột.
    const out = draggedRange(START, END, 'resize-start', 999)
    expect(new Date(out.end).getTime() - new Date(out.start).getTime()).toBe(
      MIN_DURATION_MINUTES * 60000,
    )
  })

  it('mép phải KHÔNG vượt qua mép trái', () => {
    const out = draggedRange(START, END, 'resize-end', -999)
    expect(new Date(out.end).getTime() - new Date(out.start).getTime()).toBe(
      MIN_DURATION_MINUTES * 60000,
    )
  })

  it('cuộc họp 15 phút kéo mép vào trong thì đứng yên, không lật ngược', () => {
    const out = draggedRange(START, '2026-09-10T09:15:00', 'resize-end', -60)
    expect(out.start).toBe('2026-09-10T09:00')
    expect(out.end).toBe('2026-09-10T09:15')
  })
})

describe('isInsideGrid', () => {
  it('trong khung 7:00–20:00 thì nhận', () => {
    expect(isInsideGrid({ start: '2026-09-10T07:00', end: '2026-09-10T20:00' })).toBe(true)
  })

  it('sớm hơn 7:00 thì chặn', () => {
    expect(isInsideGrid({ start: '2026-09-10T06:45', end: '2026-09-10T08:00' })).toBe(false)
  })

  it('muộn hơn 20:00 thì chặn', () => {
    expect(isInsideGrid({ start: '2026-09-10T19:00', end: '2026-09-10T20:15' })).toBe(false)
  })

  it('kéo trôi sang hôm sau thì chặn', () => {
    //  Lưới vẽ MỘT ngày. Thả sang hôm sau là phiếu biến mất khỏi màn ngay sau
    //  khi lưu, và người dùng tưởng mình vừa xóa mất nó.
    expect(isInsideGrid({ start: '2026-09-10T19:00', end: '2026-09-11T09:00' })).toBe(false)
  })

  it('kết thúc sang nửa đêm hôm sau cũng chặn — lưới chỉ vẽ MỘT ngày', () => {
    expect(isInsideGrid({ start: '2026-09-10T19:00', end: '2026-09-11T00:00' })).toBe(false)
  })
})

describe('clampToGrid', () => {
  //  Kéo quá mép là chuyện xảy ra ở MỌI thao tác kéo — người ta đẩy chuột tới
  //  rồi mới lùi lại. Không kẹp thì phiếu lưu ở 21:00 và biến mất khỏi lưới
  //  (lưới chỉ vẽ 7:00–20:00), người dùng tưởng mình vừa xóa mất nó.
  it('kéo vượt mép phải thì dừng ở 20:00, GIỮ NGUYÊN độ dài', () => {
    const out = clampToGrid({ start: '2026-09-10T21:00', end: '2026-09-10T22:00' }, 'move', DAY)
    expect(out).toEqual({ start: '2026-09-10T19:00', end: '2026-09-10T20:00' })
  })

  it('kéo vượt mép trái thì dừng ở 07:00, GIỮ NGUYÊN độ dài', () => {
    const out = clampToGrid({ start: '2026-09-10T05:00', end: '2026-09-10T06:30' }, 'move', DAY)
    expect(out).toEqual({ start: '2026-09-10T07:00', end: '2026-09-10T08:30' })
  })

  it('trong khung thì trả nguyên xi', () => {
    const out = clampToGrid({ start: '2026-09-10T09:00', end: '2026-09-10T10:00' }, 'move', DAY)
    expect(out).toEqual({ start: '2026-09-10T09:00', end: '2026-09-10T10:00' })
  })

  it('cuộc họp dài hơn cả khung lưới thì trả null, không nhét bừa', () => {
    const out = clampToGrid({ start: '2026-09-10T06:00', end: '2026-09-10T23:00' }, 'move', DAY)
    expect(out).toBeNull()
  })

  it('kéo mép phải vượt 20:00 thì CẮT ở 20:00 chứ không dời khối', () => {
    const out = clampToGrid({ start: '2026-09-10T19:00', end: '2026-09-10T23:00' }, 'resize-end', DAY)
    expect(out).toEqual({ start: '2026-09-10T19:00', end: '2026-09-10T20:00' })
  })

  it('kéo mép trái vượt 07:00 thì cắt ở 07:00', () => {
    const out = clampToGrid({ start: '2026-09-10T05:00', end: '2026-09-10T09:00' }, 'resize-start', DAY)
    expect(out).toEqual({ start: '2026-09-10T07:00', end: '2026-09-10T09:00' })
  })

  it('kẹp xong mà ngắn hơn 15 phút thì trả null', () => {
    const out = clampToGrid({ start: '2026-09-10T19:55', end: '2026-09-10T21:00' }, 'resize-end', DAY)
    expect(out).toBeNull()
  })

  it('mọi kết quả kẹp được đều nằm trong lưới', () => {
    for (const hour of [4, 5, 6, 7, 12, 19, 20, 21, 23]) {
      const out = clampToGrid(
        {
          start: `2026-09-10T${String(hour).padStart(2, '0')}:00`,
          end: `2026-09-10T${String(hour + 1).padStart(2, '0')}:00`,
        },
        'move',
        DAY,
      )
      if (out) expect(isInsideGrid(out)).toBe(true)
    }
  })

  //  ⚠️ LỖI THẬT, đo được 04/09/2026. Bản đầu dựng hai mốc kẹp từ ngày của KẾT
  //  QUẢ kéo chứ không từ ngày đang xem, nên cái kẹp trôi theo: hất chuột
  //  5.000px là +4.193 phút ≈ 3 ngày, khối rơi vào 07:23 ngày 08/09 — vẫn nằm
  //  gọn trong 7:00–20:00 *của ngày đó* nên kẹp cho qua. Phiếu lưu sang ngày
  //  khác rồi biến khỏi lưới. Bốn khẳng định dưới đây canh đúng chỗ đó.
  it('hất chuột thật mạnh cũng KHÔNG trôi sang ngày khác', () => {
    const out = clampToGrid({ start: '2026-09-13T07:23', end: '2026-09-13T07:53' }, 'move', DAY)
    expect(out?.start.slice(0, 10)).toBe('2026-09-10')
    expect(out).toEqual({ start: '2026-09-10T19:30', end: '2026-09-10T20:00' })
  })

  it('hất ngược về quá khứ cũng nằm lại đúng ngày đang xem', () => {
    const out = clampToGrid({ start: '2026-09-07T10:00', end: '2026-09-07T11:00' }, 'move', DAY)
    expect(out).toEqual({ start: '2026-09-10T07:00', end: '2026-09-10T08:00' })
  })

  it('kéo mép sang ngày khác cũng bị kéo về ngày đang xem', () => {
    const out = clampToGrid({ start: '2026-09-10T19:00', end: '2026-09-12T09:00' }, 'resize-end', DAY)
    expect(out).toEqual({ start: '2026-09-10T19:00', end: '2026-09-10T20:00' })
  })

  it('kẹp xong luôn cùng một ngày với lưới, thử đủ mọi kiểu hất tay', () => {
    for (const days of [-9, -3, -1, 0, 1, 3, 9]) {
      const start = new Date(2026, 8, 10 + days, 9, 0)
      const end = new Date(2026, 8, 10 + days, 10, 0)
      const iso = (d: Date) =>
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-` +
        `${String(d.getDate()).padStart(2, '0')}T${String(d.getHours()).padStart(2, '0')}:00`
      const out = clampToGrid({ start: iso(start), end: iso(end) }, 'move', DAY)
      expect(out?.start.slice(0, 10)).toBe('2026-09-10')
    }
  })
})

describe('clampRoomIndex', () => {
  it('kéo lên quá hàng đầu thì dừng ở hàng đầu', () => {
    expect(clampRoomIndex(-3, 5)).toBe(0)
  })

  it('kéo xuống quá hàng cuối thì dừng ở hàng cuối', () => {
    expect(clampRoomIndex(9, 5)).toBe(4)
  })

  it('danh sách rỗng không đẻ ra chỉ số âm', () => {
    expect(clampRoomIndex(2, 0)).toBe(0)
  })
})

describe('isRealDrag', () => {
  it('rung tay vài pixel vẫn là một cú BẤM', () => {
    //  Không có ngưỡng này thì mọi cú bấm mở phiếu đều biến thành một lượt dời
    //  lịch 0 phút — và mỗi lần bấm là một lệnh ghi xuống máy chủ.
    expect(isRealDrag(3, 2)).toBe(false)
  })

  it('kéo ngang quá ngưỡng là kéo thật', () => {
    expect(isRealDrag(12, 0)).toBe(true)
  })

  it('kéo dọc quá ngưỡng cũng là kéo thật — đổi phòng', () => {
    expect(isRealDrag(0, 40)).toBe(true)
  })
})
