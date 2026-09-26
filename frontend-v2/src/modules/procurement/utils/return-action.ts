// bao-CR-498 — MỘT nút «Trả về» cho hai đường trả khác nhau của YCMH / YCBG.
//
// Sau bao-CR-489 (đổi nhãn «Trả về phòng lập» thành «Trả về») màn chi tiết có HAI nút cùng
// tên đứng cạnh nhau, đại ca chốt 26/09/2026: chỉ một nút, còn xử lý thì tùy trường hợp:
//   · `requester`  — trả người lập sửa rồi gửi duyệt lại (đường luồng duyệt, phiếu đổi trạng thái);
//   · `department` — trả cả phiếu về phòng lập tự xử lý (bao-CR-414, trạng thái giữ nguyên);
//   · `choose`     — cả hai đường đều mở → hỏi người bấm muốn trả đi đâu;
//   · `null`       — không đường nào → không bày nút.

export type ReturnTarget = 'requester' | 'department'
export type ReturnResolution = ReturnTarget | 'choose' | null

export function resolveReturnAction(canReturnToRequester: boolean, canReturnToDepartment: boolean): ReturnResolution {
  if (canReturnToRequester && canReturnToDepartment) return 'choose'
  if (canReturnToRequester) return 'requester'
  if (canReturnToDepartment) return 'department'
  return null
}

export const RETURN_TARGET_LABELS: Record<ReturnTarget, { title: string; description: string }> = {
  requester: {
    title: 'Trả người lập sửa lại',
    description: 'Phiếu về trạng thái «Trả về», người lập sửa nội dung rồi gửi duyệt lại từ đầu.',
  },
  department: {
    title: 'Trả phòng lập tự xử lý',
    description: 'Phiếu giữ nguyên trạng thái, gỡ nhân sự thu mua đang phụ trách; phòng lập tự mua.',
  },
}
