import { ChevronRight } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { COMPANY_LEVEL_LABELS, companyInitial, type Company } from '../types/company'

/**
 * Ô LOGO của một pháp nhân — chữ đầu của mã khi chưa có ảnh.
 *
 * Tách ra vì nó dựng ở hai chỗ với hai cỡ: ô «Tên pháp nhân» của bảng (nhỏ) và
 * thẻ ở khổ điện thoại (to hơn, vì ở đó nó là thứ đầu tiên mắt bắt được). Để
 * hai bản chép thì đổi cách vẽ một chỗ là hai màn nói khác nhau.
 *
 * ⚠️ `bg-white` cho ảnh thật: logo công ty phần lớn là PNG nền trong suốt vẽ
 * bằng mực sẫm, đặt lên nền `accent` xám là chữ chìm vào nền.
 */
export function CompanyLogoMark({
  company,
  className,
}: {
  company: Pick<Company, 'code' | 'name' | 'logo'>
  className?: string
}) {
  return (
    <span
      className={cn(
        'grid size-7 shrink-0 place-items-center overflow-hidden rounded-md border bg-accent text-xs font-semibold text-primary',
        className,
      )}
    >
      {company.logo ? (
        <img src={company.logo} alt="" className="size-full bg-white object-contain" />
      ) : (
        companyInitial(company)
      )}
    </span>
  )
}

/**
 * Một pháp nhân ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Mỗi dòng chữ đúng MỘT hàng, dài thì cắt bằng «…»** (khách chốt
 * 10/09/2026). Cho tên xuống hai hàng thì thẻ cao thấp so le nhau — mắt phải
 * dò lại mép trên của từng thẻ thay vì lướt một cột đều, và mười ba thẻ dài ra
 * thêm gần một màn hình. Cái giá là hai pháp nhân cùng họ tên cắt ra giống hệt
 * nhau («CÔNG TY TNHH SẢN XUẤT…»); bù lại bằng **dòng mã ngay dưới** — mã
 * (`NN DEGO` · `ABA`) mới là thứ phân biệt được, và nó luôn ngắn.
 *
 * ⚠️ **Thẻ chỉ nói cái BẤT THƯỜNG.** Huy hiệu trạng thái tắt khi pháp nhân vẫn
 * *Đang dùng* — 13/13 dòng hiện tại đều vậy, in ra là mười ba huy hiệu giống hệt
 * nhau. Thứ cần nhặt ra là dòng «Ngừng». Cùng luật với thẻ Phòng họp và Chức vụ.
 *
 * ⚠️ **MST đứng riêng một dòng, có nhãn.** Nó là chuỗi số trần: nhét chung dòng
 * với mã và cấp thì ba cụm ký tự cạnh nhau không cụm nào tự giải nghĩa được.
 * Không có MST thì bỏ hẳn dòng, đừng in «—» — dấu gạch đó nói *không có thông
 * tin*, mà ở đây đúng là chưa ai nhập, hai điều khác nhau nhưng cùng vô ích.
 */
export function CompanyCard({ company }: { company: Company }) {
  return (
    <div className="flex items-start gap-3">
      <CompanyLogoMark company={company} className="size-9 text-sm" />

      <div className="min-w-0 flex-1 space-y-1">
        <span className="block truncate font-medium text-foreground">{company.name}</span>

        <span className="block truncate text-xs text-muted-foreground">
          {company.code}
          {' · '}
          {COMPANY_LEVEL_LABELS[company.level] ?? 'Chưa phân cấp'}
        </span>

        {company.tax_code && (
          <span className="block truncate text-xs text-muted-foreground">
            MST: {company.tax_code}
          </span>
        )}

        {!company.is_active && (
          <Badge variant="outline" className="mt-0.5">
            Ngừng
          </Badge>
        )}
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi
           rê qua, nên phải nói bằng hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
