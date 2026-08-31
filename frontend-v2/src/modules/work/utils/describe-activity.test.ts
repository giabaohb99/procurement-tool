import { describe, expect, it } from 'vitest'

import type { WorkActivity } from '../types/activity'
import { describeActivity } from './describe-activity'

/**
 * Câu kể đứng sau tên người trên dòng hoạt động.
 *
 * Chỗ dễ hỏng: câu ghi log là chuỗi tiếng Việt do backend gửi sang, hạ chữ hoa
 * bằng `toLowerCase()` trần là hỏng dấu và hỏng luôn các từ viết tắt (YCMH).
 */

function dong(over: Partial<WorkActivity> = {}): WorkActivity {
  return {
    id: 1,
    kind: 1,
    action: 'create',
    action_label: 'Tạo mới',
    message: 'Tạo công việc: Dựng khung',
    by: 'Trần Minh Được',
    by_id: 1,
    at: '2026-08-31T02:00:00',
    task_id: 1,
    task_title: 'Dựng khung',
    ...over,
  }
}

describe('describeActivity', () => {
  it('drops the trailing task name, which the row already shows on its own line', () => {
    expect(describeActivity(dong())).toBe('đã tạo công việc')
  })

  it('keeps a colon whose tail is NOT the task name', () => {
    //  `Thêm phụ thuộc: A → B` — cắt ở dấu hai chấm cuối là mất sạch nội dung.
    const activity = dong({
      message: 'Thêm phụ thuộc: Đăng bài → Đào tạo',
      task_title: 'Đào tạo',
    })
    expect(describeActivity(activity)).toBe('đã thêm phụ thuộc: Đăng bài → Đào tạo')
  })

  it('leaves the sentence whole when the row has no task name to show', () => {
    expect(describeActivity(dong({ task_title: '' }))).toBe('đã tạo công việc: Dựng khung')
  })

  it('does not strip a task name that merely appears in the middle', () => {
    const activity = dong({ message: 'Sửa công việc: Dựng khung xong', task_title: 'Dựng khung' })
    expect(describeActivity(activity)).toBe('đã sửa công việc: Dựng khung xong')
  })

  it('keeps Vietnamese diacritics when lowering the first letter', () => {
    expect(describeActivity(dong({ message: 'Đổi người phụ trách' }))).toBe(
      'đã đổi người phụ trách',
    )
  })

  it('leaves an all-caps abbreviation alone instead of breaking it', () => {
    expect(describeActivity(dong({ message: 'YCMH đã được duyệt' }))).toBe(
      'đã YCMH đã được duyệt',
    )
  })

  it('falls back to the action label when the log line has no message', () => {
    //  Dòng trống trơn thì người đọc không biết chuyện gì đã xảy ra.
    expect(describeActivity(dong({ message: '' }))).toBe('đã tạo mới')
    expect(describeActivity(dong({ message: '   ' }))).toBe('đã tạo mới')
  })

  it('returns an empty clause when there is nothing at all to say', () => {
    expect(describeActivity(dong({ message: '', action_label: '' }))).toBe('')
  })

  it('does not touch a sentence that already starts lowercase or with a digit', () => {
    expect(describeActivity(dong({ message: 'gỡ nhân sự #4' }))).toBe('đã gỡ nhân sự #4')
    expect(describeActivity(dong({ message: '3 việc bị dời hạn' }))).toBe('đã 3 việc bị dời hạn')
  })
})
