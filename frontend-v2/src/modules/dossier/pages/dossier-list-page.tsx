import { useMemo } from 'react'

import { CrudListPage } from '@/shared/crud'
import { Skeleton } from '@/shared/ui/skeleton'
import { buildDossierCrudConfig } from '../config/dossier-crud'
import { useDossierTypesForForm } from '../hooks/use-dossier-types'

/**
 * DANH SÁCH HỒ SƠ — `/dossier/list`, bảng `tab_dossier`, khóa quyền `dossier`.
 *
 * ⚠️ Khác mọi màn CRUD khác: khai báo là một HÀM DỰNG chứ không phải một hằng,
 * vì biểu mẫu hồ sơ phụ thuộc vào danh mục Loại hồ sơ (mỗi loại tự khai bộ ô
 * riêng). Nạp danh mục trước rồi mới dựng — xem `config/dossier-crud.tsx`.
 *
 * ⚠️ `useMemo` ở đây KHÔNG phải tối ưu vặt. `CrudDetailPage` để `config.formFields`
 * trong mảng phụ thuộc của một `useEffect` gọi `reset(...)`; dựng lại config mỗi
 * lượt vẽ là hàm đó mới mỗi lượt, effect chạy lại, và form bị **nạp lại giá trị
 * ngay giữa lúc người dùng đang gõ**.
 */
export function DossierListPage() {
  const { data, isLoading } = useDossierTypesForForm()
  const types = useMemo(() => data?.items ?? [], [data])
  const config = useMemo(() => buildDossierCrudConfig(types), [types])

  //  Dựng bảng trước khi có danh mục thì ô lọc «Loại hồ sơ» hiện ra RỖNG —
  //  người dùng mở nó, thấy không có mục nào, và kết luận công ty chưa khai loại
  //  hồ sơ nào. Khung xương nói đúng hơn: «đang tải».
  if (isLoading) {
    return (
      <div className="space-y-4 p-4 sm:p-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return <CrudListPage config={config} />
}
