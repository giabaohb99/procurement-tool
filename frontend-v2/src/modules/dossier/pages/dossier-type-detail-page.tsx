import { CrudDetailPage } from '@/shared/crud'
import { DOSSIER_TYPE_CRUD_CONFIG } from '../config/dossier-type-crud'

/**
 * Chi tiết MỘT loại hồ sơ — cùng khung khai báo với danh sách.
 *
 * Route tĩnh `/dossier/types/new` cũng trỏ vào chính component này: khung tự
 * nhận ra chế độ tạo mới (không gọi API chi tiết, không dựng thẻ danh tính lẫn
 * dòng thời gian). ⚠️ Route `/new` phải đăng ký TRƯỚC `/:id` — cùng khuôn với
 * `/hr/job-positions/new`.
 */
export function DossierTypeDetailPage() {
  return <CrudDetailPage config={DOSSIER_TYPE_CRUD_CONFIG} />
}
