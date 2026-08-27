import { describe, expect, it } from 'vitest'

import { isVideoMedia, pickMediaFiles } from './pick-media-files'

function fakeFile(name: string, type: string, sizeMb = 1): File {
  const file = new File([''], name, { type })
  // jsdom không cho dựng File có size thật — ghi đè thuộc tính chỉ đọc.
  Object.defineProperty(file, 'size', { value: sizeMb * 1024 * 1024 })
  return file
}

describe('pickMediaFiles', () => {
  it('nhận ảnh thường, không kêu ca gì', () => {
    const result = pickMediaFiles([fakeFile('a.png', 'image/png')], 0)
    expect(result.accepted).toHaveLength(1)
    expect(result.errors).toEqual([])
  })

  it('nhận video mp4/webm (D-Q3), vẫn chặn định dạng video khác', () => {
    const result = pickMediaFiles(
      [
        fakeFile('clip.mp4', 'video/mp4'),
        fakeFile('clip.webm', 'video/webm'),
        fakeFile('phim.mov', 'video/quicktime'),
      ],
      0,
    )
    expect(result.accepted.map((f) => f.name)).toEqual(['clip.mp4', 'clip.webm'])
    expect(result.errors[0]).toContain('1 tệp khác')
  })

  it('bỏ tệp không phải ảnh/video và nói rõ đã bỏ mấy tệp', () => {
    const result = pickMediaFiles(
      [fakeFile('bao-cao.pdf', 'application/pdf'), fakeFile('b.jpg', 'image/jpeg')],
      0,
    )
    expect(result.accepted.map((f) => f.name)).toEqual(['b.jpg'])
    expect(result.errors[0]).toContain('1 tệp khác')
  })

  it('tệp mất content-type nhưng đuôi là ảnh/video thì vẫn nhận (kéo từ app chat)', () => {
    const result = pickMediaFiles([fakeFile('screenshot.PNG', ''), fakeFile('clip.MP4', '')], 0)
    expect(result.accepted).toHaveLength(2)
  })

  it('bỏ tệp quá 50MB', () => {
    const result = pickMediaFiles([fakeFile('nang.mp4', 'video/mp4', 51)], 0)
    expect(result.accepted).toEqual([])
    expect(result.errors[0]).toContain('50MB')
  })

  it('cắt ở trần 10 tệp/bài, tính cả tệp đã đính trước đó', () => {
    const files = Array.from({ length: 5 }, (_, i) => fakeFile(`p${i}.png`, 'image/png'))
    const result = pickMediaFiles(files, 8)
    expect(result.accepted).toHaveLength(2)
    expect(result.errors[0]).toContain('3 tệp thừa')
  })
})

describe('isVideoMedia', () => {
  it('nhận diện theo content-type trước, đuôi tệp sau', () => {
    expect(isVideoMedia('clip.mp4', 'video/mp4')).toBe(true)
    expect(isVideoMedia('clip.webm', '')).toBe(true)
    expect(isVideoMedia('anh.png', 'image/png')).toBe(false)
  })
})
