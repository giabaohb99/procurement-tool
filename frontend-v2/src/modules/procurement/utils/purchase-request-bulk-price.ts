// Ô «Giá mới» của khối «Áp 1 NCC cho nhiều dòng» trên chi tiết YCMH.

/** Ô giá → số. Trống, không phải số, hoặc âm thì `undefined` = giữ nguyên giá cũ. */
export function parsePriceInput(raw: string): number | undefined {
  const trimmed = raw.trim()
  if (!trimmed) return undefined
  const value = Number(trimmed)
  return Number.isFinite(value) && value >= 0 ? value : undefined
}

/**
 * bao-CR-576 — dòng này có ĐỔI giá thật không, để tô nổi dòng đó ngay trên bảng.
 *
 * Đại ca chê giá nằm tận mép phải, người ta dễ bỏ qua. Gõ đúng bằng giá cũ, gõ sai, hay để
 * trống đều là «giữ nguyên» → `null`, không tô gì; chỉ khi giá mới khác giá cũ mới báo.
 */
export function describeBulkPriceChange(
  currentPrice: number | null | undefined,
  raw: string,
): { next: number } | null {
  const next = parsePriceInput(raw)
  if (next === undefined) return null
  if (next === Number(currentPrice ?? 0)) return null
  return { next }
}
