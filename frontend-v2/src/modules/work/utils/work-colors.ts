/**
 * Bảng màu ĐẶT SẴN cho cột kanban, tag và giá trị nhãn tùy biến.
 *
 * §9 của `05-giao-dien.md` cấm nhập hex tự do: hex người dùng gõ vào không có
 * biến thể tối, bật nền tối là chữ đen trên nền đen. Ở đây mỗi màu là một cặp
 * class token đã kiểm ở cả hai chế độ nền; cột `color` dưới CSDL lưu đúng TÊN
 * màu (chuỗi ngắn), không lưu class.
 */
export const WORK_COLORS = [
  { value: 'slate', label: 'Xám' },
  { value: 'red', label: 'Đỏ' },
  { value: 'orange', label: 'Cam' },
  { value: 'amber', label: 'Vàng' },
  { value: 'lime', label: 'Xanh nõn' },
  { value: 'emerald', label: 'Xanh lá' },
  { value: 'teal', label: 'Xanh ngọc' },
  { value: 'sky', label: 'Xanh trời' },
  { value: 'blue', label: 'Xanh dương' },
  { value: 'violet', label: 'Tím' },
  { value: 'fuchsia', label: 'Hồng sen' },
  { value: 'rose', label: 'Hồng' },
] as const

export type WorkColor = (typeof WORK_COLORS)[number]['value']

//  Viết đủ chuỗi class cho từng màu — Tailwind quét mã nguồn theo văn bản, ghép
//  chuỗi kiểu `bg-${color}-500` là class không được sinh ra và chip mất màu.
const CHIP: Record<string, string> = {
  slate: 'bg-slate-500/10 text-slate-700 dark:text-slate-300',
  red: 'bg-red-500/10 text-red-700 dark:text-red-300',
  orange: 'bg-orange-500/10 text-orange-700 dark:text-orange-300',
  amber: 'bg-amber-500/10 text-amber-700 dark:text-amber-300',
  lime: 'bg-lime-500/10 text-lime-700 dark:text-lime-300',
  emerald: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  teal: 'bg-teal-500/10 text-teal-700 dark:text-teal-300',
  sky: 'bg-sky-500/10 text-sky-700 dark:text-sky-300',
  blue: 'bg-blue-500/10 text-blue-700 dark:text-blue-300',
  violet: 'bg-violet-500/10 text-violet-700 dark:text-violet-300',
  fuchsia: 'bg-fuchsia-500/10 text-fuchsia-700 dark:text-fuchsia-300',
  rose: 'bg-rose-500/10 text-rose-700 dark:text-rose-300',
}

const DOT: Record<string, string> = {
  slate: 'bg-slate-500',
  red: 'bg-red-500',
  orange: 'bg-orange-500',
  amber: 'bg-amber-500',
  lime: 'bg-lime-500',
  emerald: 'bg-emerald-500',
  teal: 'bg-teal-500',
  sky: 'bg-sky-500',
  blue: 'bg-blue-500',
  violet: 'bg-violet-500',
  fuchsia: 'bg-fuchsia-500',
  rose: 'bg-rose-500',
}

/** Class nền + chữ cho một chip màu. Màu lạ (dữ liệu cũ) rơi về xám. */
export function chipClass(color: string): string {
  return CHIP[color] ?? CHIP.slate
}

/** Class cho chấm tròn màu của cột kanban / list trên sidebar. */
export function dotClass(color: string): string {
  return DOT[color] ?? DOT.slate
}

/**
 * Màu của độ ưu tiên — CỐ ĐỊNH theo bậc, không cho người dùng đổi.
 * P1 đỏ, P2 cam, P3 xanh trời, P4 xám (đúng dải của Lark).
 */
export function priorityColor(priority: number): string {
  if (priority === 1) return 'red'
  if (priority === 2) return 'orange'
  if (priority === 3) return 'sky'
  if (priority === 4) return 'slate'
  return 'slate'
}
