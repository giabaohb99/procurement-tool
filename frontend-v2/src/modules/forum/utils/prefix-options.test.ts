import { describe, expect, it } from 'vitest'

import { FORUM_PREFIX } from '@/shared/constants/statuses'

import { ANNOUNCEMENT_PREFIX, listPrefixOptions } from './prefix-options'

const values = (options: readonly { value: string }[]) => options.map((option) => option.value)

describe('listPrefixOptions', () => {
  it('keeps the generated code set in sync: announcement exists with label "Thông báo"', () => {
    const announcement = FORUM_PREFIX.find((option) => option.value === String(ANNOUNCEMENT_PREFIX))
    expect(announcement?.label).toBe('Thông báo')
  })

  it('hides the announcement label from ordinary members', () => {
    expect(values(listPrefixOptions(false))).not.toContain(String(ANNOUNCEMENT_PREFIX))
  })

  it('shows every label to forum managers', () => {
    expect(values(listPrefixOptions(true))).toEqual(values(FORUM_PREFIX))
  })

  it('keeps the current announcement value visible so an edit form does not lose it', () => {
    expect(values(listPrefixOptions(false, ANNOUNCEMENT_PREFIX))).toContain(String(ANNOUNCEMENT_PREFIX))
  })

  it('always keeps the "no prefix" option', () => {
    expect(values(listPrefixOptions(false))).toContain('0')
    expect(values(listPrefixOptions(true))).toContain('0')
  })
})
