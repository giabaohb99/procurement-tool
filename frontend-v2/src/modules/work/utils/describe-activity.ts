import type { WorkActivity } from '../types/activity'

/**
 * Câu kể của một dòng hoạt động, phần đứng SAU tên người: `đã tạo công việc: X`.
 *
 * Backend đã ghi sẵn câu đầy đủ (`Tạo công việc: X`, `Mời nhân sự #4 vào danh
 * sách`), việc ở đây chỉ là ghép nó vào sau tên cho thành câu tiếng Việt tự
 * nhiên — KHÔNG dựng lại câu từ `action` + `entity`, làm thế là chép nghiệp vụ
 * sang tầng hai và hai bên lệch nhau ngay ở lần sửa kế tiếp.
 */
export function describeActivity(activity: WorkActivity): string {
  const message = stripTaskTitle((activity.message || '').trim(), activity.task_title)
  //  Không có câu ghi log thì rơi về nhãn hành động ("Cập nhật") — dòng trống
  //  trơn thì người đọc không biết chuyện gì đã xảy ra.
  const text = message || activity.action_label || ''
  return text ? `đã ${lowerFirst(text)}` : ''
}

/**
 * Bỏ cái đuôi `: {tên việc}` khi tên việc đã hiện ở dòng trên.
 *
 * Backend ghi cả câu (`Sửa công việc: Dựng khung`) vì nhật ký của nó phải đọc
 * được một mình. Trên tab «Hoạt động» thì tên việc đứng riêng một dòng, để
 * nguyên là mỗi dòng lặp tên việc hai lần — đúng chỗ trông rối nhất.
 *
 * So bằng ĐÚNG cả đuôi chứ không cắt ở dấu hai chấm cuối: câu
 * `Thêm phụ thuộc: A → B` cũng có dấu hai chấm mà phần sau KHÔNG phải tên việc,
 * cắt là mất luôn nội dung.
 */
function stripTaskTitle(message: string, taskTitle: string): string {
  const title = (taskTitle || '').trim()
  if (!title) return message
  const suffix = `: ${title}`
  return message.endsWith(suffix) ? message.slice(0, -suffix.length) : message
}

/**
 * Hạ chữ cái đầu — `Tạo công việc` → `tạo công việc`.
 *
 * Bỏ qua nếu chữ đầu vốn đã thường hoặc không phải chữ cái (câu bắt đầu bằng số
 * hay ký hiệu), và bỏ qua cả khi HAI chữ đầu đều hoa (viết tắt kiểu `YCMH`) —
 * hạ chữ đầu của viết tắt là làm hỏng nó.
 */
function lowerFirst(text: string): string {
  const [first, second] = [text[0], text[1] ?? '']
  if (first !== first.toLocaleUpperCase('vi')) return text
  if (second && second === second.toLocaleUpperCase('vi') && /\p{L}/u.test(second)) return text
  return first.toLocaleLowerCase('vi') + text.slice(1)
}
