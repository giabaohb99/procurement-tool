/** 1cm ở 96dpi — cùng hệ quy đổi với khổ A4 dựng trong `rich-text-editor.tsx`. */
export const PX_PER_CM = 96 / 2.54

/** Kéo con trượt tới đâu cũng nhích theo từng 1/4 cm, khỏi căn tay cho tròn số. */
export const RULER_SNAP_PX = PX_PER_CM / 4

/** Số vạch cm phủ hết một chiều dài (px) của trang giấy. */
export function cmMarks(lengthPx: number): number[] {
  return Array.from({ length: Math.floor(lengthPx / PX_PER_CM) + 1 }, (_, cm) => cm)
}
