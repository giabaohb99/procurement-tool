import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { fetchJobRuns, fetchJobs, type JobListFilters, type JobRunFilters } from '../api/job-run-api'

/**
 * Danh sách việc nền kèm lần chạy gần nhất. Tự nạp lại mỗi phút khi màn đang mở: lần chạy kế tiếp và trạng thái
 * *đang chạy* đổi theo giờ, nhìn một bảng đứng yên từ sáng thì đọc sai.
 */
export function useJobs(params: JobListFilters) {
  return useQuery({
    queryKey: queryKeys.system.jobs(params as Record<string, unknown>),
    queryFn: () => fetchJobs(params),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  })
}

/** Lịch sử chạy của MỘT việc; tắt khi chưa chọn việc nào (`code` rỗng). */
export function useJobRuns(code: string, params: JobRunFilters) {
  return useQuery({
    queryKey: queryKeys.system.jobRuns(code, params as Record<string, unknown>),
    queryFn: () => fetchJobRuns(code, params),
    enabled: code !== '',
    //  Giữ trang cũ khi lật trang / đổi ô lọc của CÙNG một việc; đổi sang việc khác thì KHÔNG giữ — kẻo ngăn của việc
    //  mới hiện tạm lịch sử của việc cũ.
    placeholderData: (previous, previousQuery) => (previousQuery?.queryKey[3] === code ? previous : undefined),
    staleTime: 15 * 1000,
  })
}
