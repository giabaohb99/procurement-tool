import { describe, expect, it } from 'vitest'

import { maskTime24h, parseTime24h, shiftTime24h } from './time-24h'

describe('maskTime24h', () => {
  it('inserts the colon after two digits and drops everything that is not a digit', () => {
    expect(maskTime24h('0830')).toBe('08:30')
    expect(maskTime24h('8')).toBe('8')
    expect(maskTime24h('08:3')).toBe('08:3')
    expect(maskTime24h('ab1c7:00zz')).toBe('17:00')
  })

  it('typing «8:30» keystroke by keystroke gives 08:30, not 83:0', () => {
    let text = ''
    for (const ch of '8:30') text = maskTime24h(text + ch)
    expect(text).toBe('08:30')
  })

  it('caps at four digits so a pasted string cannot overflow the box', () => {
    expect(maskTime24h('1234567')).toBe('12:34')
    expect(maskTime24h('')).toBe('')
  })
})

describe('parseTime24h', () => {
  it('normalises the shapes people really type', () => {
    expect(parseTime24h('8')).toBe('08:00')
    expect(parseTime24h('17')).toBe('17:00')
    expect(parseTime24h('830')).toBe('08:30')
    expect(parseTime24h('0830')).toBe('08:30')
    expect(parseTime24h('8:30')).toBe('08:30')
    expect(parseTime24h(' 17:05 ')).toBe('17:05')
    expect(parseTime24h('8:3')).toBe('08:30')
  })

  it('accepts the exact edges 00:00 and 23:59', () => {
    expect(parseTime24h('00:00')).toBe('00:00')
    expect(parseTime24h('23:59')).toBe('23:59')
  })

  it('rejects out-of-range hours and minutes instead of wrapping them', () => {
    expect(parseTime24h('24:00')).toBeNull()
    expect(parseTime24h('12:60')).toBeNull()
    expect(parseTime24h('99')).toBeNull()
    expect(parseTime24h('2460')).toBeNull()
  })

  it('rejects empty, AM/PM text, negatives and junk', () => {
    for (const bad of ['', '   ', '08:00 AM', '-1', '1:2:3', 'abc', '12345', '08:000']) {
      expect(parseTime24h(bad)).toBeNull()
    }
  })
})

describe('shiftTime24h', () => {
  it('steps by minutes and pads the result', () => {
    expect(shiftTime24h('08:00', 15)).toBe('08:15')
    expect(shiftTime24h('08:00', -15)).toBe('07:45')
  })

  it('clamps at the day edges instead of wrapping past midnight', () => {
    expect(shiftTime24h('00:05', -15)).toBe('00:00')
    expect(shiftTime24h('23:50', 15)).toBe('23:59')
  })

  it('starts from 00:00 when the current value is empty or broken', () => {
    expect(shiftTime24h(null, 15)).toBe('00:15')
    expect(shiftTime24h('zz', 15)).toBe('00:15')
  })
})
