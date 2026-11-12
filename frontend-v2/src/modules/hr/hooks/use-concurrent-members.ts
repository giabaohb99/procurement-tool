import { useQuery } from '@tanstack/react-query'

import { concurrentMembersApi, type ConcurrentMembersParams } from '../api/concurrent-members-api'

//  Khóa CỤC BỘ, không vào `shared/constants/query-keys.ts` (cho phép ở `frontend-v2/.claude/rules/naming.md`: khóa chỉ
//  một hook dùng): bắt đầu bằng `['hr']` nên mọi chỗ nạp lại bằng `queryKeys.hr.all` (lưu / xóa dòng kiêm nhiệm ở tab
//  hồ sơ, đổi phòng, đổi pháp nhân) quét luôn bảng này mà không cần khai thêm ở đâu. Giai đoạn 04 đang sửa tệp khóa
//  chung nên giai đoạn 05 không thêm vào đó; điều phối có thể dời về sau.
const concurrentMembersKey = (params: ConcurrentMembersParams) => ['hr', 'concurrent-members', params] as const

/**
 * Người đang kiêm nhiệm ở một phòng ban (bảng "Kiêm nhiệm tại phòng này"). `enabled` để màn tự tắt khi thiếu quyền
 * `employee.read` — 403 trên GET không bật toast nên cứ gọi thì bảng chỉ lặng lẽ rỗng.
 */
export function useConcurrentMembers(params: ConcurrentMembersParams, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: concurrentMembersKey(params),
    queryFn: () => concurrentMembersApi.list(params),
    enabled: params.department_id > 0 && (options.enabled ?? true),
  })
}
