/**
 * bao-CR-477 (bản cũ) — luật hiển thị danh mục hóa chất theo văn bản, CHÉP ĐÚNG bản ERP
 * (`frontend-v2/src/modules/procurement/utils/customs.ts`) để hai giao diện nói cùng một kiểu
 * khi lên bản chạy thật. Sửa luật ở đây thì sửa cả bên kia.
 */

/**
 * Độ NGHIÊM TRỌNG của từng danh sách, số nhỏ = nặng hơn: hoạt chất CẤM · tiền chất vũ khí hóa
 * học (PL III) · có NGƯỠNG khối lượng (PL IV) · phải công bố theo lô · chỉ có tên (PL I, II).
 * Mã lạ xếp cuối nhưng vẫn hiện — đừng giấu thứ mình chưa hiểu.
 */
const REGULATION_SEVERITY: Record<number, number> = { 10: 0, 3: 1, 4: 2, 11: 3, 1: 4, 2: 4 }

export function regulationSeverity(listCode: number): number {
  return REGULATION_SEVERITY[listCode] ?? 9
}

interface RegulationSortable {
  list_code: number
  threshold_kg: number | null
  name: string
}

/** Nặng nhất lên đầu; cùng danh sách thì ngưỡng THẤP lên trước; rồi tới tên. Trả mảng mới. */
export function sortRegulationsBySeverity<T extends RegulationSortable>(items: readonly T[]): T[] {
  return [...items].sort(
    (a, b) =>
      regulationSeverity(a.list_code) - regulationSeverity(b.list_code) ||
      (a.threshold_kg ?? Number.POSITIVE_INFINITY) - (b.threshold_kg ?? Number.POSITIVE_INFINITY) ||
      a.name.localeCompare(b.name, 'vi'),
  )
}

/**
 * Ngưỡng → «100 kg», «1.000 kg», «0,15 kg». Giữ tới 3 chữ số lẻ: Methyl isocyanate ngưỡng
 * 0,15 kg, làm tròn thành «0 kg» là nói ngược hẳn với luật. Rỗng / âm / không phải số → ''.
 */
export function formatThresholdKg(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value) || value < 0) return ''
  return `${value.toLocaleString('vi-VN', { maximumFractionDigits: 3 })} kg`
}

/** Hoạt chất cấm → «CẤM từ 2026»; nguồn không có năm thì chỉ «CẤM». */
export function formatBannedLabel(bannedYear: number | null | undefined): string {
  return bannedYear ? `CẤM từ ${bannedYear}` : 'CẤM'
}

/**
 * Lớp nhãn theo mức nặng, dùng lại đúng các lớp `.badge.*` có sẵn trong `index.css`: cấm +
 * tiền chất vũ khí hóa học đỏ (`err`) · có ngưỡng cam (`back`) · công bố theo lô xanh (`info`)
 * · chỉ có tên xám (`gray`). Trước đây ngoài «cấm» và «ngưỡng» mọi thứ đều xanh, nên tiền chất
 * vũ khí hóa học trông nhẹ ngang một thủ tục công bố.
 */
export function regulationBadgeClass(listCode: number): string {
  if (listCode === 10 || listCode === 3) return 'err'
  if (listCode === 4) return 'back'
  if (listCode === 11) return 'info'
  return 'gray'
}
