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
      color: #0f172a;
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
      background-color: #0f172a;
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
      color: #0f172a;
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
