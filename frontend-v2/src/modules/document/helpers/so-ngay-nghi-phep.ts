/**
 * Số ngày công GỢI Ý của một đơn nghỉ phép.
 *
 * ⚠️ Bản sao của `so_ngay_goi_y` ở `backend/app/modules/document/type_metadata.py`.
 * Hai bên phải ra CÙNG một con số: backend là chốt cuối (nó ghi xuống CSDL), còn
 * bản này chỉ để ô «Tổng số ngày» hiện gợi ý ngay lúc gõ mà không phải gọi API
 * sau mỗi lần đổi ngày. Sửa một bên thì sửa cả hai — bài kiểm ở
 * `so-ngay-nghi-phep.test.ts` giữ đúng mấy mốc mà bản Python cũng kiểm.
 *
 * ⚠️ Cố ý KHÔNG trừ thứ Bảy / Chủ nhật / ngày lễ. Hệ chưa có bảng lịch làm việc,
 * mà mỗi pháp nhân lại làm việc khác nhau; đoán ra một con số trông có vẻ chính
 * xác còn tệ hơn đưa con số thô để người ta sửa. Ô này sửa đè được và người
 * duyệt là chốt cuối.
 */

/** Số công của mỗi buổi — khớp `CONG_CUA_BUOI` bên backend. */
const CONG_CUA_BUOI: Record<string, number> = {
  full: 1,
  morning: 0.5,
  afternoon: 0.5,
}

export function soNgayGoiY(
  tuNgay: string | undefined,
  denNgay: string | undefined,
  buoiDi: string | undefined,
  buoiVe: string | undefined,
): number {
  if (!tuNgay || !denNgay) return 0

  const d1 = new Date(`${tuNgay}T00:00:00`)
  const d2 = new Date(`${denNgay}T00:00:00`)
  if (Number.isNaN(d1.getTime()) || Number.isNaN(d2.getTime()) || d2 < d1) return 0

  const congDi = CONG_CUA_BUOI[buoiDi ?? 'full'] ?? 1
  const congVe = CONG_CUA_BUOI[buoiVe ?? 'full'] ?? 1

  //  Cùng một ngày thì hai ô buổi nói về CÙNG một buổi — lấy một cái.
  if (tuNgay === denNgay) return congDi

  const tronVen = Math.round((d2.getTime() - d1.getTime()) / 86_400_000) - 1
  return Math.max(0, tronVen) + congDi + congVe
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
