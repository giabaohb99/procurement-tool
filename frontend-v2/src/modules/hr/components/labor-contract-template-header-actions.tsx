import { BookOpen, Plus } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { LaborContractTemplateUploadDialog } from './labor-contract-template-upload-dialog'

/**
 * Nút ở GÓC PHẢI TIÊU ĐỀ trang "Thiết lập văn bản" khi đang ở mục Mẫu hợp đồng lao động: "Danh sách
 * biến" + "Tải lên mẫu". Đứng đúng chỗ nút "Thêm mới" của mục Văn bản mẫu — trước đây hai nút nằm lửng
 * giữa thanh lọc của bảng, lệch hẳn với tab bên cạnh. Hộp tải lên mẫu MỚI đi theo nút (danh sách tự nạp
 * lại nhờ invalidate của mutation); hộp THAY tệp vẫn ở bảng vì gắn với từng dòng.
 */
export function LaborContractTemplateHeaderActions() {
  const { can } = usePermission()
  const navigate = useNavigate()
  const [uploadOpen, setUploadOpen] = useState(false)

  if (!can('labor_contract_template', 'read')) return null
  const canCreate = can('labor_contract_template', 'create')

  return (
    <>
      <div className="flex gap-2 max-md:w-full">
        <Button
          type="button"
          variant="outline"
          className="max-md:flex-1"
          onClick={() => navigate(appRoutes.hr.laborContractVariables)}
        >
          <BookOpen className="size-4" />
          Danh sách biến
        </Button>
        {canCreate && (
          <Button type="button" className="max-md:flex-1" onClick={() => setUploadOpen(true)}>
            <Plus className="size-4" />
            Tải lên mẫu
          </Button>
        )}
      </div>
      <LaborContractTemplateUploadDialog open={uploadOpen} onOpenChange={setUploadOpen} />
    </>
  )
}
