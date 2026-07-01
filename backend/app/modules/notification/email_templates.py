HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ subject }}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
      color: #0098db;
      background-color: #f8fafc;
      margin: 0;
      padding: 0;
    }
    .wrapper {
      max-width: 600px;
      margin: 24px auto;
      background-color: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .header {
      background-color: #0098db;
      color: #ffffff;
      padding: 24px;
      text-align: center;
    }
    .header h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.025em;
    }
    .urgent-badge {
      background-color: #ef4444;
      color: #ffffff;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 4px 8px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 8px;
    }
    .content {
      padding: 32px 24px;
    }
    .greeting {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 16px;
    }
    .details-table {
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
    }
    .details-table th, .details-table td {
      padding: 10px 12px;
      text-align: left;
      font-size: 13.5px;
      border-bottom: 1px solid #f1f5f9;
    }
    .details-table th {
      width: 150px;
      color: #64748b;
      font-weight: 500;
    }
    .details-table td {
      color: #0098db;
      font-weight: 600;
    }
    .details-table td.notes {
      font-weight: normal;
      color: #475569;
    }
    .btn-container {
      text-align: center;
      margin: 32px 0 16px;
    }
    .btn {
      background-color: #0284c7;
      color: #ffffff !important;
      text-decoration: none;
      padding: 12px 24px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 8px;
      display: inline-block;
      box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.2);
    }
    .footer {
      background-color: #f8fafc;
      padding: 16px 24px;
      font-size: 12px;
      color: #64748b;
      text-align: center;
      border-top: 1px solid #e2e8f0;
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      {% if is_urgent %}
      <div class="urgent-badge">ĐƠN GẤP</div>
      {% endif %}
      <h2>Thu Mua Tool</h2>
    </div>
    <div class="content">
      <div class="greeting">Xin chào,</div>
      <p>{{ intro_message }}</p>
      
      <table class="details-table">
        <tr>
          <th>Loại chứng từ:</th>
          <td>{{ doc_type }}</td>
        </tr>
        <tr>
          <th>Mã số:</th>
          <td>{{ doc_code }}</td>
        </tr>
        {% if creator %}
        <tr>
          <th>Người tạo:</th>
          <td>{{ creator }}</td>
        </tr>
        {% endif %}
        {% if reason %}
        <tr>
          <th>Lý do từ chối:</th>
          <td class="notes">{{ reason }}</td>
        </tr>
        {% endif %}
        {% if approve_note %}
        <tr>
          <th>Ghi chú duyệt:</th>
          <td class="notes">{{ approve_note }}</td>
        </tr>
        {% endif %}
      </table>

      <div class="btn-container">
        <a href="{{ link }}" class="btn">Xem Chi Tiết Chứng Từ</a>
      </div>
    </div>
    <div class="footer">
      Đây là email tự động từ hệ thống quản lý thu mua. Vui lòng không trả lời email này.
    </div>
  </div>
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
