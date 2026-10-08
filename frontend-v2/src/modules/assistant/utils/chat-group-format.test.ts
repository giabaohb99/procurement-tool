import { describe, expect, it } from 'vitest'

import { TONE_CLASS } from '@/shared/ui/status-tone'

import type { ChatGroupMessage } from '../api/chat-group-api'
import {
  buildGroupThread,
  describeGroupState,
  describeZaloState,
  formatFileSize,
  getAvatarTone,
  getChannelTone,
  getInitials,
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

function msg(id: number, from: string, sentAtUtc: string | null, text = 'x'): ChatGroupMessage {
  return { id, from_name: from, text, sent_at: sentAtUtc, file: null }
}

describe('buildGroupThread', () => {
  //  Giờ máy chủ là UTC trần; test chạy múi giờ Asia/Ho_Chi_Minh (+7).
  const now = new Date('2026-10-08T10:00:00Z')

  it('orders oldest first even though the server sends newest first, and drops duplicates across pages', () => {
    const items = buildGroupThread([msg(3, 'A', '2026-10-08T09:30:00'), msg(1, 'A', '2026-10-08T09:00:00'),
      msg(3, 'A', '2026-10-08T09:30:00')], now)
    const ids = items.flatMap((i) => (i.kind === 'message' ? [i.message.id] : []))
    expect(ids).toEqual([1, 3])
  })

  it('puts a day separator using Vietnam time, not the UTC date', () => {
    //  23:30 UTC ngày 07 = 06:30 sáng ngày 08 giờ VN → phải nằm dưới «Hôm nay», không phải «Hôm qua».
    const items = buildGroupThread([msg(1, 'A', '2026-10-07T23:30:00')], now)
    expect(items[0]).toMatchObject({ kind: 'day', label: 'Hôm nay' })
  })

  it('labels yesterday and older days, and starts a new header after each separator', () => {
    const items = buildGroupThread(
      [msg(1, 'A', '2026-10-06T03:00:00'), msg(2, 'A', '2026-10-07T03:00:00'), msg(3, 'A', '2026-10-07T03:01:00')],
      now,
    )
    expect(items.filter((i) => i.kind === 'day').map((i) => (i.kind === 'day' ? i.label : ''))).toEqual([
      '06/10/2026',
      'Hôm qua',
    ])
    const headers = items.flatMap((i) => (i.kind === 'message' ? [i.showHeader] : []))
    expect(headers).toEqual([true, true, false])
  })

  it('shows the sender again when a different person speaks or the same person pauses over five minutes', () => {
    const items = buildGroupThread(
      [msg(1, 'A', '2026-10-08T01:00:00'), msg(2, 'B', '2026-10-08T01:01:00'), msg(3, 'B', '2026-10-08T01:07:00')],
      now,
    )
    expect(items.flatMap((i) => (i.kind === 'message' ? [i.showHeader] : []))).toEqual([true, true, true])
  })

  it('keeps a message with no time instead of dropping it', () => {
    const items = buildGroupThread([msg(1, 'A', null), msg(2, 'A', null)], now)
    expect(items.map((i) => i.kind)).toEqual(['message', 'message'])
    expect(buildGroupThread([], now)).toEqual([])
  })
})

describe('getInitials / getAvatarTone', () => {
  it('takes the first letter of the last two words, upper-cased, and survives empty names', () => {
    expect(getInitials('Trần Được')).toBe('TĐ')
    expect(getInitials('  Pltgiang ')).toBe('P')
    expect(getInitials('Nguyễn Thị Thảo Thơ')).toBe('TT')
    expect(getInitials('')).toBe('?')
    expect(getInitials(null)).toBe('?')
  })

  it('gives the same person the same colour every time', () => {
    expect(getAvatarTone('Chị Mi')).toBe(getAvatarTone('Chị Mi'))
    expect(getAvatarTone('')).toBeTruthy()
  })
})

