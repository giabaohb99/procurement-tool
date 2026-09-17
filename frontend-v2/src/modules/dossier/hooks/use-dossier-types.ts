import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import type { DossierType } from '../types/dossier-type'

/**
 * Khóa cục bộ — ngoại lệ được phép của luật "query key nằm ở
 * `shared/constants/query-keys.ts`": danh mục loại hồ sơ khi SỬA thì đi qua
 * khung CRUD, và khung đó dùng khóa `['crud', '/api/dossier-types', …]` của
 * riêng nó. Hai khóa khác nhau là cố ý — xem cảnh báo về `staleTime` bên dưới.
 */
const dossierTypeKeys = {
  forForm: ['dossier', 'dossier-types', 'for-form'] as const,
}

/**
 * Khóa để nơi khác LÀM MỚI danh mục sau khi sửa bộ trường.
 *
 * ⚠️ Cần vì trình khai bộ trường lưu qua `useCrudSave`, mà hook đó chỉ dọn cache
 * của LỚP CRUD (`['crud', '/api/dossier-types']`) — khác hẳn khóa ở đây. Không
 * gọi tới thì quản trị sửa xong bộ trường, mở màn lập hồ sơ và vẫn thấy bộ ô
 * CŨ suốt `staleTime` (5 phút), không hiểu vì sao thứ mình vừa lưu chưa hiện.
 */
export const DOSSIER_TYPES_FOR_FORM_KEY = dossierTypeKeys.forForm

/**
 * Danh mục LOẠI HỒ SƠ kèm **bộ trường tùy biến** — nguồn dựng biểu mẫu hồ sơ.
 *
 * Nạp một lần cho cả màn: ô chọn «Loại hồ sơ» cần danh sách, và biểu mẫu cần
 * `field_schema` của loại đang chọn. Gọi hai lần cho hai việc đó là hai bản
 * dữ liệu có thể lệch nhau trong cùng một trang.
 *
 * ⚠️ **KHÔNG lọc `is_active` ở đây.** Loại đã ngừng dùng vẫn phải có trong danh
 * sách, nếu không thì hồ sơ đang mang nó mở ra sẽ thấy ô «Loại hồ sơ» TRỐNG
 * (Radix `Select` không khớp mục nào thì rơi về chữ gợi ý, nhìn y như ô chưa
 * nhập) và mất luôn bộ ô tùy biến của nó. Việc chặn gán MỚI làm ở nơi dựng ô
 * chọn, bằng cách bỏ loại ngừng dùng khỏi `options` — backend cũng chặn lần
 * nữa (`service.sync_type_label`).
 *
 * ⚠️ `page_size` phải đủ lớn: mặc định của backend là 20, nên công ty khai tới
 * loại thứ 21 thì nó **biến mất khỏi ô chọn trong im lặng**. 500 là trần thực
 * tế — danh mục này đếm bằng chục, không bằng nghìn.
 */
export function useDossierTypesForForm() {
  return useQuery({
    queryKey: dossierTypeKeys.forForm,
    queryFn: () =>
      apiGet<PaginatedResult<DossierType>>('/api/dossier-types', {
        params: { page_size: 500, sort_by: 'sort_order', sort_dir: 'asc' },
      }),
    //  Bộ trường đổi thì biểu mẫu hồ sơ đổi theo — nhưng đó là việc của quản
    //  trị, không phải việc xảy ra giữa chừng một lần nhập liệu. 5 phút đủ để
    //  người vừa sửa danh mục ở tab khác thấy kết quả sau một lần tải lại trang.
    staleTime: 5 * 60 * 1000,
  })
}
