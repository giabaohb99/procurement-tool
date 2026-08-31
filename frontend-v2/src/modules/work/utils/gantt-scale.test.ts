import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import { WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import {
  barGeometry,
  buildHeader,
  buildTimeline,
  daysBetween,
  isoWeek,
  isWeekend,
  milestoneCenter,
  shiftDate,
  todayLeft,
} from './gantt-scale'

/**
 * Thang thời gian của Gantt. Sai một ngày ở đây là mọi thanh trên biểu đồ lệch
 * một ô — mà lệch đều nên nhìn vẫn "có vẻ đúng", chỉ khi đối chiếu với hạn thật
 * mới lòi ra. Vitest ghim múi giờ `Asia/Ho_Chi_Minh`.
 */

function task(patch: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 1, list_id: 1, section_id: 1, parent_id: null,
    title: 'Việc', description: '',
    status: WORK_TASK_STATUS.OPEN, kind: WORK_TASK_KIND.TASK,
    start_date: '', due_date: '', sort_order: 0,
    creator_employee_id: 0, completed_at: null, completed_by: null,
    created_at: '2026-08-01T00:00:00', updated_at: '2026-08-01T00:00:00',
    assignees: [], labels: [],
    subtask_done: 0, subtask_total: 0, comment_count: 0,
    ...patch,
  }
}

describe('shiftDate', () => {
  it('cộng ngày qua ranh giới tháng và năm', () => {
    expect(shiftDate('2026-08-31', 1)).toBe('2026-09-01')
    expect(shiftDate('2026-12-31', 1)).toBe('2027-01-01')
    expect(shiftDate('2026-03-01', -1)).toBe('2026-02-28')
  })

  it('biết năm nhuận — 2028 có 29/02', () => {
    expect(shiftDate('2028-02-28', 1)).toBe('2028-02-29')
  })
})

describe('daysBetween', () => {
  it('đếm đúng qua ranh giới tháng, và âm khi lùi', () => {
    expect(daysBetween('2026-08-28', '2026-09-02')).toBe(5)
    expect(daysBetween('2026-09-02', '2026-08-28')).toBe(-5)
    expect(daysBetween('2026-08-28', '2026-08-28')).toBe(0)
  })

  it('không lệch khi hai ngày cách nhau nhiều năm', () => {
    expect(daysBetween('2026-01-01', '2027-01-01')).toBe(365)
  })
})

describe('buildTimeline', () => {
  it('dải luôn chứa HÔM NAY dù mọi việc đều nằm ở quá khứ', () => {
    //  Thiếu vạch hôm nay thì biểu đồ mất mốc đọc.
    const timeline = buildTimeline([task({ due_date: '2026-01-10' })], 'day', '2026-08-28')
    expect(timeline.start <= '2026-01-10').toBe(true)
    expect(timeline.end >= '2026-08-28').toBe(true)
  })

  it('dự án TRỐNG vẫn có sẵn hai năm: 01/01 năm nay tới 31/12 năm sau', () => {
    //  Khách đối chiếu Lark 31/08/2026: mở Gantt của một dự án mới toanh là trục
    //  đã sẵn hai năm. Bám sát dữ liệu thì dự án trống ra một dải vài chục ngày,
    //  không đặt lịch cho quý sau được vì quý sau không tồn tại trên trục.
    const timeline = buildTimeline([], 'day', '2026-08-28')
    expect(timeline.start).toBe('2026-01-01')
    expect(timeline.end).toBe('2027-12-31')
    expect(timeline.days).toContain('2026-08-28')
  })

  it('việc không có ngày nào không kéo dài dải', () => {
    const chiHomNay = buildTimeline([], 'day', '2026-08-28')
    const themViecRong = buildTimeline([task(), task()], 'day', '2026-08-28')
    expect(themViecRong.days).toEqual(chiHomNay.days)
  })

  it('việc nằm NGOÀI khung hai năm vẫn kéo dải ra, không bị cắt mất', () => {
    //  Mất một việc khỏi biểu đồ còn tệ hơn một cái trục dài: khung hai năm là
    //  SÀN, không phải trần.
    const timeline = buildTimeline([task({ due_date: '2029-06-15' })], 'day', '2026-08-28')
    expect(timeline.start).toBe('2026-01-01')
    expect(timeline.end >= '2029-06-15').toBe(true)
  })

  it('việc ở QUÁ KHỨ trước năm nay cũng kéo dải lùi lại', () => {
    const timeline = buildTimeline([task({ start_date: '2024-03-10' })], 'day', '2026-08-28')
    expect(timeline.start <= '2024-03-10').toBe(true)
    expect(timeline.end).toBe('2027-12-31')
  })

  it('mức phóng xa hơn thì hẹp lại theo pixel nhưng KHÔNG cắt mất ngày nào', () => {
    //  Mức Tuần/Tháng BO dải về trọn tuần / trọn tháng (`snapEdges`) nên số ngày
    //  nhiều hơn mức Ngày — đó là chủ ý, để ô đầu và ô cuối không cụt. Điều phải
    //  giữ là dải rộng ra chứ không bao giờ hụt đi: hụt một ngày là một việc
    //  biến mất khỏi biểu đồ.
    const ngay = buildTimeline([task({ due_date: '2026-09-30' })], 'day', '2026-08-28')
    const thang = buildTimeline([task({ due_date: '2026-09-30' })], 'month', '2026-08-28')

    expect(thang.start <= ngay.start).toBe(true)
    expect(thang.end >= ngay.end).toBe(true)
    expect(thang.totalWidth).toBeLessThan(ngay.totalWidth)
  })

  it('mức Tuần luôn bắt đầu vào THỨ HAI và kết thúc CHỦ NHẬT', () => {
    const tuan = buildTimeline([task({ due_date: '2026-09-30' })], 'week', '2026-08-28')
    expect(tuan.days.length % 7).toBe(0)
    expect(new Date(`${tuan.start}T00:00:00`).getDay()).toBe(1)
    expect(new Date(`${tuan.end}T00:00:00`).getDay()).toBe(0)
  })

  it('mức Tháng bắt đầu mồng 1 và kết thúc ngày cuối tháng, kể cả tháng 2', () => {
    //  Hạn phải rơi RA NGOÀI khung hai năm của `homNay` thì mép cuối mới do việc
    //  quyết định — trong khung thì mép cuối luôn là 31/12, không kiểm được gì.
    const thang = buildTimeline([task({ start_date: '2028-02-10', due_date: '2028-02-20' })], 'month', '2026-05-01')
    expect(thang.start.endsWith('-01')).toBe(true)
    //  2028 nhuận: tháng 2 có 29 ngày. Tra bảng 30/31 bằng tay là chỗ hay quên.
    expect(thang.end).toBe('2028-02-29')
  })
})

describe('barGeometry', () => {
  const timeline = buildTimeline([task({ due_date: '2026-09-30' })], 'day', '2026-08-28')

  it('việc chưa có ngày nào thì KHÔNG vẽ thanh', () => {
    expect(barGeometry(task(), timeline)).toBeNull()
  })

  it('chỉ có hạn thì vẽ đúng MỘT ngày, không bịa độ dài', () => {
    const bar = barGeometry(task({ due_date: '2026-09-01' }), timeline)
    expect(bar?.width).toBe(timeline.dayWidth)
  })

  it('có cả hai ngày thì bề rộng tính CẢ ngày đầu lẫn ngày cuối', () => {
    const bar = barGeometry(
      task({ start_date: '2026-09-01', due_date: '2026-09-03' }),
      timeline,
    )
    expect(bar?.width).toBe(3 * timeline.dayWidth)
  })

  it('ngày bắt đầu SAU hạn (dữ liệu ngược) vẫn ra thanh dương, không biến mất', () => {
    const bar = barGeometry(
      task({ start_date: '2026-09-05', due_date: '2026-09-01' }),
      timeline,
    )
    expect(bar).not.toBeNull()
    expect(bar?.width).toBe(5 * timeline.dayWidth)
  })
})

describe('buildHeader', () => {
  it('mức Ngày: hàng trên gom theo THÁNG, hàng dưới là từng ngày kèm thứ', () => {
    const timeline = buildTimeline([task({ due_date: '2026-10-15' })], 'day', '2026-08-28')
    const header = buildHeader(timeline, 'day', '2026-08-28')

    //  Dải luôn là khung hai năm (01/01 năm nay → 31/12 năm sau) nên hàng trên
    //  đúng 24 ô tháng, ô đầu là tháng 1 năm nay.
    expect(header.top).toHaveLength(24)
    expect(header.top[0].key).toBe('2026-01')
    expect(header.top[0].label).toBe('Tháng 1/2026')
    expect(header.top.at(-1)?.key).toBe('2027-12')
    expect(header.bottom).toHaveLength(timeline.days.length)
    expect(header.bottom[0].sub).toBeTruthy()
  })

  it('mức Tuần: hàng trên là NĂM, hàng dưới là tuần ISO, mỗi ô đúng 7 ngày', () => {
    const timeline = buildTimeline([task({ due_date: '2026-10-15' })], 'week', '2026-08-28')
    const header = buildHeader(timeline, 'week', '2026-08-28')

    //  Khung hai năm bo về thứ Hai — Chủ nhật nên tràn sang cuối 2025 và đầu
    //  2028; hàng trên vì thế có bốn nhãn năm, không phải một.
    expect(header.top.map((o) => o.label)).toEqual(['2025', '2026', '2027', '2028'])
    expect(header.bottom[0].label).toMatch(/^T\.\d+$/)
    //  Dải mức Tuần được bo về thứ Hai — Chủ nhật, nên KHÔNG ô nào cụt. Ô cụt là
    //  dấu hiệu `snapEdges` hỏng, mà nhìn thì chỉ thấy "lưới hơi lệch".
    const week = 7 * timeline.dayWidth
    expect(header.bottom.every((o) => o.width === week)).toBe(true)
  })

  it('mức Tháng: hàng dưới là từng tháng, không ô nào cụt', () => {
    const timeline = buildTimeline([task({ due_date: '2027-03-15' })], 'month', '2026-08-28')
    const header = buildHeader(timeline, 'month', '2026-08-28')

    //  Mức Tháng bo về mồng 1 — ngày cuối tháng, mà khung đã sẵn 01/01 và 31/12
    //  nên không tràn năm: đúng hai nhãn năm.
    expect(header.top.map((o) => o.label)).toEqual(['2026', '2027'])
    expect(header.bottom[0].label).toMatch(/^Th \d+$/)
    //  Tháng đầu và tháng cuối phải TRỌN vẹn: 28…31 ngày, không phải vài ngày lẻ.
    const days = header.bottom.map((o) => o.width / timeline.dayWidth)
    expect(Math.min(...days)).toBeGreaterThanOrEqual(28)
  })

  it('tổng bề rộng CẢ HAI hàng tiêu đề bằng đúng bề rộng dải', () => {
    //  Lệch một pixel là lưới ngày và thanh trượt khỏi nhau ở cuối biểu đồ.
    for (const zoom of ['day', 'week', 'month'] as const) {
      const timeline = buildTimeline([task({ due_date: '2026-12-31' })], zoom, '2026-08-28')
      const header = buildHeader(timeline, zoom, '2026-08-28')
      expect(header.top.reduce((s, o) => s + o.width, 0)).toBe(timeline.totalWidth)
      expect(header.bottom.reduce((s, o) => s + o.width, 0)).toBe(timeline.totalWidth)
    }
  })

  it('dải vắt qua hai năm không gộp hai tháng 01 khác năm vào một ô', () => {
    //  Gom bằng `Map` theo khóa sẽ dính đúng lỗi này: hai quãng cách nhau cả năm
    //  chung khóa → một ô rộng bằng cả biểu đồ.
    const timeline = buildTimeline(
      [task({ start_date: '2026-01-05', due_date: '2028-01-05' })],
      'month',
      '2026-08-28',
    )
    const header = buildHeader(timeline, 'month', '2026-08-28')
    const thangMot = header.bottom.filter((o) => o.label === 'Th 1')
    expect(thangMot).toHaveLength(3)
  })
})

describe('isoWeek', () => {
  it('theo chuẩn ISO chứ không đếm từ 01/01', () => {
    //  01/01/2027 là thứ Sáu → vẫn thuộc tuần 53 của 2026 theo ISO.
    expect(isoWeek('2027-01-01')).toBe(53)
    expect(isoWeek('2026-01-01')).toBe(1)
    expect(isoWeek('2026-09-07')).toBe(37)
  })
})

describe('milestoneCenter và todayLeft', () => {
  const timeline = buildTimeline([task({ due_date: '2026-09-30' })], 'day', '2026-08-28')

  it('cột mốc rơi vào GIỮA ô ngày của nó, không phải mép ô', () => {
    const center = milestoneCenter(task({ due_date: '2026-09-01' }), timeline)
    const left = daysBetween(timeline.start, '2026-09-01') * timeline.dayWidth
    expect(center).toBe(left + timeline.dayWidth / 2)
  })

  it('cột mốc chưa có ngày thì không có chỗ mà vẽ', () => {
    expect(milestoneCenter(task(), timeline)).toBeNull()
  })

  it('hôm nay ngoài dải thì KHÔNG vẽ vạch', () => {
    expect(todayLeft(timeline, '2030-01-01')).toBeNull()
    expect(todayLeft(timeline, '2026-08-28')).not.toBeNull()
  })
})

describe('isWeekend', () => {
  it('nhận đúng thứ Bảy và Chủ nhật', () => {
    expect(isWeekend('2026-08-29')).toBe(true) // thứ Bảy
    expect(isWeekend('2026-08-30')).toBe(true) // Chủ nhật
    expect(isWeekend('2026-08-28')).toBe(false) // thứ Sáu
  })
})
