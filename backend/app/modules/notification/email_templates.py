HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ subject }}</title>
</head>
<body style="margin:0; padding:0; background-color:#f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#1e293b; -webkit-font-smoothing:antialiased;">

  <!-- Wrapper -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc; padding:32px 16px;">
    <tr>
      <td align="center">

        <!-- Email Container -->
        <table role="presentation" width="650" cellpadding="0" cellspacing="0" style="width:650px; max-width:650px; background-color:#ffffff; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background-color:#0098db; padding:20px 32px; border-bottom:3px solid #f5871f;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <img src="https://thumua.degoholding.vn/pwa-192.png" width="34" height="34" alt="DEGO"
                         style="display:inline-block; vertical-align:middle; border:0; border-radius:6px; background-color:#ffffff;">
                    <span style="display:inline-block; vertical-align:middle; margin-left:10px; font-size:18px; font-weight:700; color:#ffffff; letter-spacing:1px; text-transform:uppercase;">DEGO HOLDING</span>
                  </td>
                  <td align="right" style="vertical-align:middle;">
                    <span style="font-size:13px; color:#e0f2fe; font-weight:500;">MINITOOL THU MUA</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body Content -->
          <tr>
            <td style="padding:40px 32px;">

              {% if is_urgent %}
              <!-- Urgent Badge -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
                <tr>
                  <td style="background-color:#fef2f2; border:1px solid #fecaca; border-radius:4px; padding:8px 14px;">
                    <span style="font-size:12px; font-weight:700; color:#dc2626; text-transform:uppercase; letter-spacing:0.5px;">&#9679; Đơn gấp &mdash; cần xử lý sớm</span>
                  </td>
                </tr>
              </table>
              {% endif %}

              <h2 style="margin:0 0 24px 0; font-size:20px; font-weight:700; color:#0098db; line-height:1.3;">
                {{ subject }}
              </h2>

              {% if recipient_name %}
              <p style="margin:0 0 16px 0; font-size:15px; font-weight:600; color:#1e293b;">
                Kính gửi {{ recipient_name }},
              </p>
              {% endif %}

              <p style="margin:0 0 24px 0; font-size:14px; line-height:1.6; color:#475569;">
                {{ intro_message }}
              </p>

              <!-- Details Table -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9; border-radius:6px; margin-bottom:24px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px; color:#1e293b;">
                      <tr>
                        <td width="38%" style="padding-bottom:10px; color:#475569; font-weight:500;">Loại chứng từ:</td>
                        <td style="padding-bottom:10px; font-weight:700; color:#0098db;">{{ doc_type }}</td>
                      </tr>
                      <tr>
                        <td style="padding-bottom:10px; color:#475569; font-weight:500;">Mã số:</td>
                        <td style="padding-bottom:10px; font-weight:700; color:#0098db;">{{ doc_code }}</td>
                      </tr>
                      {% if creator %}
                      <tr>
                        <td style="color:#475569; font-weight:500;">Người tạo:</td>
                        <td style="font-weight:700; color:#0098db;">{{ creator }}</td>
                      </tr>
                      {% endif %}
                    </table>
                  </td>
                </tr>
              </table>

              {% if reason %}
              <!-- Rejection Reason -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:4px solid #dc2626; background-color:#fef2f2; margin-bottom:24px;">
                <tr>
                  <td style="padding:14px 20px; font-size:13.5px; line-height:1.6; color:#7f1d1d;">
                    <strong style="color:#dc2626;">Lý do từ chối:</strong><br>{{ reason }}
                  </td>
                </tr>
              </table>
              {% endif %}

              {% if approve_note %}
              <!-- Approve Note -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:4px solid #16a34a; background-color:#f0fdf4; margin-bottom:24px;">
                <tr>
                  <td style="padding:14px 20px; font-size:13.5px; line-height:1.6; color:#14532d;">
                    <strong style="color:#16a34a;">Ghi chú duyệt:</strong><br>{{ approve_note }}
                  </td>
                </tr>
              </table>
              {% endif %}

              <p style="margin:0 0 16px 0; font-size:14px; line-height:1.6; color:#475569;">
                Anh/Chị vui lòng click vào nút bên dưới để xem chi tiết và xử lý chứng từ:
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin:0 auto 28px auto;">
                <tr>
                  <td align="center" style="background-color:#0098db; border-radius:4px;">
                    <a href="{{ link }}" target="_blank"
                       style="display:inline-block; padding:12px 32px; font-size:14px; font-weight:700; color:#ffffff; text-decoration:none; letter-spacing:0.5px; border-radius:4px;">
                      XEM CHI TIẾT TẠI ĐÂY
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 24px 0; font-size:13px; line-height:1.6; color:#64748b;">
                Nếu nút trên không hoạt động, Anh/Chị có thể sao chép liên kết dưới đây dán vào trình duyệt: <br>
                <a href="{{ link }}" target="_blank" style="color:#1c9cf0; word-break:break-all;">{{ link }}</a>
              </p>

              <!-- Closing Signature -->
              <p style="margin:0 0 4px 0; font-size:14px; color:#475569;">Trân trọng,</p>
              <p style="margin:0; font-size:14px; font-weight:700; color:#0098db;">HỆ THỐNG MINITOOL THU MUA</p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="background-color:#f1f5f9; padding:16px; border-top:1px solid #e2e8f0;">
              <span style="font-size:12px; color:#64748b; font-weight:600; letter-spacing:0.5px;">HỆ THỐNG MINITOOL &copy; 2026</span>
            </td>
          </tr>

        </table>

        <!-- Automatic Disclaimer -->
        <p style="margin:16px 0 0 0; font-size:11px; color:#94a3b8; text-align:center;">
          Đây là email tự động gửi từ hệ thống MiniTool Thu Mua. Vui lòng không trả lời trực tiếp email này.
        </p>

      </td>
    </tr>
  </table>

</body>
</html>
"""

ACCOUNT_CREATION_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Thông báo cấp tài khoản MiniTool</title>
</head>
<body style="margin:0; padding:0; background-color:#f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#1e293b; -webkit-font-smoothing:antialiased;">

  <!-- Wrapper -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc; padding:32px 16px;">
    <tr>
      <td align="center">

        <!-- Email Container -->
        <table role="presentation" width="650" cellpadding="0" cellspacing="0" style="width:650px; max-width:650px; background-color:#ffffff; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background-color:#0098db; padding:24px 32px; border-bottom:3px solid #f5871f;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <span style="font-size:18px; font-weight:700; color:#ffffff; letter-spacing:1px; text-transform:uppercase;">DEGO HOLDING</span>
                  </td>
                  <td align="right">
                    <span style="font-size:13px; color:#94a3b8; font-weight:500;">MINITOOL</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body Content -->
          <tr>
            <td style="padding:40px 32px;">

              <h2 style="margin:0 0 24px 0; font-size:20px; font-weight:700; color:#0098db; line-height:1.3;">
                Thông Báo Cấp Tài Khoản Hệ Thống MiniTool
              </h2>

              <p style="margin:0 0 16px 0; font-size:15px; font-weight:600; color:#0098db;">
                Kính gửi: Anh/Chị {{ full_name }}
              </p>

              <p style="margin:0 0 24px 0; font-size:14px; line-height:1.6; color:#475569;">
                Ban Quản trị Hệ thống MiniTool xin gửi đến Anh/Chị thông tin tài khoản đăng nhập để sử dụng hệ thống. Chi tiết tài khoản như sau:
              </p>

              <!-- Credentials Table -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9; border-radius:6px; margin-bottom:24px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px; color:#1e293b;">
                      <tr>
                        <td width="35%" style="padding-bottom:10px; color:#475569; font-weight:500;">Họ và tên:</td>
                        <td style="padding-bottom:10px; font-weight:700; color:#0098db;">{{ full_name }}</td>
                      </tr>
                      <tr>
                        <td style="padding-bottom:10px; color:#475569; font-weight:500;">Tài khoản đăng nhập:</td>
                        <td style="padding-bottom:10px; font-weight:700; color:#0098db;">{{ email }}</td>
                      </tr>
                      <tr>
                        <td style="color:#475569; font-weight:500;">Đường dẫn hệ thống:</td>
                        <td style="font-weight:700; color:#0098db;"><a href="{{ login_url }}" style="color:#1c9cf0; text-decoration:none;">{{ login_url }}</a></td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 16px 0; font-size:14px; line-height:1.6; color:#475569;">
                Anh/Chị vui lòng click vào nút bên dưới để thực hiện thiết lập mật khẩu mới cho tài khoản và bắt đầu kích hoạt:
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                <tr>
                  <td style="background-color:#0098db; border-radius:4px;">
                    <a href="{{ link }}" target="_blank"
                       style="display:inline-block; padding:12px 32px; font-size:14px; font-weight:700; color:#ffffff; text-decoration:none; letter-spacing:0.5px; border-radius:4px;">
                      THIẾT LẬP MẬT KHẨU MỚI
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 24px 0; font-size:13px; line-height:1.6; color:#64748b;">
                Nếu nút trên không hoạt động, Anh/Chị có thể sao chép liên kết dưới đây dán vào trình duyệt: <br>
                <a href="{{ link }}" target="_blank" style="color:#1c9cf0; word-break:break-all;">{{ link }}</a>
              </p>

              <!-- Security Alert Box -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:4px solid #f5871f; background-color:#fffbeb; margin-bottom:28px;">
                <tr>
                  <td style="padding:14px 20px; font-size:13px; line-height:1.5; color:#78350f;">
                    <strong>Lưu ý bảo mật:</strong> Để đảm bảo an toàn thông tin, vui lòng <strong>thiết lập mật khẩu mạnh và đổi lại mật khẩu trong lần đăng nhập đầu tiên</strong>. Tuyệt đối không chia sẻ tài khoản này với người khác.
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 24px 0; font-size:14px; line-height:1.6; color:#475569;">
                Nếu cần hỗ trợ trong quá trình sử dụng hệ thống, Anh/Chị vui lòng gửi yêu cầu hỗ trợ đến Ban Quản trị Hệ thống MiniTool.
              </p>

              <!-- Closing Signature -->
              <p style="margin:0 0 4px 0; font-size:14px; color:#475569;">Trân trọng kính chào,</p>
              <p style="margin:0; font-size:14px; font-weight:700; color:#0098db;">BAN QUẢN TRỊ HỆ THỐNG MINITOOL</p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="background-color:#f1f5f9; padding:16px; border-top:1px solid #e2e8f0;">
              <span style="font-size:12px; color:#64748b; font-weight:600; letter-spacing:0.5px;">HỆ THỐNG MINITOOL &copy; 2026</span>
            </td>
          </tr>

        </table>

        <!-- Automatic Disclaimer -->
        <p style="margin:16px 0 0 0; font-size:11px; color:#94a3b8; text-align:center;">
          Đây là email tự động gửi từ hệ thống MiniTool. Vui lòng không trả lời trực tiếp email này.
        </p>

      </td>
    </tr>
  </table>

</body>
</html>
"""

PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Khôi phục mật khẩu MiniTool</title>
</head>
<body style="margin:0; padding:0; background-color:#f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#1e293b; -webkit-font-smoothing:antialiased;">

  <!-- Wrapper -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc; padding:32px 16px;">
    <tr>
      <td align="center">

        <!-- Email Container -->
        <table role="presentation" width="650" cellpadding="0" cellspacing="0" style="width:650px; max-width:650px; background-color:#ffffff; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background-color:#0098db; padding:24px 32px; border-bottom:3px solid #f5871f;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <span style="font-size:18px; font-weight:700; color:#ffffff; letter-spacing:1px; text-transform:uppercase;">DEGO HOLDING</span>
                  </td>
                  <td align="right">
                    <span style="font-size:13px; color:#94a3b8; font-weight:500;">MINITOOL</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body Content -->
          <tr>
            <td style="padding:40px 32px;">

              <h2 style="margin:0 0 24px 0; font-size:20px; font-weight:700; color:#0098db; line-height:1.3;">
                Yêu Cầu Thiết Lập Lại Mật Khẩu
              </h2>

              <p style="margin:0 0 16px 0; font-size:15px; font-weight:600; color:#0098db;">
                Kính gửi: Anh/Chị {{ full_name }}
              </p>

              <p style="margin:0 0 24px 0; font-size:14px; line-height:1.6; color:#475569;">
                Chúng tôi nhận được yêu cầu khôi phục/thiết lập lại mật khẩu cho tài khoản đăng nhập hệ thống MiniTool của Anh/Chị:
              </p>

              <!-- Credentials Table -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9; border-radius:6px; margin-bottom:24px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px; color:#1e293b;">
                      <tr>
                        <td width="35%" style="color:#475569; font-weight:500;">Tài khoản đăng nhập:</td>
                        <td style="font-weight:700; color:#0098db;">{{ email }}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 16px 0; font-size:14px; line-height:1.6; color:#475569;">
                Vui lòng click vào nút bên dưới để thực hiện thiết lập mật khẩu mới:
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                <tr>
                  <td style="background-color:#0098db; border-radius:4px;">
                    <a href="{{ link }}" target="_blank"
                       style="display:inline-block; padding:12px 32px; font-size:14px; font-weight:700; color:#ffffff; text-decoration:none; letter-spacing:0.5px; border-radius:4px;">
                      THIẾT LẬP MẬT KHẨU MỚI
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 24px 0; font-size:13px; line-height:1.6; color:#64748b;">
                Nếu nút trên không hoạt động, Anh/Chị có thể sao chép liên kết dưới đây dán vào trình duyệt: <br>
                <a href="{{ link }}" target="_blank" style="color:#1c9cf0; word-break:break-all;">{{ link }}</a>
              </p>

              <!-- Security Alert Box -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:4px solid #f5871f; background-color:#fffbeb; margin-bottom:28px;">
                <tr>
                  <td style="padding:14px 20px; font-size:13px; line-height:1.5; color:#78350f;">
                    <strong>Lưu ý:</strong> Yêu cầu thiết lập lại mật khẩu này chỉ có hiệu lực trong vòng 24 giờ. Nếu Anh/Chị không gửi yêu cầu này, vui lòng bỏ qua email hoặc liên hệ với Ban Quản trị để được hỗ trợ.
                  </td>
                </tr>
              </table>

              <!-- Closing Signature -->
              <p style="margin:0 0 4px 0; font-size:14px; color:#475569;">Trân trọng kính chào,</p>
              <p style="margin:0; font-size:14px; font-weight:700; color:#0098db;">BAN QUẢN TRỊ HỆ THỐNG MINITOOL</p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="background-color:#f1f5f9; padding:16px; border-top:1px solid #e2e8f0;">
              <span style="font-size:12px; color:#64748b; font-weight:600; letter-spacing:0.5px;">HỆ THỐNG MINITOOL &copy; 2026</span>
            </td>
          </tr>

        </table>

        <!-- Automatic Disclaimer -->
        <p style="margin:16px 0 0 0; font-size:11px; color:#94a3b8; text-align:center;">
          Đây là email tự động gửi từ hệ thống MiniTool. Vui lòng không trả lời trực tiếp email này.
        </p>

      </td>
    </tr>
  </table>

</body>
</html>
"""
