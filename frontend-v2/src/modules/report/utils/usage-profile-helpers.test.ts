import { describe, expect, it } from 'vitest'

import type { UsageSnapshot } from '../types/usage-profile'
import { classifyDay, describeCohort, findSecurityFlags, heatLevel, sumDwellByModule } from './usage-profile-helpers'

const day = (o: Partial<Parameters<typeof classifyDay>[0]>) => ({ day: '2026-10-05', active: false, is_workday: true, ...o })

describe('classifyDay', () => {
  it('separates leave and holiday from plain absence', () => {
    expect(classifyDay(day({ active: true }))).toBe('worked')
    expect(classifyDay(day({ leave_days: 1 }))).toBe('leave')
    expect(classifyDay(day({ is_holiday: true, is_workday: false }))).toBe('holiday')
    expect(classifyDay(day({ is_workday: false }))).toBe('off')
    expect(classifyDay(day({}))).toBe('absent')
  })

  it('counts a login on a holiday as worked, not as holiday', () => {
    expect(classifyDay(day({ active: true, is_holiday: true }))).toBe('worked')
  })

  it('treats zero leave days as absence', () => {
    expect(classifyDay(day({ leave_days: 0 }))).toBe('absent')
  })
})

describe('heatLevel', () => {
  it('maps to 0..4 and keeps any positive cell visible', () => {
    expect(heatLevel(0, 10)).toBe(0)
    expect(heatLevel(1, 1000)).toBe(1)
    expect(heatLevel(10, 10)).toBe(4)
    expect(heatLevel(5, 0)).toBe(0)
    expect(heatLevel(-3, 10)).toBe(0)
    expect(heatLevel(Number.NaN, 10)).toBe(0)
  })
})

describe('sumDwellByModule', () => {
  it('groups by module, drops zero dwell and sorts descending', () => {
    const out = sumDwellByModule(
      [
        { route: '/a', dwell_ms: 100 },
        { route: '/a/x', dwell_ms: 50 },
        { route: '/b', dwell_ms: 300 },
        { route: '/c', dwell_ms: 0 },
      ],
      (r) => (r.startsWith('/a') ? 'A' : r === '/b' ? 'B' : ''),
    )
    expect(out).toEqual([
      { label: 'B', value: 300 },
      { label: 'A', value: 150 },
    ])
  })

  it('returns an empty list for no screens', () => {
    expect(sumDwellByModule([], () => 'x')).toEqual([])
  })
})

describe('findSecurityFlags', () => {
  const snap = (metrics: UsageSnapshot['metrics'], unmeasured?: Record<string, number>): UsageSnapshot => ({ metrics, unmeasured })

  it('is empty when everything is zero, missing or unmeasured', () => {
    expect(findSecurityFlags(snap({ new_ip_logins: { v: 0 }, max_parallel_ips: { v: 1 } }))).toEqual([])
    expect(findSecurityFlags(snap({ new_ip_logins: { v: 3 } }, { new_ip_logins: 1 }))).toEqual([])
    expect(findSecurityFlags(snap({}))).toEqual([])
  })

  it('flags positive values, and parallel IPs only from 2', () => {
    expect(findSecurityFlags(snap({ new_device_logins: { v: 1 }, max_parallel_ips: { v: 2 } }))).toEqual([
      'new_device_logins',
      'max_parallel_ips',
    ])
  })
})

describe('describeCohort', () => {
  it('names the role cohort plainly', () => {
    expect(describeCohort({ kind: 1, name: 'Kế toán', size: 12 })).toBe('Đang so với: vai trò Kế toán (12 người).')
  })

  it('explains the fallback when the cohort is a company or everyone', () => {
    expect(describeCohort({ kind: 2, name: 'DEGO', size: 8 })).toContain('pháp nhân DEGO')
    expect(describeCohort({ kind: 3, name: '', size: 40 })).toContain('toàn công ty')
    expect(describeCohort({ kind: 3, name: '', size: 40 })).toContain('đủ 5 người')
  })

  it('copes with a missing cohort', () => {
    expect(describeCohort(undefined)).toBe('Chưa có nhóm so sánh.')
  })
})
