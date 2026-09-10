/**
 * Bảng màu trạng thái dùng chung cho MỌI phân hệ.
 *
 * Nhóm theo Ý NGHĨA chứ không theo từng mã: mỗi loại chứng từ có bộ mã riêng
 * nhưng người đọc chỉ cần phân biệt vài tình huống — trung tính, đang chờ, đang
 * chạy, đã xong, bị chặn.
 *
 * Trước đây khai riêng trong `procurement/components/document-status-badge.tsx`.
 * Tách ra khi phân hệ Tài chính cần đúng bảng này: chép sang là hai phân hệ lệch
 * màu nhau từ lần sửa đầu tiên, mà người dùng đọc "vàng = đang chờ" theo thói
 * quen chứ không đọc tên phân hệ.
 *
 * bao-CR-363 (10/09/2026): thêm 5 tông. Năm tông đầu quá ÍT cho chuỗi mua hàng —
 * `dispatched` · `purchased` · `completed` · `received` đều rơi vào `done`, còn
 * `submitted` · `rejected` · `processing` · `purchasing` đều rơi vào `pending`,
 * nên trên màn danh sách hai phiếu ở hai mốc khác hẳn nhau nhìn ra y hệt. Khách
 * báo lỗi này trên prod (ticket 38), bản v1 đã vá cùng ngày.
 *
 * ⚠️ Luật khi thêm tông mới: một mốc và mốc LIỀN KỀ nó trong vòng đời phải xa
 * nhau trên vòng màu. Thêm tông na ná tông đã có là quay lại đúng lỗi này.
 *
 * ⚠️ TÔ ĐẶC, CHỮ TRẮNG — không dùng nền mờ `/10` nữa. Bản cũ (`bg-warning/10
 * text-warning`) nhìn nhợt nhạt trên màn danh sách: chữ huy hiệu nhỏ và nền chỉ
 * 10% độ đậm nên gần như hòa vào nền bảng, phải nhìn kỹ mới ra màu. Khách phản
 * hồi đúng điểm này ngày 10/09/2026, cả hai bản v1 và v2 đổi cùng lúc.
 *
 * ⚠️ Mọi màu dưới đây đều chọn ở bậc ĐẬM (600/700/900) để chữ trắng đạt tương
 * phản >= 4,5:1 (ngưỡng WCAG AA cho chữ nhỏ). Bậc tươi 500 chỉ được ~3:1 — đừng
 * "làm sáng cho vui mắt", nó thành chữ nhòe. Hex khớp đúng bản v1
 * (`frontend/src/index.css`, các lớp `.badge.*`) để hai bản không lệch màu.
 */
export const TONE_CLASS = {
  /** Xám — chưa vào luồng (nháp). */
  neutral: 'bg-slate-500 text-white',
  /** Hổ phách — đang NẰM CHỜ người khác nhận (chờ duyệt). */
  pending: 'bg-amber-700 text-white',
  /** Xanh dương — đã qua cửa duyệt, đang chạy tiếp. */
  progress: 'bg-sky-700 text-white',
  /** Xanh lá — đã xong khâu đó. */
  done: 'bg-green-700 text-white',
  /** Đỏ — mốc KHÓA (từ chối, hủy). */
  danger: 'bg-red-700 text-white',
  /** Tím — đã giao việc cho người khác làm tiếp (điều phối). */
  handoff: 'bg-violet-600 text-white',
  /** Hồng sen — đang chạy thật, có người đang làm; khác `pending` là "nằm chờ ai đó nhận". */
  active: 'bg-pink-600 text-white',
  /** Xanh mòng — xong MỘT PHẦN: có kết quả nhưng chưa phủ hết (nhận một phần, mua một phần). */
  partial: 'bg-teal-700 text-white',
  /**
   * Cam — bị trả lại để sửa. Cố ý KHÔNG dùng `danger`: đỏ là mốc khóa phiếu (từ chối),
   * còn trả lại thì sửa rồi gửi duyệt lại được — hai thứ đó không được nhìn giống nhau.
   */
  returned: 'bg-orange-700 text-white',
  /**
   * Xanh lá ĐẬM NHẤT — mốc CUỐI, phiếu đã đóng. Đậm hơn `done` một bậc vì hai mốc này
   * đứng liền nhau trong vòng đời (Đã mua hàng → Hoàn thành) nên phải khác nhau, mà đổi
   * sang hẳn màu khác thì mất nghĩa "xong". Càng về cuối càng đậm là cách phân biệt
   * đọc được ngay.
   */
  closed: 'bg-green-900 text-white',
} as const

export type StatusTone = keyof typeof TONE_CLASS
