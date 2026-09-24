import { describe, expect, it } from 'vitest'

import { tokenizeJson } from './tokenize-json'

/** Ghép token lại phải ra ĐÚNG chuỗi gốc — bất biến quan trọng nhất của bộ tách. */
function rebuild(text: string): string {
  return tokenizeJson(text)
    .map((t) => t.text)
    .join('')
}

/** Lấy phần chữ của mọi token thuộc một loại, cho dễ khẳng định. */
function textsOf(text: string, kind: string): string[] {
  return tokenizeJson(text)
    .filter((t) => t.kind === kind)
    .map((t) => t.text)
}

describe('tokenizeJson', () => {
  it('never loses or duplicates a character — the join must equal the input', () => {
    //  Đây là chốt chặn thật sự: tô màu mà nuốt một dấu ngoặc thì người đi truy
    //  sự cố đọc một thân yêu cầu KHÁC với thân đã gửi, và không cách nào biết.
    const samples = [
      '{\n  "status": 0\n}',
      '{"a":[1,2,{"b":null}],"c":"x"}',
      'Traceback (most recent call last):\n  File "x.py", line 12',
      '',
      '   ',
      '{"vi": "Đã cập nhật tiến độ", "n": -12.5e3}',
    ]
    for (const sample of samples) expect(rebuild(sample)).toBe(sample)
  })

  it('tells a KEY apart from a string value — both are quoted', () => {
    const json = '{"status": "draft"}'
    expect(textsOf(json, 'key')).toEqual(['"status"'])
    expect(textsOf(json, 'string')).toEqual(['"draft"'])
  })

  it('keeps the colon out of the key token', () => {
    //  Gộp dấu hai chấm vào khóa thì nó ăn màu khóa và ra một cụm lạ giữa dòng.
    const tokens = tokenizeJson('{"a": 1}')
    expect(tokens.find((t) => t.kind === 'key')?.text).toBe('"a"')
    expect(tokens.map((t) => t.text).join('')).toContain('": ')
  })

  it('does not break on an escaped quote inside a string', () => {
    //  Mẫu ngây thơ `"[^"]*"` cắt ngay tại dấu nháy đã escape rồi lệch màu suốt
    //  phần còn lại của dòng — thân yêu cầu có trích dẫn là dính ngay.
    const json = '{"msg": "nói \\"xin chào\\" rồi đi"}'
    expect(textsOf(json, 'string')).toEqual(['"nói \\"xin chào\\" rồi đi"'])
    expect(rebuild(json)).toBe(json)
  })

  it('reads numbers in every JSON shape, including negative and exponent', () => {
    expect(textsOf('{"a": -12.5e-3}', 'number')).toEqual(['-12.5e-3'])
    expect(textsOf('{"a": 0}', 'number')).toEqual(['0'])
  })

  it('marks true/false/null as keywords, but not words that merely contain them', () => {
    expect(textsOf('{"a": true, "b": null}', 'keyword')).toEqual(['true', 'null'])
    //  "nullable" chỉ là chữ thường trong một chuỗi — tô nó lên là nói dối về kiểu.
    expect(textsOf('{"a": "nullable"}', 'keyword')).toEqual([])
  })

  it('returns nothing for an empty string instead of one empty token', () => {
    expect(tokenizeJson('')).toEqual([])
  })

  it('survives text that is not JSON at all', () => {
    const text = 'không phải JSON, chỉ là một câu'
    expect(rebuild(text)).toBe(text)
  })

  it('stays correct when called twice — the shared regex must not keep its lastIndex', () => {
    //  Biểu thức khai ở tầng module với cờ `g`: quên đặt lại `lastIndex` thì lượt
    //  gọi thứ hai bắt đầu từ giữa chuỗi và mất sạch màu, chỉ ở những lần render
    //  sau — đúng kiểu lỗi không bao giờ tái hiện được bằng tay.
    const json = '{"a": 1}'
    expect(tokenizeJson(json)).toEqual(tokenizeJson(json))
  })
})
