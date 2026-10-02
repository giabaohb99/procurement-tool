import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { authService } from '@/core/auth/auth-service'
import { useAuthStore } from '@/core/auth/auth-store'
import { queryKeys } from '@/shared/constants/query-keys'
import { reportAccessApi } from '../api/report-access-api'
import type { GrantReportAccessInput } from '../types/report-access'

/**
 * Cấu hình «ai xem được báo cáo nào» — tab Báo cáo của Phân quyền tài khoản
 * (phase 06, kế hoạch `plans/261002-0836-phan-quyen-tung-bao-cao`).
 */
export function useReportAccessList() {
  return useQuery({
    queryKey: queryKeys.system.reportAccess(),
    queryFn: () => reportAccessApi.list(),
  })
}

/**
 * Nạp lại hồ sơ của CHÍNH người đang đăng nhập sau khi gán/thu hồi — phòng
 * trường hợp admin vừa tự gán/cấm CHÍNH MÌNH. `report_keys` quyết định menu
 * (`useNavContext` đọc từ `useAuthStore`, xem `src/core/authorization/
 * use-permission.ts`) nằm trong store **zustand**, KHÔNG nằm trong cache
 * React Query — `invalidateQueries({queryKey: queryKeys.auth.me()})` một
 * mình KHÔNG đủ: nó chỉ làm `useQuery(auth.me())` ở Trang cá nhân nạp lại
 * (và chỉ khi trang đó đang MỞ để nhận kết quả), không có tác dụng gì trên
 * chính màn Phân quyền tài khoản đang gọi hàm này. Phải gọi thẳng
 * `/api/auth/me` rồi ghi kết quả vào store để menu đổi ngay trên trang đang
 * mở. Lỗi mạng ở đây NUỐT ÂM THẦM: không chặn toast thành công của việc
 * gán/thu hồi, menu chỉ cập nhật trễ tới lần tải lại kế tiếp (đăng nhập lại /
 * làm mới token).
 */
async function refreshAuthUser(): Promise<void> {
  try {
    const user = await authService.me()
    useAuthStore.getState().setUser(user)
  } catch {
    // nuốt im — xem giải thích ở trên
  }
}

/**
 * Gán thêm cho MỘT báo cáo. Trùng (báo cáo, chủ thể, chiều) còn sống thì
 * backend SỬA dòng đó (`updated`), không đẻ dòng mới — `skipped` là phần
 * backend ÂM THẦM bỏ qua (chủ thể không tồn tại), phải báo riêng kẻo người
 * gán tưởng đã gán cho cả danh sách.
 */
export function useGrantReportAccess(reportKey: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: GrantReportAccessInput) => reportAccessApi.grant(reportKey, payload),
    onSuccess: (result) => {
      if (result.skipped.length > 0) {
        toast.warning(
          `Đã gán cho ${result.created + result.updated}, bỏ qua ${result.skipped.length} ` +
            'đối tượng không tìm thấy',
        )
      } else {
        toast.success(`Đã gán cho ${result.created + result.updated} đối tượng`)
      }
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.reportAccess() })
      void refreshAuthUser()
    },
  })
}

/** Thu hồi MỘT dòng — không gắn theo báo cáo nào vì `DELETE` chỉ cần `accessId`. */
export function useRevokeReportAccess() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ accessId, reason }: { accessId: number; reason: string }) =>
      reportAccessApi.revoke(accessId, reason),
    onSuccess: () => {
      toast.success('Đã thu hồi quyền xem báo cáo')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.reportAccess() })
      void refreshAuthUser()
    },
  })
}
