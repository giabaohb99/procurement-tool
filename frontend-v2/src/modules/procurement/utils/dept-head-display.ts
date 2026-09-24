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
