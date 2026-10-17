import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AI_SKILL_INTRO_CHAPTERS } from './ai-skill-intro'

//  Thứ tự 9 chương đã chốt với Agent 1 (doc/erp/21 §6.4) — đổi chữ / đổi thứ tự là phải báo lại.
const EXPECTED_TITLES = [
  'Chọn phòng ban sẽ dùng',
  'Tạo bộ skill',
  'Soạn hoặc tải skill lên',
  'Gán ai được đọc',
  'Phát khóa cho từng người',
  'Nối AI của nhân sự',
  'Hỏi AI một câu nghiệp vụ',
  'Xem ai dùng gì',
  'Thu hồi khóa tức thì',
]

describe('AI_SKILL_INTRO_CHAPTERS', () => {
  it('has the nine agreed chapters in order with unique ids', () => {
    expect(AI_SKILL_INTRO_CHAPTERS.map((c) => c.title)).toEqual(EXPECTED_TITLES)
    expect(new Set(AI_SKILL_INTRO_CHAPTERS.map((c) => c.id)).size).toBe(9)
  })

  it('keeps every caption a real sentence without guillemets or emoji', () => {
    for (const c of AI_SKILL_INTRO_CHAPTERS) {
      for (const text of [c.title, c.caption]) {
        expect(text.trim().length).toBeGreaterThan(0)
        expect(text).not.toMatch(/[«»]/)
        expect(text).not.toMatch(/\p{Extended_Pictographic}/u)
      }
      expect(c.durationMs).toBeGreaterThanOrEqual(3000)
    }
  })

  it('keeps cursor paths inside the frame and inside the chapter timeline', () => {
    for (const c of AI_SKILL_INTRO_CHAPTERS) {
      for (const p of c.cursor ?? []) {
        expect(p.at).toBeGreaterThanOrEqual(0)
        expect(p.at).toBeLessThanOrEqual(1)
        expect(p.x).toBeGreaterThanOrEqual(0)
        expect(p.x).toBeLessThanOrEqual(100)
        expect(p.y).toBeGreaterThanOrEqual(0)
        expect(p.y).toBeLessThanOrEqual(100)
      }
    }
  })

  it('renders every scene at start, middle and end, moving and still, without throwing', () => {
    for (const c of AI_SKILL_INTRO_CHAPTERS) {
      for (const progress of [0, 0.5, 1]) {
        for (const reduced of [false, true]) {
          const { unmount, container } = render(<>{c.render({ progress, reduced })}</>)
          expect(container.textContent?.length).toBeGreaterThan(0)
          unmount()
        }
      }
    }
  })

  it('shows the finished state on the last frame (what reduced-motion users see)', () => {
    const revoke = AI_SKILL_INTRO_CHAPTERS[8]
    const { getByText } = render(<>{revoke.render({ progress: 1, reduced: true })}</>)
    expect(getByText('Đã thu hồi')).toBeInTheDocument()
  })
})
