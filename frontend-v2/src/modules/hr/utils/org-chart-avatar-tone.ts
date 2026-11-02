/**
 * Màu vòng chữ viết tắt trên sơ đồ tổ chức, cố định theo người (ERPNext tô màu ảnh đại diện).
 *
 * Dùng token màu của theme (`chart-*`, `primary`) — đã có bản cho chế độ tối — chứ không mã màu cứng.
 * Viết TRỌN tên lớp để Tailwind quét thấy; ghép chuỗi kiểu `bg-chart-${n}` là mất lớp lúc dựng.
 */
const TONES = [
  'bg-chart-1/15 text-chart-1',
  'bg-chart-2/15 text-chart-2',
  'bg-chart-3/15 text-chart-3',
  'bg-chart-4/20 text-chart-4',
  'bg-primary/15 text-primary',
] as const

/** Cùng một id luôn ra cùng một màu; id âm / lẻ / không hữu hạn vẫn ra một màu hợp lệ. */
export function pickOrgChartAvatarTone(id: number): string {
  const index = Number.isFinite(id) ? Math.abs(Math.trunc(id)) % TONES.length : 0
  return TONES[index]
}
