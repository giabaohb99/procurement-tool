import { describe, expect, it } from 'vitest'

import type { WorkActivity } from '../types/activity'
import { groupActivitiesByDay } from './group-activities-by-day'

/**
 * Gom dòng hoạt động theo ngày.
 *
 * Hai chỗ hỏng ÂM THẦM, cả hai đều chỉ lộ ra ở đúng vài giờ trong ngày:
 * - Backend trả mốc UTC KHÔNG hậu tố `Z`. Quên bù múi giờ thì một dòng lúc 1h
 *   sáng giờ Việt Nam bị xếp về "Hôm qua" (test chạy ở `Asia/Ho_Chi_Minh`).
 * - Trang được lấy dần khi cuộn, nên một ngày rất dễ vắt qua hai trang — gom
 *   sai là màn hình hiện hai mốc "Hôm nay" nằm liền nhau.
 */

const NOW = new Date('2026-08-31T10:00:00+07:00')

function dong(id: number, at: string, message = 'Tạo công việc: A'): WorkActivity {
  return {
    id,
    kind: 1,
    action: 'create',
    action_label: 'Tạo mới',
    message,
    by: 'Trần Minh Được',
    by_id: 1,
    at,
    task_id: null,
    task_title: '',
  }
}

describe('groupActivitiesByDay', () => {
  it('reads the timestamp as UTC even without a Z, so 01:00 local stays today', () => {
    //  `2026-08-30T18:30:00` UTC = 01:30 ngày 31/08 giờ VN. Đọc như giờ máy là
    //  rơi nhầm về "Hôm qua".
    const days = groupActivitiesByDay([dong(1, '2026-08-30T18:30:00')], NOW)
    expect(days).toHaveLength(1)
    expect(days[0].label).toBe('Hôm nay')
    expect(days[0].key).toBe('2026-08-31')
  })

  it('labels the previous calendar day as Hôm qua and older days as a date', () => {
    const days = groupActivitiesByDay(
      [dong(3, '2026-08-31T02:00:00'), dong(2, '2026-08-30T02:00:00'), dong(1, '2026-08-05T02:00:00')],
      NOW,
    )
    expect(days.map((d) => d.label)).toEqual(['Hôm nay', 'Hôm qua', 'Th 8'])
    expect(days.map((d) => d.dayNumber)).toEqual(['31', '30', '05'])
  })

  it('keeps one group per day even when the day is split across two fetched pages', () => {
    //  Đúng thế trận cuộn: trang 1 hết ở giữa ngày, trang 2 bắt đầu cũng ngày đó.
    const trang1 = [dong(5, '2026-08-31T02:00:00'), dong(4, '2026-08-31T01:00:00')]
    const trang2 = [dong(3, '2026-08-31T00:30:00'), dong(2, '2026-08-30T02:00:00')]
    const days = groupActivitiesByDay([...trang1, ...trang2], NOW)
    expect(days).toHaveLength(2)
    expect(days[0].items.map((i) => i.id)).toEqual([5, 4, 3])
  })

  it('preserves the newest-first order the backend sent, without re-sorting', () => {
    const days = groupActivitiesByDay(
      [dong(9, '2026-08-31T05:00:00'), dong(8, '2026-08-31T04:00:00')],
      NOW,
    )
    expect(days[0].items.map((i) => i.id)).toEqual([9, 8])
  })

  it('shows rows with a broken timestamp instead of swallowing them', () => {
    //  Mất một dòng nhật ký là mất dấu vết — thà hiện "Không rõ thời điểm".
    const days = groupActivitiesByDay([dong(1, ''), dong(2, 'khong-phai-ngay')], NOW)
    expect(days.flatMap((d) => d.items)).toHaveLength(2)
    expect(days.every((d) => d.label === 'Không rõ thời điểm')).toBe(true)
  })

  it('returns an empty array for an empty feed', () => {
    expect(groupActivitiesByDay([], NOW)).toEqual([])
  })

  it('adds the year to the month label when the day is not in the current year', () => {
    //  "Th 8" của năm ngoái và "Th 8" năm nay trông y hệt nhau nếu thiếu năm.
    const days = groupActivitiesByDay([dong(1, '2025-08-05T02:00:00')], NOW)
    expect(days[0].label).toBe('Th 8, 2025')
  })

  it('does not merge two different days that share a day-of-month', () => {
    //  31/08 và 31/07 cùng số ngày — khóa phải là cả năm-tháng-ngày.
    const days = groupActivitiesByDay(
      [dong(2, '2026-08-31T02:00:00'), dong(1, '2026-07-31T02:00:00')],
      NOW,
    )
    expect(days).toHaveLength(2)
  })
})
