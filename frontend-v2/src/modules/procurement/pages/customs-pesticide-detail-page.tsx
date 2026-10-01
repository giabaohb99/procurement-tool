// CHI TIẾT MỘT THUỐC BVTV — `/procurement/customs-prices/pesticides/:id` (duoc-CR-492, 29/09/2026).
//
// Trang riêng thay cho hộp thoại cũ (đại ca chốt): hộp thoại phải nhét nút Sửa/Xóa chen giữa tiêu đề
// và thông tin, và bảng phạm vi sử dụng dưới đáy không có tiêu đề đủ rõ để biết nó là gì. Trang đi
// 01/10/2026 — làm lại cả bố cục (đại ca chê xấu sau ba lần vá từng khối): THẺ ĐẦU TRANG gom thông
// tin chính, phần dưới chia TAB (phạm vi · thuốc liên quan · tệp · lịch sử), cột «Tìm thuốc khác» +
// «Tra cứu nhanh» bên phải khi màn đủ rộng, màn hẹp thì thành nút «Tra cứu» mở ngăn kéo.
//
// Gác quyền: đường này nằm DƯỚI mục menu «Thuốc BVTV» (`customs_price.read`) nên `canAccessRoute` tự
// gác; nút Sửa / Xóa theo khóa riêng `customs_pesticide` (duoc-CR-490).
import { ArrowLeft, Pencil, Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { useBackTarget } from '@/shared/hooks/use-back-target'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'

import { CustomsPesticideBannedNotice } from '../components/customs/customs-pesticide-banned-notice'
import { CustomsPesticideDetailTabs } from '../components/customs/customs-pesticide-detail-tabs'
import { CustomsPesticideFormDialog } from '../components/customs/customs-pesticide-form-dialog'
import { CustomsPesticideHeroCard } from '../components/customs/customs-pesticide-hero-card'
import { CustomsPesticideLookupSidebar } from '../components/customs/customs-pesticide-lookup-sidebar'
import { buildCustomsSectionPath } from '../config/customs-sections'
import {
  useCustomsPesticide,
  useDeleteCustomsPesticide,
  usePesticidePermissions,
} from '../hooks/use-customs-pesticides'
import { toPesticideInput } from '../utils/customs-pesticide-form'

export function CustomsPesticideDetailPage() {
  const { id } = useParams<{ id: string }>()
  const pesticideId = Number(id) || 0
  const navigate = useNavigate()
  const back = useBackTarget(buildCustomsSectionPath('pesticides'))
  const { canCreate, canEdit, canDelete } = usePesticidePermissions()
  const [editing, setEditing] = useState(false)
  const [lookupOpen, setLookupOpen] = useState(false)
  const { data, isLoading } = useCustomsPesticide(pesticideId || null)
  const remove = useDeleteCustomsPesticide()

  const backButton = (
    <Button
      variant="outline"
      size="icon"
      title="Quay lại danh mục thuốc BVTV"
      aria-label="Quay lại danh mục thuốc BVTV"
      onClick={() => navigate(back.url)}
    >
      <ArrowLeft className="size-4" />
    </Button>
  )

  if (isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải thuốc BVTV…</p>
      </PageContainer>
    )
  }
  if (!data) {
    return (
      <PageContainer>
        <PageHeader leading={backButton} title="Không tìm thấy thuốc BVTV" />
        <p className="text-sm text-muted-foreground">
          Thuốc này không còn trong danh mục — có thể đã bị xóa, hoặc đã thay bằng lần nạp danh mục
          mới.
        </p>
      </PageContainer>
    )
  }

  const actions = (
    <>
      {/*  Màn hẹp không có cột tra cứu — mở nó trong ngăn kéo. */}
      <Button
        type="button"
        variant="outline"
        className="xl:hidden"
        onClick={() => setLookupOpen(true)}
      >
        <Search className="size-4" />
        Tra cứu
      </Button>
      {canEdit && (
        <Button type="button" variant="outline" onClick={() => setEditing(true)}>
          <Pencil className="size-4" />
          Sửa
        </Button>
      )}
      {canDelete && (
        <DeleteConfirmButton
          recordName={data.trade_name}
          pending={remove.isPending}
          warning={
            data.is_manual
              ? undefined
              : 'Thuốc này lấy từ bản cào — lần «Nạp danh mục» sau sẽ thêm lại nó theo nguồn.'
          }
          onConfirm={async () => {
            await remove.mutateAsync(data.id)
            navigate(back.url, { replace: true })
          }}
        />
      )}
    </>
  )

  return (
    <PageContainer>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_16rem] xl:items-start">
        <div className="min-w-0 space-y-4">
          <CustomsPesticideBannedNotice items={data.banned} />
          <CustomsPesticideHeroCard pesticide={data} leading={backButton} actions={actions} />
          <CustomsPesticideDetailTabs pesticide={data} canManageFiles={canEdit || canCreate} />
        </div>
        {/*  `sticky`: cuộn bảng dài vẫn còn ô tìm trong tầm tay. Màn hẹp ẩn hẳn (đã có ngăn kéo). */}
        <CustomsPesticideLookupSidebar
          currentPestGroup={data.pest_group}
          className="hidden xl:sticky xl:top-4 xl:flex"
        />
      </div>

      <Sheet open={lookupOpen} onOpenChange={setLookupOpen}>
        <SheetContent side="right" className="gap-0 overflow-y-auto p-0">
          <SheetHeader className="border-b">
            <SheetTitle>Tra cứu thuốc BVTV</SheetTitle>
          </SheetHeader>
          <CustomsPesticideLookupSidebar
            currentPestGroup={data.pest_group}
            className="rounded-none border-0 shadow-none"
          />
        </SheetContent>
      </Sheet>

      {editing && (
        <CustomsPesticideFormDialog
          pesticideId={data.id}
          initial={toPesticideInput(data)}
          fromSource={!data.is_manual}
          onClose={() => setEditing(false)}
          onSaved={() => setEditing(false)}
        />
      )}
    </PageContainer>
  )
}
