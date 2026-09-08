/**
 * Số ngày công GỢI Ý của một đơn nghỉ phép.
 *
 * ⚠️ Bản sao của `so_ngay_goi_y` ở `backend/app/modules/document/type_metadata.py`.
 * Hai bên phải ra CÙNG một con số: backend là chốt cuối (nó ghi xuống CSDL), còn
 * bản này chỉ để ô «Tổng số ngày» hiện gợi ý ngay lúc gõ mà không phải gọi API
 * sau mỗi lần đổi ngày. Sửa một bên thì sửa cả hai — bài kiểm ở
 * `suggested-day-count.test.ts` giữ đúng mấy mốc mà bản Python cũng kiểm.
 *
 * ⚠️ Cố ý KHÔNG trừ thứ Bảy / Chủ nhật / ngày lễ. Hệ chưa có bảng lịch làm việc,
 * mà mỗi pháp nhân lại làm việc khác nhau; đoán ra một con số trông có vẻ chính
 * xác còn tệ hơn đưa con số thô để người ta sửa. Ô này sửa đè được và người
 * duyệt là chốt cuối.
 */

/**
 * Số công của NGÀY ĐẦU và NGÀY CUỐI — khớp `START_DAY_WORK_CREDIT` /
 * `END_DAY_WORK_CREDIT` ở `backend/app/core/leave_codes.py`.
 *
 * ⚠️ **Hai bảng khác nhau** (vá 07/09/2026). Ô buổi nói MỐC, không nói buổi:
 * *bắt đầu buổi Sáng* là nghỉ trọn ngày đó, *kết thúc buổi Chiều* cũng là nghỉ
 * trọn ngày đó. Bản cũ tra chung một bảng `{full: 1, morning: .5, afternoon: .5}`
 * cho cả hai đầu nên đơn *«từ Sáng 05 đến hết 07»* gợi ý 2.5 thay vì 3 ngày.
 */
const START_DAY_CREDIT: Record<string, number> = {
  full: 1,
  morning: 1,
  afternoon: 0.5,
  //  Theo giờ: con số suy ra từ khoảng giờ, không suy ra được từ ô buổi.
  hourly: 0,
}

const END_DAY_CREDIT: Record<string, number> = {
  full: 1,
  morning: 0.5,
  afternoon: 1,
  hourly: 0,
}

/**
 * Nghỉ gọn trong MỘT ngày — hai ô buổi cùng nói về ngày ấy nên phải xét CẢ HAI.
 *
 * Hai mốc nửa ngày: bắt đầu ở nửa `0` (sáng) hay `1` (chiều), kết thúc ở nửa `0`
 * hay `1`; số nửa phủ được là `end − start + 1`. Lấy riêng ô đi như bản cũ thì
 * *«Cả ngày → Sáng»* ra nguyên một ngày trong khi người khai kết thúc lúc hết
 * buổi sáng — người lao động mất oan nửa ngày phép.
 */
function sameDayCredit(outgoing: string, incoming: string): number {
  if (outgoing === 'hourly' || incoming === 'hourly') return 0
  const start = outgoing === 'afternoon' ? 1 : 0
  const end = incoming === 'morning' ? 0 : 1
  return Math.max(0, (end - start + 1) * 0.5)
}

export function suggestedDayCount(
  fromDate: string | undefined,
  toDate: string | undefined,
  buoiDi: string | undefined,
  buoiVe: string | undefined,
): number {
  if (!fromDate || !toDate) return 0

  const d1 = new Date(`${fromDate}T00:00:00`)
  const d2 = new Date(`${toDate}T00:00:00`)
  if (Number.isNaN(d1.getTime()) || Number.isNaN(d2.getTime()) || d2 < d1) return 0

  const outgoing = buoiDi ?? 'full'
  const incoming = buoiVe ?? 'full'

  if (fromDate === toDate) return sameDayCredit(outgoing, incoming)

  const tronVen = Math.round((d2.getTime() - d1.getTime()) / 86_400_000) - 1
  return (
    Math.max(0, tronVen) +
    (START_DAY_CREDIT[outgoing] ?? 1) +
    (END_DAY_CREDIT[incoming] ?? 1)
  )
}

/**
 * Ô BẮT BUỘC của khối nghỉ phép — kiểm khi bấm «Tiếp tục» ở bước Thông tin chính.
 *
 * Để ở đây chứ không ở tệp component: tệp component chỉ nên export component,
 * nếu không `react-refresh` mất khả năng nạp nóng cả tệp đó.
 *
 * Backend là chốt cuối (`type_metadata._kiem_nghi_phep`) — danh sách này chỉ để
 * người dùng thấy lỗi ngay tại ô thay vì sau một vòng mạng.
 */
export const LEAVE_FIELDS = [
  'leave.from_date',
  'leave.to_date',
  'leave.reason',
] as const
