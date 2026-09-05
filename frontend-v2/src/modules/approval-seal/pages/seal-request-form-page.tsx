import { ArrowLeft } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { SealPageHeader } from '../components/seal-page-header'
import { SealRequestForm } from '../components/seal-request-form'
import { useSealRequest } from '../hooks/use-seal-requests'
import type { SealRequest } from '../types/seal-request'

/**
 * Trang Thêm mới (`/approval-seal/new`) và Chỉnh sửa (`/approval-seal/:id/edit`)
 * yêu cầu đóng dấu.
 */
export function SealRequestFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const backToList = () => navigate(appRoutes.approvalSeal.root)
  const backToDetail = () => navigate(appRoutes.approvalSeal.detail(Number(id)))

  const { data, isLoading, isError } = useSealRequest(isEdit ? Number(id) : null)

  const title = isEdit ? 'Chỉnh sửa yêu cầu đóng dấu' : 'Tạo yêu cầu đóng dấu'

  //  Sau khi lưu: đã gửi duyệt → về chi tiết; còn nháp → sang trang SỬA của phiếu
  //  vừa lưu để người dùng đính kèm chứng từ đã ký rồi gửi duyệt.
  const handleSaved = (result: SealRequest, submitted: boolean) => {
    navigate(submitted ? appRoutes.approvalSeal.detail(result.id) : appRoutes.approvalSeal.edit(result.id))
  }

  return (
    <PageContainer className="w-full">
      {!isEdit ? (
        <SealRequestForm title={title} onCancel={backToList} onSaved={handleSaved} />
      ) : isLoading ? (
        <>
          <SealPageHeader title={title} onBack={backToList} />
          <Skeleton className="h-96 w-full" />
        </>
      ) : isError || !data ? (
        <>
          <SealPageHeader title={title} onBack={backToList} />
          <ErrorState
            title="Không tìm thấy yêu cầu đóng dấu"
            description="Phiếu có thể đã bị xóa hoặc bạn không có quyền xem."
          >
            <Button variant="outline" onClick={backToList}>
              <ArrowLeft className="size-4" />
              Về danh sách
            </Button>
          </ErrorState>
        </>
      ) : (
        <SealRequestForm request={data} title={title} onCancel={backToDetail} onSaved={handleSaved} />
      )}
    </PageContainer>
  )
}
