import { ArrowLeft } from 'lucide-react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

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
  const [searchParams] = useSearchParams()
  const isEdit = Boolean(id)
  const fromId = Number(searchParams.get('from')) || null

  const backToList = () => navigate(appRoutes.approvalSeal.requests)
  const backToDetail = () => navigate(appRoutes.approvalSeal.detail(Number(id)))

  //  Sửa: nạp phiếu theo :id. Nhân bản: nạp phiếu nguồn theo ?from=.
  const loadId = isEdit ? Number(id) : fromId
  const { data, isLoading, isError } = useSealRequest(loadId)

  const needsLoad = isEdit || fromId !== null
  const title = isEdit
    ? 'Chỉnh sửa yêu cầu đóng dấu'
    : fromId
      ? 'Nhân bản yêu cầu đóng dấu'
      : 'Tạo yêu cầu đóng dấu'

  //  Sau khi lưu (dù nháp hay đã gửi duyệt) đều về trang CHI TIẾT: trang này nay
  //  sửa được ngay tại chỗ (đính kèm chứng từ + gửi duyệt), không cần trang /edit riêng.
  const handleSaved = (result: SealRequest) => {
    navigate(appRoutes.approvalSeal.detail(result.id))
  }

  return (
    <PageContainer className="w-full">
      {!needsLoad ? (
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
      ) : isEdit ? (
        <SealRequestForm request={data} title={title} onCancel={backToDetail} onSaved={handleSaved} />
      ) : (
        <SealRequestForm duplicateFrom={data} title={title} onCancel={backToList} onSaved={handleSaved} />
      )}
    </PageContainer>
  )
}
