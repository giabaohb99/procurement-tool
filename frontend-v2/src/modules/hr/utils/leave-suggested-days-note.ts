/**
 * Câu giải thích «số ngày gợi ý tính theo gì» dưới bảng loại nghỉ.
 *
 * Phải rẽ nhánh theo `exclude_holiday` của LOẠI NGHỈ đang chọn: loại tính ngày lịch
 * (thai sản, nghỉ ốm dài ngày…) đếm cả ngày nghỉ tuần lẫn ngày lễ, nên nói «đã trừ…»
 * là nói ngược với con số hiện bên cạnh (bản trước làm vậy cho mọi loại nghỉ).
 * `excludeHoliday` chưa biết (chưa chọn loại) thì coi như loại thường — cùng mặc định
 * với backend.
 */
export function describeSuggestedDays(
  suggestedDays: number,
  excludeHoliday: boolean | undefined,
  scheduleName?: string,
): string {
  if (excludeHoliday === false) {
    return `Khoảng ngày đã chọn có ${suggestedDays} ngày — loại nghỉ này đếm theo ngày lịch, tính cả ngày nghỉ tuần và ngày lễ.`
  }
  const schedule = scheduleName ? ` «${scheduleName}»` : ''
  return `Khoảng ngày đã chọn có ${suggestedDays} ngày công (đã trừ ngày nghỉ theo lịch làm việc${schedule} và ngày lễ).`
}
