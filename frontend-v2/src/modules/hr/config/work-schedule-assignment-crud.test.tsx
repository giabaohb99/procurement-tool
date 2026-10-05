import { describe, expect, it } from 'vitest'

import { WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG as config } from './work-schedule-assignment-crud'
import { WORK_SCHEDULE_CRUD_CONFIG } from './work-schedule-crud'

describe('work schedule CRUD configs', () => {
  // Regression: gán/gỡ lịch đổi assignment_count của mẫu, đổi tên mẫu đổi cột «Mẫu lịch» ở
  // màn Gán — thiếu khai báo thì hai màn hiển thị số liệu cũ cho tới khi tải lại trang.
  it('each screen also refreshes the cache of the other', () => {
    expect(config.alsoInvalidate).toContain(WORK_SCHEDULE_CRUD_CONFIG.apiPath)
    expect(WORK_SCHEDULE_CRUD_CONFIG.alsoInvalidate).toContain(config.apiPath)
  })

  it('never sends the display-only target_name to the backend and coerces ids to numbers', () => {
    const body = config.buildPayload?.({
      target_level: '3',
      target_id: '7',
      schedule_id: '2',
      target_name: 'Phòng Kế toán',
      effective_from: '2026-11-01',
    })
    expect(body).toEqual({
      target_level: 3,
      target_id: 7,
      schedule_id: 2,
      effective_from: '2026-11-01',
    })
    expect(body).not.toHaveProperty('target_name')
  })

  it('SYSTEM level with an empty / NaN target id sends 0, not NaN', () => {
    for (const bad of ['', undefined, 'x']) {
      const body = config.buildPayload?.({ target_level: 1, target_id: bad, schedule_id: 1 })
      expect(body?.target_id).toBe(0)
    }
  })
})
