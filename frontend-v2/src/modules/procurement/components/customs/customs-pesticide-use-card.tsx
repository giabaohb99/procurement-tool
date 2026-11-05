import type { CustomsPesticideUse } from '../../types/customs-pesticide'

/**
 * Một PHẠM VI SỬ DỤNG của thuốc BVTV ở khổ điện thoại — thay bảng 5 cột (~840px) ở trang chi
 * tiết thuốc.
 *
 * ⚠️ **Cây trồng lên đầu, dịch hại ngay dưới, mỗi trường có nhãn** (hai ô cạnh nhau mà nối
 * bằng dấu chấm thì không biết vế nào là cây, vế nào là sâu bệnh): người tra hỏi "thuốc này
 * trị được gì trên cây gì", liều lượng và thời gian cách ly là câu hỏi thứ hai. Thời gian cách ly giữ nguyên chữ của nguồn
 * ("7 ngày", "Không xác định"…) — đây là con số an toàn thực phẩm, không tự diễn giải.
 *
 * Bảng không khai `onRowClick` nên thẻ là `<div>` thường; mọi ô xuống dòng tự do, không cắt.
 */
export function CustomsPesticideUseCard({ row }: { row: CustomsPesticideUse }) {
  const details = [
    row.pest && `Dịch hại: ${row.pest}`,
    row.dosage && `Liều lượng: ${row.dosage}`,
    row.pre_harvest_interval && `Cách ly: ${row.pre_harvest_interval}`,
  ].filter(Boolean) as string[]

  return (
    <div className="space-y-1">
      <p className="font-medium break-words text-foreground">{row.crop || '—'}</p>
      {details.map((text) => (
        <p key={text} className="text-xs break-words text-muted-foreground">
          {text}
        </p>
      ))}
      {row.usage && <p className="text-xs break-words">{row.usage}</p>}
    </div>
  )
}
