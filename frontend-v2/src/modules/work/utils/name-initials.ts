/**
 * Chữ tắt hiện trên avatar tròn của một người.
 *
 * Luật: **chữ cái đầu của HAI TỪ CUỐI**. Tên Việt gọi theo tên, mà chỉ lấy tên
 * thì cả phòng trùng nhau — "Nguyễn Văn Nhân Sự Một" và "Phạm Thị Kế Toán Một"
 * đều ra một chữ.
 *
 * Bản cũ (còn nằm ở `project-list-page.tsx`) lấy HAI KÝ TỰ ĐẦU CỦA TỪ CUỐI, cho
 * ra `MỘ` cho cả hai người trên — vừa trùng nhau vừa đọc như một âm cụt. Lấy đầu
 * hai từ cuối thì ra `SM` và `TM`, phân biệt được.
 *
 * Dùng `Array.from` chứ không `slice`: tên có ký tự ngoài BMP (emoji người ta dán
 * vào ô tên) thì `slice(0, 1)` cắt đúng giữa một cặp surrogate và trả về ký tự
 * hỏng hiển thị thành ô vuông.
 */
export function nameInitials(fullName: string): string {
  const words = (fullName ?? '').trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'

  const firstCharOf = (word: string) => Array.from(word)[0] ?? ''

  //  Một từ duy nhất ("Admin", "Sơn") thì không có "hai từ cuối" — lấy hai ký tự
  //  đầu của chính nó, còn hơn trả về một chữ đứng lệch trong vòng tròn.
  const raw =
    words.length === 1
      ? Array.from(words[0]).slice(0, 2).join('')
      : firstCharOf(words[words.length - 2]) + firstCharOf(words[words.length - 1])

  return raw.toUpperCase()
}
