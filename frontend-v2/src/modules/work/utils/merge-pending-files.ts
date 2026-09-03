/**
 * Gom tệp đang chờ gửi kèm một bình luận.
 *
 * Tách khỏi component vì tệp vào ô soạn bằng BA đường khác nhau — chọn tay, dán
 * ảnh, kéo thả — mà cả ba phải chịu chung một luật. Nhét luật vào từng chỗ gọi
 * là chỗ nào đó sẽ quên, và quên trần thì backend từ chối lúc gửi: người dùng
 * gõ xong cả đoạn mới biết mình thừa tệp.
 */

/**
 * @param dangCho  Tệp đã chọn từ trước.
 * @param them     Tệp vừa vào, theo thứ tự người dùng đưa vào.
 * @param max      Trần tệp mỗi bình luận (backend cũng chặn đúng số này).
 */
export function mergePendingFiles(dangCho: File[], them: File[], max: number): File[] {
  //  Trần ≤ 0 nghĩa là không cho kèm tệp — trả rỗng chứ đừng để `slice` hiểu số
  //  âm thành "đếm từ cuối" và lọt ra vài tệp.
  if (max <= 0) return []

  const out = [...dangCho]
  for (const file of them) {
    if (out.length >= max) break
    //  Bỏ TRÙNG: dán hai lần cùng một ảnh, hoặc thả lại đúng tệp vừa thả, là
    //  chuyện thường. Gửi lên hai bản giống hệt thì backend nhận cả hai và
    //  người đọc thấy hai dòng y nhau mà không hiểu vì sao.
    //  So bằng BỘ BA tên · cỡ · lần sửa cuối: `File` không có id, mà hai tệp
    //  khác nhau trùng cả ba thứ đó thì gần như chắc chắn là một.
    if (out.some((f) => sameFile(f, file))) continue
    out.push(file)
  }
  return out
}

function sameFile(a: File, b: File): boolean {
  return a.name === b.name && a.size === b.size && a.lastModified === b.lastModified
}
