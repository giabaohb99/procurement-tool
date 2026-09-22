import type { TimelineState } from '@/shared/ui/timeline-item'
import { formatDateTime } from '@/shared/utils/format-date'
import { SEAL_STATUS, type SealRequest } from '../types/seal-request'

/** Một chặng của phiếu đóng dấu: Tạo phiếu → TBP duyệt → Văn thư đóng dấu. */
export interface SealStage {
  key: string
  title: string
  state: TimelineState
  /** Mốc thời gian đã xảy ra, đã định dạng; rỗng khi chưa tới chặng. */
  time: string
  /** Người thực hiện chặng; rỗng khi chưa biết. */
  actor: string
  /** Nhãn đứng trước tên người ("Người lập", "Chờ duyệt bởi"). Rỗng thì không dựng. */
  actorLabel: string
  /** Lý do phiếu dừng ở chặng này — chỉ có ở chặng `stopped`. */
  reason: string
}

export interface BuildSealStagesOptions {
  /** Đang mở biểu mẫu sửa — xem chú thích `editing` ở đầu hàm. */
  editing?: boolean
  /** Lý do bị từ chối / trả về, moi từ nhật ký (`extractSealStopReason`). */
  stopReason?: string
}

/**
 * Dựng TIẾN TRÌNH của phiếu đóng dấu — *ai lập, ai duyệt, ai đóng dấu*.
 *
 * Thay cho thẻ bốn dòng "TBP duyệt / Duyệt lúc / Văn thư / Hoàn tất lúc": bốn ô
 * đó đọc ra bốn mẩu rời, phiếu mới thì cả bốn là dấu gạch, và người lập không
 * thấy được CHÍNH MÌNH ở đầu chuỗi. Xếp theo chặng thì ô trống thành câu trả lời
 * ("Chờ Trưởng bộ phận duyệt") và thứ tự trước-sau tự nói ra luồng.
 *
 * Hàm THUẦN, không đụng React — bài kiểm chạy thẳng vào luật nghiệp vụ.
 *
 * ⚠️ `editing` = đang mở biểu mẫu sửa. Khi đó tên TBP duyệt của chặng CHƯA duyệt
 * bị bỏ đi: chính ô chọn trong biểu mẫu mới là giá trị thật, bày thêm tên đã lưu
 * ở đây thì đổi ô chọn xong màn hình có hai cái tên cho một vai. Tên của chặng
 * ĐÃ duyệt thì giữ — đó là dấu vết, không phải dự định.
 */
export function buildSealStages(
  request: SealRequest,
  { editing = false, stopReason = '' }: BuildSealStagesOptions = {},
): SealStage[] {
  const s = request.status

  const stages: SealStage[] = [
    {
      key: 'created',
      title: s === SEAL_STATUS.draft ? 'Lập phiếu (nháp)' : 'Lập phiếu',
      state: 'done',
      time: formatDateTime(request.created_at),
      actor: request.requester,
      actorLabel: 'Người lập',
      reason: '',
    },
  ]

  //  Chặng DUYỆT. Trạng thái phiếu là nguồn chính, `approved_at` chỉ là mốc giờ:
  //  phiếu đi qua luồng duyệt nhiều bước được đẩy sang "Đã duyệt" mà không ghi
  //  mốc duyệt một-bước, xem mốc là điều kiện thì phiếu duyệt rồi vẫn hiện "Chờ".
  const approved =
    Boolean(request.approved_at) ||
    s === SEAL_STATUS.approved ||
    s === SEAL_STATUS.completed

  if (s === SEAL_STATUS.rejected || s === SEAL_STATUS.returned) {
    //  Dừng ở đây: hai kết cục này KHÔNG có chặng đóng dấu nào nữa. Giữ lại dòng
    //  "Chờ Văn thư đóng dấu" bên dưới là hứa một việc đã chết.
    stages.push({
      key: 'approve',
      title: s === SEAL_STATUS.rejected ? 'Bị từ chối' : 'Trả về yêu cầu chỉnh sửa',
      state: 'stopped',
      time: formatDateTime(request.approved_at),
      actor: request.approver_name,
      actorLabel: 'Người xử lý',
      reason: stopReason,
    })
    return stages
  }

  stages.push({
    key: 'approve',
    title: approved ? 'Trưởng bộ phận đã duyệt' : 'Chờ Trưởng bộ phận duyệt',
    state: approved ? 'done' : 'pending',
    time: formatDateTime(request.approved_at),
    actor: editing && !approved ? '' : request.approver_name,
    actorLabel: approved ? 'Người duyệt' : 'Sẽ trình',
    reason: '',
  })

  const completed = s === SEAL_STATUS.completed || Boolean(request.completed_at)

  stages.push({
    key: 'stamp',
    title: completed ? 'Văn thư đã đóng dấu' : 'Chờ Văn thư đóng dấu',
    state: completed ? 'done' : 'pending',
    time: formatDateTime(request.completed_at),
    actor: request.completed_by_name,
    actorLabel: 'Văn thư',
    reason: '',
  })

  //  Phiếu ĐÃ HỦY: bỏ những chặng chưa tới lượt (không bao giờ tới nữa), giữ
  //  nguyên dấu vết của chặng đã xong rồi đóng bằng một dòng dừng.
  if (s === SEAL_STATUS.cancelled) {
    return [
      ...stages.filter((stage) => stage.state !== 'pending'),
      {
        key: 'cancel',
        title: 'Đã hủy phiếu',
        state: 'stopped',
        time: '',
        actor: '',
        actorLabel: '',
        reason: stopReason,
      },
    ]
  }

  return stages
}
