import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import {
  barGeometry,
  buildTimeline,
  daysBetween,
  groupHeader,
  isWeekend,
  shiftDate,
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
    status: WORK_TASK_STATUS.OPEN, start_date: '', due_date: '', sort_order: 0,
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

  it('danh sách rỗng vẫn ra dải hợp lệ quanh hôm nay, không nổ', () => {
    const timeline = buildTimeline([], 'day', '2026-08-28')
    expect(timeline.days.length).toBeGreaterThanOrEqual(21)
    expect(timeline.days).toContain('2026-08-28')
  })

  it('việc không có ngày nào không kéo dài dải', () => {
    const chiHomNay = buildTimeline([], 'day', '2026-08-28')
    const themViecRong = buildTimeline([task(), task()], 'day', '2026-08-28')
    expect(themViecRong.days).toEqual(chiHomNay.days)
  })

  it('dải ngắn được kéo lên tối thiểu 21 ngày', () => {
    const timeline = buildTimeline([task({ due_date: '2026-08-28' })], 'day', '2026-08-28')
    expect(timeline.days.length).toBe(21)
  })

  it('mức phóng chỉ đổi bề rộng, KHÔNG đổi số ngày', () => {
    const ngay = buildTimeline([task({ due_date: '2026-09-30' })], 'day', '2026-08-28')
    const thang = buildTimeline([task({ due_date: '2026-09-30' })], 'month', '2026-08-28')
    expect(thang.days).toEqual(ngay.days)
    expect(thang.totalWidth).toBeLessThan(ngay.totalWidth)
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

describe('groupHeader', () => {
  it('gom theo tháng ở mức Ngày, theo năm ở mức Tháng', () => {
    const timeline = buildTimeline([task({ due_date: '2026-10-15' })], 'day', '2026-08-28')
    const theoThang = groupHeader(timeline, 'day')
    expect(theoThang.map((o) => o.key)).toEqual(['2026-08', '2026-09', '2026-10'])
    expect(theoThang[0].label).toBe('Tháng 8/2026')

    expect(groupHeader(timeline, 'month').map((o) => o.label)).toEqual(['Năm 2026'])
  })

  it('tổng bề rộng các ô tiêu đề bằng đúng bề rộng dải', () => {
    //  Lệch một pixel là lưới ngày và thanh trượt khỏi nhau ở cuối biểu đồ.
    const timeline = buildTimeline([task({ due_date: '2026-12-31' })], 'week', '2026-08-28')
    const tong = groupHeader(timeline, 'week').reduce((s, o) => s + o.width, 0)
    expect(tong).toBe(timeline.totalWidth)
  })
})

describe('isWeekend', () => {
  it('nhận đúng thứ Bảy và Chủ nhật', () => {
    expect(isWeekend('2026-08-29')).toBe(true) // thứ Bảy
    expect(isWeekend('2026-08-30')).toBe(true) // Chủ nhật
    expect(isWeekend('2026-08-28')).toBe(false) // thứ Sáu
  })
})
