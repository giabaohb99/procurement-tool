import { describe, expect, it } from 'vitest'

import { TONE_CLASS } from '@/shared/ui/status-tone'

import {
  describeGroupState,
  describeZaloState,
  formatFileSize,
  getChannelTone,
  toQrImageSrc,
} from './chat-group-format'

describe('describeGroupState', () => {
  it('says the bot left before anything else, even when the group was also paused', () => {
    expect(describeGroupState({ active: false, paused: true }).label).toBe('Bot đã rời nhóm')
  })

  it('separates paused from recording with different tones', () => {
    const paused = describeGroupState({ active: true, paused: true })
    const live = describeGroupState({ active: true, paused: false })
    expect(paused.label).toBe('Ngừng ghi')
    expect(live.label).toBe('Đang ghi')
    expect(paused.tone).not.toBe(live.tone)
  })
})

describe('getChannelTone', () => {
  it('gives the three channels three different colours and falls back to neutral', () => {
    const tones = ['telegram', 'zalo_account', 'zalo_bot'].map(getChannelTone)
    expect(new Set(tones).size).toBe(3)
    expect(getChannelTone('')).toBe(TONE_CLASS.neutral)
    expect(getChannelTone('whatsapp')).toBe(TONE_CLASS.neutral)
  })
})

describe('describeZaloState', () => {
  it('treats a missing status as switched off, not as connected', () => {
    expect(describeZaloState(undefined).label).toBe('Chưa bật')
  })

  it('marks lost sessions and an unreachable listener as danger', () => {
    expect(describeZaloState({ enabled: true, state: 'down' }).tone).toBe(TONE_CLASS.danger)
    expect(describeZaloState({ enabled: true, state: 'unreachable' }).tone).toBe(TONE_CLASS.danger)
  })

  it('shows an unknown state code as-is instead of hiding it', () => {
    expect(describeZaloState({ enabled: true, state: 'banned' }).label).toBe('banned')
  })
})

describe('formatFileSize', () => {
  it('returns empty for unknown, zero, negative or non-finite sizes', () => {
    for (const v of [0, -5, Number.NaN, Number.POSITIVE_INFINITY, null, undefined]) {
      expect(formatFileSize(v)).toBe('')
    }
  })

  it('switches units at the KB and MB boundaries', () => {
    expect(formatFileSize(1)).toBe('1 B')
    expect(formatFileSize(1023)).toBe('1023 B')
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1024 * 1024)).toBe('1.0 MB')
    expect(formatFileSize(25 * 1024 * 1024)).toBe('25.0 MB')
  })
})

describe('toQrImageSrc', () => {
  it('wraps bare base64 into a png data url and strips whitespace', () => {
    expect(toQrImageSrc('iVBO Rw0K\n')).toBe('data:image/png;base64,iVBORw0K')
  })

  it('keeps a value that already is an image data url', () => {
    expect(toQrImageSrc('data:image/png;base64,AAAA')).toBe('data:image/png;base64,AAAA')
  })

  it('refuses anything that is not base64 so it cannot become an arbitrary src', () => {
    expect(toQrImageSrc('javascript:alert(1)')).toBe('')
    expect(toQrImageSrc('https://evil.example/x.png')).toBe('')
    expect(toQrImageSrc('"><img onerror=x>')).toBe('')
    expect(toQrImageSrc('')).toBe('')
    expect(toQrImageSrc(null)).toBe('')
  })
})
