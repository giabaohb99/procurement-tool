// bao-CR-658: bài kiểm quét mã — Ô LỌC KHÔNG ĐƯỢC TỰ GÁN.
// Đọc mọi .tsx trong src/, tìm thẻ <SearchSelect có placeholder bắt đầu bằng "Tất cả" (dấu hiệu
// ô lọc: rỗng = Tất cả) mà lại bật autoSelectSingle thì in lỗi và thoát mã 1.
// Chạy: npm run check:filters
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const srcDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'src')

const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
  const p = path.join(dir, e.name)
  return e.isDirectory() ? walk(p) : e.name.endsWith('.tsx') ? [p] : []
})

// Cắt nguyên thẻ mở <SearchSelect ...> — bỏ qua dấu > / /> nằm trong {...} hoặc trong chuỗi
function readTag(src, start) {
  let depth = 0
  let quote = null
  for (let i = start + 1; i < src.length; i++) {
    const ch = src[i]
    if (quote) {
      if (ch === '\\') i++
      else if (ch === quote) quote = null
      continue
    }
    if (ch === '"' || ch === "'" || ch === '`') quote = ch
    else if (ch === '{') depth++
    else if (ch === '}') depth--
    else if (ch === '>' && depth === 0) return src.slice(start, i + 1)
  }
  return src.slice(start)
}

const FILTER_PLACEHOLDER = /placeholder=(?:"|\{\s*["'`])Tất cả/
// Bật = có thuộc tính autoSelectSingle mà KHÔNG phải ={false}
const AUTO_ON = /\bautoSelectSingle\b(?!\s*=\s*\{\s*false\s*\})/

const errors = []
for (const file of walk(srcDir)) {
  const src = fs.readFileSync(file, 'utf8')
  let idx = src.indexOf('<SearchSelect')
  while (idx !== -1) {
    const tag = readTag(src, idx)
    if (FILTER_PLACEHOLDER.test(tag) && AUTO_ON.test(tag)) {
      const line = src.slice(0, idx).split('\n').length
      errors.push(`${path.relative(path.join(srcDir, '..'), file)}:${line}`)
    }
    idx = src.indexOf('<SearchSelect', idx + 1)
  }
}

if (errors.length) {
  console.error('Ô lọc (placeholder "Tất cả") đang bật autoSelectSingle — ô lọc không được tự gán (bao-CR-658):')
  for (const e of errors) console.error('  ' + e)
  process.exit(1)
}
console.log('check:filters OK — không ô lọc nào bật autoSelectSingle.')
