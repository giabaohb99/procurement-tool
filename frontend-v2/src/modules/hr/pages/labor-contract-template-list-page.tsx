import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { LaborContractTemplateCatalog } from '../components/labor-contract-template-catalog'
import { LaborContractTemplateHeaderActions } from '../components/labor-contract-template-header-actions'

/**
 * Trang «Mẫu hợp đồng» NGAY TRONG phân hệ Nhân sự (`/hr/labor-contract-templates`, duoc-CR-643).
 *
 * duoc-CR-629b từng cho mục menu này nhảy sang «Thiết lập văn bản» của phân hệ Văn bản — người dùng
 * bấm xong bị đẩy khỏi Nhân sự (đại ca: «bấm vô thì nó load ra chứ mẫu mà ko phải điều hướng»). Nay
 * trang dựng lại đúng bảng dùng chung `LaborContractTemplateCatalog` (cùng dữ liệu, cùng quyền
 * `labor_contract_template`); tab «Mẫu hợp đồng lao động» bên Văn bản vẫn giữ cho văn thư.
 */
export function LaborContractTemplateListPage() {
  return (
    //  `fill` để bảng chiếm phần cao còn lại (như trang Thiết lập văn bản); khổ hẹp thì cả trang cuộn.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Mẫu hợp đồng"
        description="Mẫu Word (.docx) lập hợp đồng lao động của từng pháp nhân."
        actions={<LaborContractTemplateHeaderActions />}
      />
      <LaborContractTemplateCatalog />
    </PageContainer>
  )
}
