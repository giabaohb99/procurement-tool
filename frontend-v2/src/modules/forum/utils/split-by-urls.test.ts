import { describe, expect, it } from 'vitest'

import { splitByUrls } from './split-by-urls'

describe('splitByUrls', () => {
  it('không có link thì trả nguyên văn một mẩu chữ', () => {
    expect(splitByUrls('chào cả nhà')).toEqual([{ type: 'text', value: 'chào cả nhà' }])
  })

  it('tách link giữa câu, giữ nguyên chữ hai bên', () => {
    expect(splitByUrls('xem tại https://dego.vn/tin nhé')).toEqual([
      { type: 'text', value: 'xem tại ' },
      { type: 'url', value: 'https://dego.vn/tin' },
      { type: 'text', value: ' nhé' },
    ])
  })

  it('dấu câu bám đuôi link thuộc về câu văn, không thuộc địa chỉ', () => {
    expect(splitByUrls('vào https://dego.vn.')).toEqual([
      { type: 'text', value: 'vào ' },
      { type: 'url', value: 'https://dego.vn' },
      { type: 'text', value: '.' },
    ])
  })

  it('link có ngoặc đóng hợp lệ (kiểu Wikipedia) thì không bị gọt', () => {
    expect(splitByUrls('https://vi.wikipedia.org/wiki/A_(phim)')).toEqual([
      { type: 'url', value: 'https://vi.wikipedia.org/wiki/A_(phim)' },
    ])
  })

  it('tên miền trần không có http thì KHÔNG biến thành link', () => {
    expect(splitByUrls('tệp baocao.xlsx gửi qua dego.vn')).toEqual([
      { type: 'text', value: 'tệp baocao.xlsx gửi qua dego.vn' },
    ])
  })

  it('nhiều link trong một bài đều được tách', () => {
    const parts = splitByUrls('a https://x.vn b http://y.vn c')
    expect(parts.filter((p) => p.type === 'url').map((p) => p.value)).toEqual([
      'https://x.vn',
      'http://y.vn',
    ])
  })
})
