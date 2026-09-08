import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import type { WorkList } from '../types/work'
import { useUpdateWorkList } from './use-work-lists'

/** Trần khớp cột `tab_work_list.name` — `String(200)` ở `model.py`. */
export const LIST_NAME_MAX = 200
/** Mô tả là `Text` nên DB không chặn; 1500 là trần do nghiệp vụ đặt. */
export const LIST_DESCRIPTION_MAX = 1500

/**
 * Trạng thái của biểu mẫu THÔNG TIN dự án (tên · mô tả · màu).
 *
 * Tách khỏi component vì hộp Quản lý dự án cần dùng nó ở HAI CHỖ CÁCH XA NHAU:
 * các ô nhập nằm ở khối trên cùng, còn nút *Lưu thông tin* nằm dưới đáy hộp,
 * sau cả danh sách thành viên. Hai chỗ phải nhìn chung một trạng thái, nếu không
 * nút Lưu không biết có gì để lưu.
 */
export function useListInfoForm(list: WorkList) {
  const [name, setName] = useState(list.name)
  const [description, setDescription] = useState(list.description ?? '')
  const [color, setColor] = useState(list.color ?? '')
  const updateList = useUpdateWorkList()

  //  Nạp lại khi mở sang DỰ ÁN KHÁC. Chỉnh state ngay trong lượt dựng (khuôn
  //  `useHasChanged`) chứ không dùng `useEffect`: setState trong effect đẻ ra một
  //  lượt dựng thừa và bị `react-hooks/set-state-in-effect` cảnh báo. Bám vào
  //  `list.id` chứ không bám từng ô — bám ô thì mỗi lần lưu xong prop đổi là nó
  //  xoá luôn cái người dùng đang gõ dở.
  if (useHasChanged(list.id)) {
    setName(list.name)
    setDescription(list.description ?? '')
    setColor(list.color ?? '')
  }

  const trimmedName = name.trim()
  const isDirty =
    trimmedName !== list.name ||
    description.trim() !== (list.description ?? '') ||
    color !== (list.color ?? '')
  const canSave = Boolean(trimmedName) && isDirty && !updateList.isPending

  function save() {
    if (!canSave) return
    updateList.mutate({
      id: list.id,
      values: { name: trimmedName, description: description.trim(), color },
    })
  }

  return {
    name,
    setName,
    description,
    setDescription,
    color,
    setColor,
    trimmedName,
    canSave,
    isPending: updateList.isPending,
    save,
  }
}

export type ListInfoForm = ReturnType<typeof useListInfoForm>
