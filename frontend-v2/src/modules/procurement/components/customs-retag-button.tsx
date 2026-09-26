import { useMutation } from '@tanstack/react-query'
import { Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'

import { retagCustomsKinds } from '../api/customs-kind-api'

/**
 * Nút «Gắn lại nhãn» trên danh mục từ khóa — bao-CR-494.
 *
 * Dòng hàng đã nạp KHÔNG tự đổi nhãn khi admin sửa từ khóa (nhãn tính lúc nạp, lưu xuống cột
 * để lọc được). Phải có một nút chạy lại cho toàn bộ, không thì admin thêm từ khóa xong mà
 * bảng vẫn hiện nhãn cũ, tưởng từ khóa không ăn. Vài chục nghìn dòng chạy trong vài giây.
 */
export function CustomsRetagButton() {
  const retag = useMutation({
    mutationFn: retagCustomsKinds,
    onSuccess: (result) => {
      toast.success(
        `Đã gắn lại ${result.total.toLocaleString('vi-VN')} dòng — ${result.technical.toLocaleString('vi-VN')} nguyên liệu, ${(result.total - result.technical).toLocaleString('vi-VN')} thành phẩm`,
      )
    },
  })

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      disabled={retag.isPending}
      onClick={() => retag.mutate()}
      title="Áp bộ từ khóa hiện tại lên MỌI dòng hàng đã nạp — chạy sau khi thêm/sửa từ khóa"
    >
      {retag.isPending ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
      Gắn lại nhãn
    </Button>
  )
}
