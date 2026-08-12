import { QueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'

/**
 * Cấu hình mặc định cho React Query — áp cho toàn hệ thống, module không tự chỉnh
 * trừ khi có lý do rõ ràng (vd danh mục ít đổi thì tăng staleTime tại chỗ).
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Dữ liệu ERP đổi liên tục nhưng không tới mức realtime: 30 giây là cân bằng
      // giữa "không gọi lại API mỗi lần chuyển tab" và "số liệu không quá cũ".
      staleTime: 30_000,
      retry: (failureCount, error) => {
        const status = (error as AxiosError).response?.status
        // 4xx là lỗi nghiệp vụ/phân quyền — thử lại cũng vẫn hỏng, đừng phí request.
        if (status && status >= 400 && status < 500) return false
        return failureCount < 2
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      // Lỗi mutation đã được http-client toast sẵn — ở đây không retry để tránh
      // gửi trùng lệnh tạo/duyệt phiếu.
      retry: false,
    },
  },
})
