import { Lock } from 'lucide-react'

import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { SectionHeading } from '@/shared/ui/section-heading'
import { SUPPLIER_TYPE } from '../types/driver'
import { CatalogFormField } from './catalog-form-field'
import { CatalogModeButton } from './catalog-mode-button'

/** Bốn ô mô tả bên cho thuê — chỉ dựng khi nguồn là *Thuê ngoài*. */
export interface CatalogSupplierValues {
  external_company: string
  tax_code: string
  tax_address: string
  id_number: string
}

interface CatalogSourceSectionProps {
  /** Danh từ của bản ghi: "xe" hay "tài xế" — dùng trong câu giải thích. */
  unitLabel: string
  /** Đang SỬA bản ghi đã tạo — nguồn và loại nhà cung cấp lúc đó đã chốt. */
  isEdit: boolean
  isExternal: boolean
  onExternalChange: (isExternal: boolean) => void
  supplierType: number
  onSupplierTypeChange: (supplierType: number) => void
  values: CatalogSupplierValues
  onChange: (key: keyof CatalogSupplierValues, value: string) => void
  /** Câu chú thích cho ô CCCD — mỗi danh mục gọi tên người đó một kiểu. */
  idNumberHint: string
}

/**
 * Khối NGUỒN của biểu mẫu danh mục Đặt xe: nội bộ hay thuê ngoài, và nếu thuê
 * ngoài thì thuê của doanh nghiệp hay cá nhân + giấy tờ kèm theo.
 *
 * Dùng chung cho cả Xe lẫn Tài xế — hai biểu mẫu vốn chép nguyên khối này của
 * nhau, và bản chép đã bắt đầu trôi khác nhau từng chữ.
 *
 * ⚠️ Khi SỬA, hai lựa chọn đó **hiện bằng chữ chứ không phải nút mờ**. Bản cũ
 * dựng nguyên bốn nút `disabled` rồi viết hai dòng "Không đổi được…" bên dưới:
 * nút mờ vẫn trông như bấm được nên người dùng bấm trước, đọc sau, và hai câu
 * giải thích gần giống hệt nhau xếp chồng lên nhau thì thành nhiễu. Chữ trong
 * `ReadOnlyValue` nói ngay rằng đây là giá trị đã chốt — và vẫn bôi đen / chép
 * ra được, thứ mà nút `disabled` không cho.
 *
 * Ô giấy tờ của bên cho thuê thì VẪN sửa được khi đang sửa: chỉ *nguồn* và
 * *loại nhà cung cấp* là chốt, còn mã số thuế gõ nhầm thì phải cho sửa.
 */
export function CatalogSourceSection({
  unitLabel,
  isEdit,
  isExternal,
  onExternalChange,
  supplierType,
  onSupplierTypeChange,
  values,
  onChange,
  idNumberHint,
}: CatalogSourceSectionProps) {
  const isIndividual = supplierType === SUPPLIER_TYPE.individual

  return (
    <section className="flex flex-col gap-4">
      <SectionHeading>Nguồn {unitLabel}</SectionHeading>

      {isEdit ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <CatalogFormField
            label="Nguồn"
            hint={
              <span className="inline-flex items-center gap-1">
                <Lock className="size-3" />
                Không đổi được sau khi tạo.
              </span>
            }
          >
            <ReadOnlyValue>{isExternal ? 'Thuê ngoài' : 'Nội bộ'}</ReadOnlyValue>
          </CatalogFormField>

          {isExternal && (
            <CatalogFormField label="Loại nhà cung cấp">
              <ReadOnlyValue>{isIndividual ? 'Cá nhân' : 'Doanh nghiệp'}</ReadOnlyValue>
            </CatalogFormField>
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-2 sm:max-w-md">
            <CatalogModeButton
              active={!isExternal}
              tone="blue"
              onClick={() => onExternalChange(false)}
            >
              Nội bộ
            </CatalogModeButton>
            <CatalogModeButton
              active={isExternal}
              tone="amber"
              onClick={() => onExternalChange(true)}
            >
              Thuê ngoài
            </CatalogModeButton>
          </div>

          {isExternal && (
            <div className="flex flex-col gap-1.5">
              <Label>Loại nhà cung cấp</Label>
              <div className="grid grid-cols-2 gap-2 sm:max-w-md">
                <CatalogModeButton
                  active={!isIndividual}
                  tone="blue"
                  onClick={() => onSupplierTypeChange(SUPPLIER_TYPE.enterprise)}
                >
                  Doanh nghiệp
                </CatalogModeButton>
                <CatalogModeButton
                  active={isIndividual}
                  tone="amber"
                  onClick={() => onSupplierTypeChange(SUPPLIER_TYPE.individual)}
                >
                  Cá nhân
                </CatalogModeButton>
              </div>
              {/*  Nói TRƯỚC khi họ bấm, không nói sau: sang trang sửa mới biết
                  mình chọn nhầm thì đã phải tạo lại cả bản ghi. */}
              <p className="text-xs text-muted-foreground">
                Chọn xong là chốt — nguồn và loại nhà cung cấp không sửa lại được sau khi tạo.
              </p>
            </div>
          )}
        </div>
      )}

      {isExternal &&
        (isIndividual ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <CatalogFormField label="CCCD" hint={idNumberHint}>
              <Input
                value={values.id_number}
                onChange={(e) => onChange('id_number', e.target.value)}
                placeholder="Số căn cước công dân"
              />
            </CatalogFormField>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <CatalogFormField label="Tên doanh nghiệp" required>
              <Input
                value={values.external_company}
                onChange={(e) => onChange('external_company', e.target.value)}
                placeholder="VD: Công ty Vận tải ABC"
              />
            </CatalogFormField>
            <CatalogFormField label="Mã số thuế" required>
              <Input
                value={values.tax_code}
                onChange={(e) => onChange('tax_code', e.target.value)}
                placeholder="VD: 0312345678"
              />
            </CatalogFormField>
            <CatalogFormField
              label="Địa chỉ thuế"
              required
              fullWidth
              hint="Địa chỉ trên đăng ký kinh doanh — dùng để đối chiếu khi bên cho thuê xuất hóa đơn."
            >
              <Input
                value={values.tax_address}
                onChange={(e) => onChange('tax_address', e.target.value)}
                placeholder="Địa chỉ đăng ký thuế"
              />
            </CatalogFormField>
          </div>
        ))}
    </section>
  )
}
