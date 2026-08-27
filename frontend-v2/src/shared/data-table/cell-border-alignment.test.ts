import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

/**
 * LỖI ĐÃ XẢY RA (27/08/2026, phát hiện với bảng màu Notebook).
 *
 * Ô tiêu đề vẽ vạch dọc bằng `inset shadow`, ô thân bảng vẽ bằng `border-r`, mà
 * bảng để `border-collapse: collapse`. Hai cơ chế đặt vạch ở hai chỗ khác nhau:
 *
 * - `border-r` khi collapse bị CHIA ĐÔI qua ranh giới → `[mép − 0.5, mép + 0.5)`
 * - `inset shadow` vẽ HẲN trong lòng ô → `[mép − 1, mép)`
 *
 * Lệch nửa pixel ngay chỗ vạch của tiêu đề phải nối liền vạch của thân bảng. Bộ
 * màu DEGO có `--border` rất nhạt nên chẳng ai thấy; bảng màu nào đặt `--border`
 * đậm là lộ ngay.
 *
 * Test đọc thẳng chuỗi class trong nguồn: thứ cần canh là CƠ CHẾ vẽ vạch, mà
 * jsdom không tính bố cục nên đo trên DOM giả cũng không ra được độ lệch.
 */

const testDir = dirname(fileURLToPath(import.meta.url))

/** Lấy giá trị chuỗi của một hằng `const TÊN = '...'` (cho phép xuống dòng). */
function readStringConst(source: string, name: string): string {
  const match = source.match(new RegExp(`const ${name} =\\s*\\n?\\s*'([^']*)'`))
  if (!match) throw new Error(`Không tìm thấy hằng ${name}`)
  return match[1]
}

describe.each(['data-table.tsx', 'lines-table.tsx'])('%s', (fileName) => {
  const source = readFileSync(resolve(testDir, fileName), 'utf8')
  const headCell = readStringConst(source, 'HEAD_CELL')
  const bodyCell = readStringConst(source, 'BODY_CELL')

  it('ô thân bảng vẽ vạch dọc bằng inset shadow, KHÔNG bằng border-r', () => {
    expect(bodyCell).toContain('shadow-[inset_-1px_0_0_0_var(--border)]')
    expect(bodyCell).not.toMatch(/\bborder-r\b/)
  })

  it('ô tiêu đề và ô thân bảng dùng CÙNG một cơ chế vẽ vạch dọc', () => {
    const verticalRule = 'inset_-1px_0_0_0_var(--border)'
    expect(headCell).toContain(verticalRule)
    expect(bodyCell).toContain(verticalRule)
  })

  it('ô cuối hàng tắt vạch dọc để không vẽ đè lên viền ngoài của bảng', () => {
    expect(bodyCell).toMatch(/\blast:shadow-none\b/)
  })
})
