import { useMemo } from 'react'

import { CrudDetailPage } from '@/shared/crud'
import { Skeleton } from '@/shared/ui/skeleton'
import { buildDossierCrudConfig } from '../config/dossier-crud'
import { useDossierTypesForForm } from '../hooks/use-dossier-types'

/**
 * Chi tiết MỘT hồ sơ — và cũng là màn THÊM MỚI (`/dossier/list/new`).
 *
 * Route tĩnh `/new` trỏ vào chính component này; khung tự nhận ra chế độ tạo
 * mới. ⚠️ Nó phải đăng ký TRƯỚC `/:id` kẻo «new» bị khớp thành id.
 *
 * ⚠️ **Phải chờ danh mục Loại hồ sơ tải xong mới dựng khung.** Bộ ô của biểu mẫu
 * lấy từ `field_schema` của loại; dựng khi danh mục còn rỗng thì `useForm` khởi
 * tạo với bộ ô THIẾU phần riêng của loại, và giá trị đã lưu của những ô đó
 * không có chỗ nào để đổ vào — người dùng mở một hồ sơ cũ ra và thấy các ô riêng
 * trống trơn. Chúng chỉ hiện lại sau lần `reset` kế tiếp, tức là có thể không
 * bao giờ.
 */
export function DossierDetailPage() {
  const { data, isLoading } = useDossierTypesForForm()
  const types = useMemo(() => data?.items ?? [], [data])
  const config = useMemo(() => buildDossierCrudConfig(types), [types])

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-5xl space-y-4 p-4 sm:p-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    )
  }

  return <CrudDetailPage config={config} />
}
