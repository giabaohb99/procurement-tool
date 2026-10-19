import { describe, expect, it } from 'vitest'

import {
  VARIABLE_TYPE_DATE,
  VARIABLE_TYPE_MONEY,
  VARIABLE_TYPE_MULTILINE,
  VARIABLE_TYPE_NUMBER,
  VARIABLE_TYPE_TEXT,
} from '../types/labor-contract-variable'
import { formatVariableValue, numberToDisplay, sanitizeNumberText, toWireValue } from './labor-contract-variable-value'

describe('toWireValue', () => {
  it('kiểu Số: đổi , thành . và bỏ dấu thập phân treo', () => {
    expect(toWireValue(VARIABLE_TYPE_NUMBER, '1,5')).toBe('1.5')
    expect(toWireValue(VARIABLE_TYPE_NUMBER, '12,')).toBe('12')
    expect(toWireValue(VARIABLE_TYPE_NUMBER, ' 3 ')).toBe('3')
  })
  it('kiểu khác giữ nguyên', () => {
    expect(toWireValue(VARIABLE_TYPE_TEXT, 'a,b')).toBe('a,b')
    expect(toWireValue(VARIABLE_TYPE_MULTILINE, 'a\nb')).toBe('a\nb')
  })
})

describe('sanitizeNumberText', () => {
  it('chỉ giữ chữ số và một dấu thập phân, tối đa 2 số lẻ, không âm', () => {
    expect(sanitizeNumberText('-1a2,345')).toBe('12,34')
    expect(sanitizeNumberText('1.2.3')).toBe('1.23')
    expect(sanitizeNumberText('abc')).toBe('')
  })
  it('numberToDisplay đưa dấu chấm thập phân về dấu phẩy', () => {
    expect(numberToDisplay('1.5')).toBe('1,5')
  })
})

describe('formatVariableValue', () => {
  it('ngày dd/mm/yyyy, tiền ngăn nghìn, số kiểu Việt', () => {
    expect(formatVariableValue(VARIABLE_TYPE_DATE, '2026-10-01')).toBe('01/10/2026')
    expect(formatVariableValue(VARIABLE_TYPE_MONEY, '15000000')).toBe('15.000.000')
    expect(formatVariableValue(VARIABLE_TYPE_NUMBER, '1234.5')).toBe('1.234,5')
    expect(formatVariableValue(VARIABLE_TYPE_TEXT, 'abc')).toBe('abc')
    expect(formatVariableValue(VARIABLE_TYPE_TEXT, '')).toBe('')
  })
})
