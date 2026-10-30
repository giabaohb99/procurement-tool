import { describe, expect, it } from 'vitest'

import { JOB_RUN_STATUS } from '../api/job-run-api'
import { formatDuration, jobRunTone, runsText } from './job-run-format'

describe('formatDuration', () => {
  it('shows a dash, not 0 ms, when the run has no duration (still running or died midway)', () => {
    expect(formatDuration(null)).toBe('—')
    expect(formatDuration(undefined)).toBe('—')
    expect(formatDuration(-5)).toBe('—')
    expect(formatDuration(Number.NaN)).toBe('—')
  })

  it('keeps sub-second runs in milliseconds, including a zero-length run', () => {
    expect(formatDuration(0)).toBe('0 ms')
    expect(formatDuration(349.6)).toBe('350 ms')
    expect(formatDuration(999)).toBe('999 ms')
  })

  it('writes seconds with a Vietnamese decimal comma', () => {
    expect(formatDuration(1000)).toBe('1,0 giây')
    expect(formatDuration(4210)).toBe('4,2 giây')
  })

  it('switches to minutes at 60 s and pads the seconds', () => {
    expect(formatDuration(60_000)).toBe('1 phút 00 giây')
    expect(formatDuration(185_000)).toBe('3 phút 05 giây')
  })

  it('switches to hours at 60 minutes for a long backup', () => {
    expect(formatDuration(3_600_000)).toBe('1 giờ 00 phút')
    expect(formatDuration(4_320_000)).toBe('1 giờ 12 phút')
    expect(formatDuration(30 * 3_600_000)).toBe('30 giờ 00 phút')
  })
})

describe('jobRunTone', () => {
  it('colours success, failure and running apart, and never paints a skipped run green', () => {
    expect(jobRunTone(JOB_RUN_STATUS.SUCCESS)).toBe('done')
    expect(jobRunTone(JOB_RUN_STATUS.FAILED)).toBe('danger')
    expect(jobRunTone(JOB_RUN_STATUS.RUNNING)).toBe('active')
    expect(jobRunTone(JOB_RUN_STATUS.SKIPPED)).toBe('neutral')
  })

  it('falls back to neutral for a never-run job or an unknown code from a newer server', () => {
    expect(jobRunTone(null)).toBe('neutral')
    expect(jobRunTone(undefined)).toBe('neutral')
    expect(jobRunTone(99)).toBe('neutral')
  })
})

describe('runsText', () => {
  it('says the job did not run at all in 7 days instead of a quiet 0', () => {
    expect(runsText(0, 0)).toBe('Chưa chạy')
    expect(runsText(null, null)).toBe('Chưa chạy')
    expect(runsText(-3, 1)).toBe('Chưa chạy')
  })

  it('adds the failure count only when there is one', () => {
    expect(runsText(7, 0)).toBe('7 lần')
    expect(runsText(12, 2)).toBe('12 lần · 2 lỗi')
  })

  it('never reports more failures than runs or a negative failure count', () => {
    expect(runsText(3, 9)).toBe('3 lần · 3 lỗi')
    expect(runsText(3, -1)).toBe('3 lần')
  })
})
