import { useLocation, useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { confirm } from '@/shared/ui/confirm-dialog'

import { useArchiveWorkList, usePurgeWorkList } from './use-work-lists'

/**
 * Hai thao tác gỡ một dự án — **Đưa vào lưu trữ** và **Xóa vĩnh viễn** (duoc-CR-783, anh Được 19/11/2026: "có 2 chức
 * năng là xóa vĩnh viễn và đưa vào lưu trữ"). Dùng chung cho menu "…" ở cây bên trái và menu Quản lý dự án đầu trang, để
 * câu hỏi xác nhận và đường về sau khi gỡ chỉ có một bản.
 *
 * Gỡ xong mà đang đứng ở chính dự án đó thì về màn danh sách dự án — ở lại là một trang cụt.
 */
export function useProjectRemoveActions(project: { id: number; name: string }) {
  const archive = useArchiveWorkList()
  const purge = usePurgeWorkList()
  const navigate = useNavigate()
  const location = useLocation()

  const leaveIfHere = () => {
    const detail = appRoutes.project.detail(project.id)
    if (location.pathname === detail || location.pathname.startsWith(`${detail}/`)) {
      navigate(appRoutes.project.list)
    }
  }

  async function archiveProject() {
    const ok = await confirm({
      title: 'Đưa dự án vào lưu trữ',
      message: `Đưa "${project.name}" vào lưu trữ? Dự án ẩn khỏi danh sách, việc bên trong giữ nguyên và khôi phục được.`,
      confirmLabel: 'Đưa vào lưu trữ',
    })
    if (ok) archive.mutate(project.id, { onSuccess: leaveIfHere })
  }

  async function purgeProject() {
    const ok = await confirm({
      title: 'Xóa vĩnh viễn dự án',
      message: `Xóa vĩnh viễn "${project.name}" cùng mọi việc, bình luận và tệp đính kèm bên trong? Thao tác này KHÔNG khôi phục được.`,
      confirmLabel: 'Xóa vĩnh viễn',
      tone: 'danger',
    })
    if (ok) purge.mutate(project.id, { onSuccess: leaveIfHere })
  }

  return { archiveProject, purgeProject }
}
