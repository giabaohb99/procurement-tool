import { describe, expect, it } from 'vitest'

import { RETRYABLE_SYNC_STATUSES, SYNC_STATUS } from '../api/sync-log-api'
import { runCountsText, shortMessage, syncStatusTone } from './sync-log-format'

describe('syncStatusTone', () => {
  it('keeps every status distinguishable, so a screen of skipped rows never reads as success', () => {
    const tones = Object.values(SYNC_STATUS).map(syncStatusTone)
    expect(new Set(tones).size).toBe(Object.values(SYNC_STATUS).length)
  })

  it('never paints a failed row with a calm tone', () => {
    expect(syncStatusTone(SYNC_STATUS.FAILED)).toBe('danger')
  })

  it('falls back to neutral for a code this build has never heard of', () => {
    //  Backend có thể thêm mã trạng thái mới trước khi frontend được deploy lại.
    //  Rơi về xám còn hơn ném lỗi và làm trắng cả bảng.
    expect(syncStatusTone(99)).toBe('neutral')
    expect(syncStatusTone(0)).toBe('neutral')
    expect(syncStatusTone(-1)).toBe('neutral')
  })
})

describe('RETRYABLE_SYNC_STATUSES', () => {
  //  Khớp `RETRYABLE_STATUSES` ở backend/app/modules/sync_log/constants.py.
  //  Lệch nhau thì nút *Chạy lại* hiện ra rồi ăn 400, hoặc ẩn đi ở đúng dòng
  //  người ta cần bấm.
  it('offers retry exactly on failed and pending rows', () => {
    expect([...RETRYABLE_SYNC_STATUSES].sort()).toEqual(
      [SYNC_STATUS.PENDING, SYNC_STATUS.FAILED].sort(),
    )
    expect(RETRYABLE_SYNC_STATUSES).not.toContain(SYNC_STATUS.SUCCESS)
    expect(RETRYABLE_SYNC_STATUSES).not.toContain(SYNC_STATUS.RUNNING)
    expect(RETRYABLE_SYNC_STATUSES).not.toContain(SYNC_STATUS.SKIPPED)
  })
})

describe('runCountsText', () => {
  it('shows a dash for an idle run instead of three zeroes that look like a fault', () => {
    expect(runCountsText(0, 0, 0)).toBe('—')
  })

  it('keeps a run that fetched rows but wrote none — that is the interesting one', () => {
    expect(runCountsText(12, 0, 0)).toBe('12 kéo · 0 ghi · 0 bỏ')
  })

  it('keeps counts that only appear in the skipped column', () => {
    expect(runCountsText(0, 0, 3)).toBe('0 kéo · 0 ghi · 3 bỏ')
  })
})

describe('shortMessage', () => {
  it('cuts at the first line, so a Python traceback does not fill the column with its banner', () => {
    const traceback = 'Traceback (most recent call last):\n  File "x.py", line 1\nKeyError: bookingId'
    expect(shortMessage(traceback)).toBe('Traceback (most recent call last):')
  })

  it('returns an empty string for a message that is only whitespace', () => {
    expect(shortMessage('')).toBe('')
    expect(shortMessage('   \n  \n')).toBe('')
  })

  it('truncates a single long line and marks the cut', () => {
    const long = 'x'.repeat(200)
    const cut = shortMessage(long, 120)
    expect(cut).toHaveLength(121)
    expect(cut.endsWith('…')).toBe(true)
  })

  it('leaves a line sitting exactly on the limit untouched', () => {
    const exact = 'y'.repeat(120)
    expect(shortMessage(exact, 120)).toBe(exact)
  })

  it('trims the first line so a leading newline does not render as a blank cell', () => {
    expect(shortMessage('\n  Khóa ký sai  \nchi tiết')).toBe('')
    expect(shortMessage('  Khóa ký sai  \nchi tiết')).toBe('Khóa ký sai')
  })
})
