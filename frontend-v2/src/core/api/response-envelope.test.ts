import { describe, expect, it } from 'vitest'

import { extractErrorMessage } from './response-envelope'

const FALLBACK = 'Có lỗi xảy ra, vui lòng thử lại'

describe('extractErrorMessage', () => {
  it('ưu tiên thông điệp trong phong bì lỗi của backend', () => {
    const error = {
      message: 'Request failed with status code 400',
      response: {
        data: {
          success: false,
          error: { code: 'VALIDATION', message: 'Ngày giao không được ở quá khứ' },
          message: 'Bad Request',
        },
      },
    }
    // Câu của axios ("Request failed…") tuyệt đối không được lọt ra toast.
    expect(extractErrorMessage(error)).toBe('Ngày giao không được ở quá khứ')
  })

  it('không có error.message thì lấy message ở thân phản hồi', () => {
    const error = { response: { data: { message: 'Phiên đăng nhập đã hết hạn' } } }
    expect(extractErrorMessage(error)).toBe('Phiên đăng nhập đã hết hạn')
  })

  it('lỗi mạng (không có phản hồi) thì lấy message của axios', () => {
    expect(extractErrorMessage({ message: 'Network Error' })).toBe('Network Error')
  })

  it('không đọc được gì thì trả câu mặc định tiếng Việt', () => {
    expect(extractErrorMessage(null)).toBe(FALLBACK)
    expect(extractErrorMessage(undefined)).toBe(FALLBACK)
    expect(extractErrorMessage('vỡ ở đâu đó')).toBe(FALLBACK)
    expect(extractErrorMessage({})).toBe(FALLBACK)
    expect(extractErrorMessage({ response: { data: {} } })).toBe(FALLBACK)
  })

  it('thông điệp rỗng bị coi như không có, rơi xuống mức dưới', () => {
    const error = {
      message: 'Network Error',
      response: { data: { error: { message: '' } } },
    }
    expect(extractErrorMessage(error)).toBe('Network Error')
  })
})
