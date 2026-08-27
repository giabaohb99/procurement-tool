import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

/**
 * LỖI ĐÃ XẢY RA (27/08/2026). Nền hàng của hai bảng danh sách viết cứng bằng bảng
 * màu Tailwind gốc: `bg-slate-200/80` cho hàng tiêu đề, `even:bg-slate-100` cho
 * vằn hàng chẵn, `hover:bg-sky-100`, `data-[state=selected]:bg-blue-100`. Màu
 * Tailwind gốc KHÔNG đi theo bảng màu người dùng chọn.
 *
 * Hậu quả thấy được khi bật bảng màu Starry Night: hàng tiêu đề lấy `--muted` của
 * bảng màu nên ra màu kem, còn vằn hàng và hover vẫn xanh slate/sky cố định — ba
 * họ màu chẳng liên quan gì nhau trong cùng một cái bảng.
 *
 * Đọc thẳng tệp nguồn thay vì dựng component: thứ cần canh là CHUỖI CLASS, mà
 * khẳng định theo class trên DOM thì trái luật trong `.claude/rules/testing.md`.
 */

const testDir = dirname(fileURLToPath(import.meta.url))

/** Màu nền cứng, không đi theo bảng màu. `bg-transparent`/`bg-inherit` thì được. */
const HARD_CODED_BACKGROUND = /\bbg-(slate|sky|blue|gray|zinc|neutral|stone)-\d{2,3}\b/

/** Màu CHỮ cứng, cùng lý do. */
const HARD_CODED_TEXT = /\btext-(slate|sky|blue|gray|zinc|neutral|stone)-\d{2,3}\b/

/** Bỏ comment để chú thích kể lại lỗi cũ không bị chính test này bắt. */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '')
}

describe.each(['data-table.tsx', 'lines-table.tsx'])('%s', (fileName) => {
  const code = stripComments(readFileSync(resolve(testDir, fileName), 'utf8'))

  it('không tô nền hàng bằng màu Tailwind gốc — nền hàng phải đi theo bảng màu', () => {
    expect(code.match(HARD_CODED_BACKGROUND)).toBeNull()
  })

  it('không tô chữ hàng tiêu đề bằng màu Tailwind gốc', () => {
    expect(code.match(HARD_CODED_TEXT)).toBeNull()
  })

  it('dùng đủ bộ token nền hàng', () => {
    for (const token of ['bg-row-head', 'bg-row-stripe', 'bg-row-hover']) {
      expect(code).toContain(token)
    }
  })

  it('nền hàng và nền tiêu đề KHÔNG có alpha — cột ghim lấy bg-inherit nên hở là lộ dòng trôi phía sau', () => {
    //  Lỗi thật 24/08/2026: `bg-sky-100/70` làm chữ cột ghim chồng lên chữ của
    //  cột đang cuộn ngang qua bên dưới.
    expect(code.match(/\bbg-row-[a-z-]+\/\d+/)).toBeNull()
    expect(code.match(/\bbg-card\/\d+/)).toBeNull()
  })
})
