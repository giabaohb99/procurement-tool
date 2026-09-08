import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workTaskApi } from '../api/work-task-api'
import type { WorkBoard, WorkTaskLink } from '../types/work'

/**
 * Thêm / bỏ MŨI TÊN PHỤ THUỘC trên Gantt (B-15).
 *
 * Không có hook ĐỌC: mũi tên nằm sẵn trong payload `board` (khóa
 * `queryKeys.work.board`), nên cả hai mutation chỉ việc vá đúng khóa đó.
 *
 * Cả hai đều **cập nhật lạc quan**. Với việc thêm thì đây không phải chuyện làm
 * đẹp: máy chủ mất một nhịp mới trả về, mà trong nhịp ấy người dùng vừa buông
 * chuột và đang nhìn thẳng vào chỗ mũi tên sẽ hiện — trống trơn nghĩa là "thao
 * tác trượt rồi", và họ kéo lại lần nữa. Lần thứ hai chắc chắn ăn 400 «đã có
 * phụ thuộc».
 *
 * Mũi tên tạm mang **id âm** để phân biệt với id thật; nó sống đúng tới lúc
 * `invalidate` kéo bản thật về.
 */

/** Id giả cho mũi tên đang chờ máy chủ xác nhận — âm nên không đụng id thật. */
let tempId = -1

export function useCreateTaskLink(listId: number) {
  const queryClient = useQueryClient()
  const boardKey = queryKeys.work.board(listId)

  return useMutation({
    mutationFn: (values: Parameters<typeof workTaskApi.createLink>[0]) =>
      workTaskApi.createLink(values),

    onMutate: async (values) => {
      await queryClient.cancelQueries({ queryKey: boardKey })
      const snapshot = queryClient.getQueryData<WorkBoard>(boardKey)
      if (snapshot) {
        const draft: WorkTaskLink = {
          id: tempId--,
          list_id: listId,
          predecessor_id: values.predecessor_id,
          successor_id: values.successor_id,
          link_type: values.link_type ?? 1,
          lag_days: values.lag_days ?? 0,
        }
        queryClient.setQueryData<WorkBoard>(boardKey, {
          ...snapshot,
          links: [...snapshot.links, draft],
        })
      }
      return { snapshot }
    },

    //  Toast lỗi do `@/core/api` bắn ra kèm ĐÚNG câu của máy chủ ("tạo thành
    //  vòng lặp", "đã có phụ thuộc"…) — thêm một toast chung chung ở đây là hai
    //  thông báo chồng nhau, cái mơ hồ che mất cái nói rõ nguyên nhân.
    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(boardKey, context.snapshot)
    },

    onSettled: () => queryClient.invalidateQueries({ queryKey: boardKey }),
  })
}

export function useUpdateTaskLink(listId: number) {
  const queryClient = useQueryClient()
  const boardKey = queryKeys.work.board(listId)

  return useMutation({
    mutationFn: ({ linkId, values }: { linkId: number; values: { link_type?: number } }) =>
      workTaskApi.updateLink(linkId, values),

    //  Đổi kiểu là đổi chỗ mũi tên CẮM VÀO thanh (mép trái ↔ mép phải), tức
    //  đường vẽ lại hẳn — chờ máy chủ trả lời rồi mới đổi thì người dùng chọn
    //  xong nhìn thấy mũi tên đứng yên một nhịp, tưởng bấm hụt.
    onMutate: async ({ linkId, values }) => {
      await queryClient.cancelQueries({ queryKey: boardKey })
      const snapshot = queryClient.getQueryData<WorkBoard>(boardKey)
      if (snapshot) {
        queryClient.setQueryData<WorkBoard>(boardKey, {
          ...snapshot,
          links: snapshot.links.map((l) => (l.id === linkId ? { ...l, ...values } : l)),
        })
      }
      return { snapshot }
    },

    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(boardKey, context.snapshot)
    },

    onSettled: () => queryClient.invalidateQueries({ queryKey: boardKey }),
  })
}

export function useDeleteTaskLink(listId: number) {
  const queryClient = useQueryClient()
  const boardKey = queryKeys.work.board(listId)

  return useMutation({
    mutationFn: (linkId: number) => workTaskApi.removeLink(linkId),

    onMutate: async (linkId) => {
      await queryClient.cancelQueries({ queryKey: boardKey })
      const snapshot = queryClient.getQueryData<WorkBoard>(boardKey)
      if (snapshot) {
        queryClient.setQueryData<WorkBoard>(boardKey, {
          ...snapshot,
          links: snapshot.links.filter((l) => l.id !== linkId),
        })
      }
      return { snapshot }
    },

    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(boardKey, context.snapshot)
      toast.error('Không xóa được phụ thuộc, đã trả về như cũ')
    },

    onSettled: () => queryClient.invalidateQueries({ queryKey: boardKey }),
  })
}
