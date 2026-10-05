/**
 * bao-CR-474 — ô «Trưởng bộ phận (TBP) / Người liên hệ» của YCMH hiện AI.
 *
 * Luật đại ca chốt 24/09/2026: ô này LUÔN phải hiện một người. Đã chọn thì người
 * đó; chưa chọn (`head_of_dept_id = 0` — phiếu mới, hoặc vừa đổi người yêu cầu sang
 * phòng khác) thì trưởng phòng mặc định của phòng (`Department.manager_id`), vì đó
 * chính là người backend tự điền lúc lưu / gửi duyệt. Hiện trống trong khi dữ liệu
 * lưu xuống lại có người là màn hình nói sai.
 *
 * Chỉ lùi về mặc định khi đang SỬA: phiếu đã khóa hiện đúng tên đã lưu, không đoán.
 */
export interface DeptHeadRef {
  head_of_dept: string
  head_of_dept_id: number
}

export function resolveShownDeptHead(
  saved: DeptHeadRef,
  editing: boolean,
  fallback?: DeptHeadRef | null,
): DeptHeadRef {
  if (editing && !saved.head_of_dept_id && fallback?.head_of_dept_id) {
    return { head_of_dept: fallback.head_of_dept, head_of_dept_id: fallback.head_of_dept_id }
  }
  return { head_of_dept: saved.head_of_dept, head_of_dept_id: saved.head_of_dept_id }
}

/**
 * bao-CR-590 — ghi THẬT xuống phiếu người đang hiện ở hai ô TBP + «Trưởng phòng phê duyệt».
 *
 * Trước đây màn hình HIỆN TBP mặc định ở cả hai ô nhưng bản nháp vẫn giữ id 0, nên lúc tạo
 * phiếu, người dùng thấy ô đã có người mà dữ liệu gửi lên thì trống — và bộ kiểm lúc gửi duyệt
 * đọc bản nháp nên tưởng thiếu. Ô nào người dùng đã tự chọn thì giữ nguyên, không đè.
 */
export function fillApproverDefaults<T extends DeptHeadRef & { approver_employee_id?: number | null }>(
  draft: T,
  shown: DeptHeadRef,
): T {
  const headId = draft.head_of_dept_id || shown.head_of_dept_id
  return {
    ...draft,
    head_of_dept_id: headId,
    head_of_dept: draft.head_of_dept_id ? draft.head_of_dept : shown.head_of_dept || draft.head_of_dept,
    approver_employee_id: draft.approver_employee_id || headId,
  }
}
