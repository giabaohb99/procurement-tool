/**
 * Mấy mức số lượng có sẵn cho ô "được khai mấy văn bản".
 *
 * Trước đây form hỏi thẳng hai ô số `min_count` / `max_count`, và người khai
 * phải tự biết rằng **0 nghĩa là không giới hạn** — con số duy nhất trong form
 * mà giá trị nhỏ nhất lại có nghĩa là lớn nhất. Ba mức dưới đây phủ gần hết
 * trường hợp thật; ai cần khoảng lạ thì chọn "Tùy chỉnh" để hiện lại hai ô số.
 */
export type CountPreset = 'exactly-one' | 'at-least-one' | 'unlimited' | 'custom'

export const COUNT_PRESETS: {
  value: Exclude<CountPreset, 'custom'>
  label: string
  min: number
  max: number
}[] = [
  { value: 'exactly-one', label: 'Đúng 1 văn bản', min: 1, max: 1 },
  { value: 'at-least-one', label: 'Ít nhất 1 văn bản', min: 1, max: 0 },
  { value: 'unlimited', label: 'Không giới hạn', min: 0, max: 0 },
]

/** Cặp số hiện có ứng với mức nào. Không khớp mức nào thì là "Tùy chỉnh". */
export function countPresetOf(min: number, max: number): CountPreset {
  const khop = COUNT_PRESETS.find((item) => item.min === min && item.max === max)
  return khop?.value ?? 'custom'
}
