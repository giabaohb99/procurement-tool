/**
 * So BẢN NHÁP bộ giá trị với bản gốc rồi bắn đúng những lệnh cần thiết.
 *
 * Dùng chung cho hai loại trường có bộ giá trị — Tag và nhãn tùy biến — vì luật
 * so sánh y hệt nhau, chỉ khác đường API. Chép ra hai bản là sớm muộn một bên
 * quên gửi `sort_order` rồi kéo xếp xong lại nhảy về chỗ cũ.
 */

/** Một dòng trong bản nháp; `id < 0` = dòng vừa thêm, chưa có ở máy chủ. */
export interface DraftOption {
  id: number
  name: string
  color: string
}

/** Giá trị đang có ở máy chủ — `WorkTag` và `WorkLabelOption` đều khớp hình này. */
export interface SavedOption {
  id: number
  name: string
  color: string
}

export interface OptionSaveApi {
  create(values: { name: string; color: string; sort_order: number }): Promise<unknown>
  update(id: number, values: { name: string; color: string; sort_order: number }): Promise<unknown>
  remove(id: number): Promise<unknown>
}

/**
 * Lưu theo LÔ: thêm dòng mới, sửa dòng đã đổi, xóa dòng đã bỏ khỏi bản nháp.
 *
 * Vị trí trong mảng chính là `sort_order`, nên chỉ đổi thứ tự (không sửa chữ)
 * vẫn phải gửi lệnh sửa.
 */
export async function saveFieldOptions(
  original: SavedOption[],
  draft: DraftOption[],
  api: OptionSaveApi,
): Promise<void> {
  const cu = new Map(original.map((o) => [o.id, o]))

  for (const [thuTu, o] of draft.entries()) {
    const ten = o.name.trim()
    //  Dòng trống thì BỎ QUA chứ không gửi: máy chủ từ chối tên rỗng, mà lỗi ấy
    //  làm hỏng cả lượt lưu — người dùng thêm nhầm một dòng là mất luôn các sửa
    //  đổi khác.
    if (!ten) continue

    if (o.id < 0) {
      await api.create({ name: ten, color: o.color, sort_order: thuTu })
      continue
    }

    const goc = cu.get(o.id)
    if (!goc) continue
    const doiThuTu = original.findIndex((x) => x.id === o.id) !== thuTu
    if (goc.name !== ten || goc.color !== o.color || doiThuTu)
      await api.update(o.id, { name: ten, color: o.color, sort_order: thuTu })
  }

  const conLai = new Set(draft.map((o) => o.id))
  for (const o of original) {
    if (!conLai.has(o.id)) await api.remove(o.id)
  }
}
