/**
 * VÙNG THẢ trong MỘT dòng cây khi kéo thả — dùng chung cho mọi cây dựng trên
 * `TreeView` (thư mục văn bản là nơi dùng đầu tiên, phase 05 nối dài).
 *
 * - `into`: thả LÀM CON của dòng này (đổi cha) — hành vi cũ, một vùng phủ
 *   trọn dòng.
 * - `before`/`after`: thả TRƯỚC/SAU dòng này, đứng NGANG HÀNG (đổi thứ tự anh
 *   em cùng cha, không đổi cha) — mép trên/dưới dòng.
 */
export type DropZone = 'before' | 'into' | 'after'

export interface DropZoneOptions {
  /** Dòng này CÓ nhận đổi CHA hay không — ví dụ `dropState(node) === 'valid'`. */
  canDropInto: boolean
  /** Dòng này CÓ nhận đổi THỨ TỰ (anh em cùng cha) hay không. */
  canReorder: boolean
}

/** Mép trên/dưới dành cho đổi thứ tự — 30% mỗi mép, 40% giữa dành cho đổi cha. */
const EDGE_RATIO = 0.3

/**
 * Tính vùng thả theo VỊ TRÍ CON TRỎ trong một dòng — hàm THUẦN, nhận sẵn tỉ lệ
 * Y đã chuẩn hóa (`ratioY`, 0 = mép trên dòng · 1 = mép dưới) thay vì tự đọc
 * `getBoundingClientRect`, để test không cần dựng DOM thật. `tree-row.tsx` là
 * nơi DUY NHẤT gọi hàm này lúc `dragover`/`drop`.
 *
 * - Không khả năng nào hợp lệ (`!canDropInto && !canReorder`) → `null`, nơi
 *   gọi không thả được gì vào dòng này.
 * - Chỉ ĐỔI CHA hợp lệ → cả dòng là vùng `into` (đúng hành vi TRƯỚC khi có
 *   đổi thứ tự, không đổi hành vi cũ).
 * - Chỉ ĐỔI THỨ TỰ hợp lệ (đổi cha không hợp lệ với đúng dòng này, ví dụ khác
 *   pháp nhân hoặc vượt cấp) → chia đôi dòng theo `ratioY = 0.5`, không có
 *   vùng `into` ở giữa vì nó không hợp lệ.
 * - CẢ HAI cùng hợp lệ (thường gặp nhất: kéo qua một ANH EM cùng cha, thứ vừa
 *   là đích đổi thứ tự vừa có thể là đích đổi cha) → chia ba, mép trên/dưới
 *   `EDGE_RATIO` là đổi thứ tự, phần giữa là đổi cha.
 */
export function resolveDropZone(ratioY: number, options: DropZoneOptions): DropZone | null {
  const { canDropInto, canReorder } = options

  if (!canReorder && !canDropInto) return null
  if (!canReorder) return 'into'
  if (!canDropInto) return ratioY < 0.5 ? 'before' : 'after'

  if (ratioY < EDGE_RATIO) return 'before'
  if (ratioY > 1 - EDGE_RATIO) return 'after'
  return 'into'
}
