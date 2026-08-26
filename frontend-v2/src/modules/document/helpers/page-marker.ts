/**
 * THẺ THAY ĐƯỢC trong đầu trang / chân trang.
 *
 * Danh sách gốc khai ở backend (`version_model.THE_DAU_CHAN_TRANG`); ở đây chép
 * lại đúng bộ đó để giao diện gợi ý và thay tại chỗ. Thêm thẻ mới thì phải sửa
 * cả hai nơi, nếu không người dùng gõ thẻ đúng mà chỗ này ra chữ, chỗ kia ra
 * thẻ thô.
 */
export interface PageMarkerValues {
  /** Số trang hiện tại. Bỏ trống ở nơi chưa biết (trình soạn thảo). */
  trang?: number | string
  tongTrang?: number | string
  soHieu?: string
  tenVanBan?: string
  ngay?: string
}

export const PAGE_MARKERS = [
  { the: '{{trang}}', mo_ta: 'Số trang' },
  { the: '{{tong_trang}}', mo_ta: 'Tổng số trang' },
  { the: '{{so_hieu}}', mo_ta: 'Số hiệu văn bản' },
  { the: '{{ten_van_ban}}', mo_ta: 'Trích yếu' },
  { the: '{{ngay}}', mo_ta: 'Ngày in' },
] as const

/**
 * Thay thẻ trong một dòng đầu/chân trang.
 *
 * Thẻ không có giá trị thì thay bằng chuỗi rỗng chứ KHÔNG để nguyên thẻ thô:
 * in ra tờ giấy mang dòng `{{so_hieu}}` là lỗi ai cũng thấy, còn chỗ trống thì
 * chỉ là thiếu thông tin.
 */
export function fillPageMarkers(mau: string, values: PageMarkerValues): string {
  if (!mau) return ''

  const bang: Record<string, string> = {
    '{{trang}}': values.trang === undefined ? '' : String(values.trang),
    '{{tong_trang}}': values.tongTrang === undefined ? '' : String(values.tongTrang),
    '{{so_hieu}}': values.soHieu ?? '',
    '{{ten_van_ban}}': values.tenVanBan ?? '',
    '{{ngay}}': values.ngay ?? '',
  }

  return Object.entries(bang).reduce(
    (chuoi, [the, value]) => chuoi.split(the).join(value),
    mau,
  )
}

/** Có ô nào được khai không — dùng để biết có phải vẽ dải đầu/chân trang hay không. */
export function hasPageMarkerContent(...o: (string | undefined)[]): boolean {
  return o.some((chuoi) => Boolean(chuoi && chuoi.trim()))
}
