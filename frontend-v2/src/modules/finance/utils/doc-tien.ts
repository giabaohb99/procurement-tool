/**
 * Đọc số tiền thành chữ (tiếng Việt) cho bản in Đề nghị thanh toán.
 *
 * Chép NGUYÊN VĂN từ bản v1 (`frontend/src/pages/PrintPaymentRequest.tsx`) để
 * bản in v2 đọc ra đúng từng chữ như bản đang chạy thật — kế toán đối chiếu số
 * bằng chữ với chứng từ cũ, lệch một chữ là phải in lại. Có sửa quy tắc đọc thì
 * sửa cả hai nơi cho tới khi bản v1 được tắt.
 */
export function docTien(amount: number): string {
  let n = Math.round(Number(amount) || 0)
  if (n <= 0) return 'Không đồng'
  const d = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín']
  const readTriple = (num: number, showH: boolean) => {
    const tram = Math.floor(num / 100), chuc = Math.floor((num % 100) / 10), dv = num % 10
    const p: string[] = []
    if (showH || tram > 0) p.push(d[tram] + ' trăm')
    if (chuc === 0) { if (dv > 0) p.push((showH || tram > 0 ? 'lẻ ' : '') + d[dv]) }
    else if (chuc === 1) { p.push('mười'); if (dv === 5) p.push('lăm'); else if (dv > 0) p.push(d[dv]) }
    else { p.push(d[chuc] + ' mươi'); if (dv === 1) p.push('mốt'); else if (dv === 5) p.push('lăm'); else if (dv > 0) p.push(d[dv]) }
    return p.join(' ')
  }
  const groups: number[] = []
  while (n > 0) { groups.push(n % 1000); n = Math.floor(n / 1000) }
  const scale = ['', ' nghìn', ' triệu', ' tỷ', ' nghìn tỷ']
  const out: string[] = []
  for (let i = groups.length - 1; i >= 0; i--) {
    if (groups[i] === 0) continue
    out.push(readTriple(groups[i], i < groups.length - 1) + scale[i])
  }
  const s = out.join(' ').replace(/\s+/g, ' ').trim()
  return s.charAt(0).toUpperCase() + s.slice(1) + ' đồng chẵn'
}
