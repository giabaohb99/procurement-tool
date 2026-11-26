/**
 * duoc-CR-784 — chọn nhãn ngày cho trục X của biểu đồ bản in sao cho KHÔNG đè nhau (trước đây lấy cách đều `i % step`
 * rồi thêm nhãn cuối nên hai nhãn cuối chồng lên nhau khi điểm cuối sát điểm trước).
 *
 * Nhãn đầu neo trái (`start`), nhãn cuối neo phải (`end`), nhãn giữa căn giữa (`middle`). Độ rộng nhãn ước theo số ký tự
 * (chữ số tabular ~ `CHAR_WIDTH` đơn vị viewBox ở cỡ 11px) nên hàm thuần, kiểm được không cần dựng SVG.
 */
const CHAR_WIDTH = 6.4
/** Khe tối thiểu giữa hai nhãn liền kề (đơn vị viewBox). */
const LABEL_GAP = 10

export type TickAnchor = 'start' | 'middle' | 'end'

function extent(x: number, text: string, anchor: TickAnchor): [number, number] {
  const width = text.length * CHAR_WIDTH
  if (anchor === 'start') return [x, x + width]
  if (anchor === 'end') return [x - width, x]
  return [x - width / 2, x + width / 2]
}

/**
 * Chỉ số các điểm được ghi nhãn ngày. Luôn giữ điểm đầu và điểm cuối; điểm giữa chỉ giữ khi cách đều theo `step` VÀ không
 * chạm nhãn đã giữ trước nó hay nhãn cuối.
 */
export function pickDateTickIndexes(xs: readonly number[], labels: readonly string[], step: number): number[] {
  const count = xs.length
  if (count === 0) return []
  const last = count - 1
  const kept = [0]
  const lastBox = last > 0 ? extent(xs[last], labels[last], 'end') : null
  let keptEnd = extent(xs[0], labels[0], 'start')[1]
  for (let i = step; i < last; i += step) {
    const [from, to] = extent(xs[i], labels[i], 'middle')
    if (from < keptEnd + LABEL_GAP) continue
    if (lastBox && to + LABEL_GAP > lastBox[0]) continue
    kept.push(i)
    keptEnd = to
  }
  if (last > 0) kept.push(last)
  return kept
}

/** Neo chữ của nhãn ở chỉ số `index` (đầu = start, cuối = end, giữa = middle). */
export function dateTickAnchor(index: number, count: number): TickAnchor {
  if (index === count - 1 && count > 1) return 'end'
  return index === 0 ? 'start' : 'middle'
}
