import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { nameInitials } from '@/shared/utils/name-initials'
import type { Driver } from '../types/driver'
import { CatalogIdentityCell } from './catalog-identity-cell'

/**
 * Ô NHẬN DIỆN một tài xế trong bảng danh mục: tên ở dòng trên, giấy phép lái xe
 * ở dòng dưới, kèm ảnh đại diện chữ cái.
 *
 * ⚠️ Gộp hai cột *Số GPLX* + *Hạng* vào dòng phụ là CÓ CHỦ Ý (22/09/2026). Bản
 * cũ để chúng thành hai cột riêng, mà 13/15 tài xế bỏ trống số GPLX — tức một
 * cột rộng 150px gần như trắng trơn, còn cột *Hạng* thì chỉ chứa hai ký tự.
 * Gộp lại, mỗi hàng còn đúng một điểm nhấn là TÊN, thứ người ta tìm khi mở màn.
 */
export function DriverIdentityCell({ driver }: { driver: Driver }) {
  //  Hạng đứng trước số: hạng là thứ người điều phối cần đối chiếu với loại xe
  //  (B2 không lái được xe tải hạng C), còn số GPLX chỉ dùng khi làm giấy tờ.
  const license = [driver.license_class, driver.license_number].filter(Boolean).join(' · ')

  return (
    <CatalogIdentityCell
      media={
        <Avatar className="size-8 shrink-0 border border-border/70 bg-primary/10 shadow-2xs">
          <AvatarFallback className="bg-transparent text-xs font-bold text-primary">
            {nameInitials(driver.name || '')}
          </AvatarFallback>
        </Avatar>
      }
      title={driver.name}
      subtitle={license ? `GPLX ${license}` : 'Chưa khai GPLX'}
    />
  )
}
