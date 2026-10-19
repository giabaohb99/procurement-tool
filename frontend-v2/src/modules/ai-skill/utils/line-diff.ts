/**
 * So hai bản nội dung skill theo DÒNG (LCS) để màn Phiên bản tô dòng thêm / bớt khi đặt hai bản cạnh nhau.
 *
 * Bảng LCS tốn bộ nhớ n × m: hai bản 5 000 dòng là 25 triệu ô — đủ làm treo tab. Quá trần thì trả `tooLarge` và màn
 * chỉ đặt hai bản cạnh nhau, không tô.
 */

export const MAX_DIFF_CELLS = 4_000_000

export type DiffKind = 'same' | 'removed' | 'added'

export interface DiffLine {
  kind: DiffKind
  text: string
}

export interface LineDiff {
  /** Dòng của bản cũ, đánh dấu `removed` những dòng không còn ở bản mới. */
  left: DiffLine[]
  /** Dòng của bản mới, đánh dấu `added` những dòng mới thêm. */
  right: DiffLine[]
  added: number
  removed: number
  tooLarge: boolean
}

function splitLines(text: string): string[] {
  if (text === '') return []
  return text.replace(/\r\n?/g, '\n').split('\n')
}

export function diffLines(oldText: string, newText: string): LineDiff {
  const a = splitLines(oldText)
  const b = splitLines(newText)
  const n = a.length
  const m = b.length

  if ((n + 1) * (m + 1) > MAX_DIFF_CELLS) {
    return {
      left: a.map((text) => ({ kind: 'same', text })),
      right: b.map((text) => ({ kind: 'same', text })),
      added: 0,
      removed: 0,
      tooLarge: true,
    }
  }

  //  lcs[i][j] = độ dài chuỗi con chung dài nhất của a[i..] và b[j..], trải phẳng một mảng số nguyên.
  const width = m + 1
  const lcs = new Uint32Array((n + 1) * width)
  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = m - 1; j >= 0; j -= 1) {
      lcs[i * width + j] =
        a[i] === b[j] ? lcs[(i + 1) * width + j + 1] + 1 : Math.max(lcs[(i + 1) * width + j], lcs[i * width + j + 1])
    }
  }

  const left: DiffLine[] = []
  const right: DiffLine[] = []
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      left.push({ kind: 'same', text: a[i] })
      right.push({ kind: 'same', text: b[j] })
      i += 1
      j += 1
    } else if (lcs[(i + 1) * width + j] >= lcs[i * width + j + 1]) {
      left.push({ kind: 'removed', text: a[i] })
      i += 1
    } else {
      right.push({ kind: 'added', text: b[j] })
      j += 1
    }
  }
  for (; i < n; i += 1) left.push({ kind: 'removed', text: a[i] })
  for (; j < m; j += 1) right.push({ kind: 'added', text: b[j] })

  return {
    left,
    right,
    added: right.filter((line) => line.kind === 'added').length,
    removed: left.filter((line) => line.kind === 'removed').length,
    tooLarge: false,
  }
}
