import csv
from io import StringIO
from fastapi import HTTPException
from fastapi.responses import Response
from app.core.utils import generate_code

def export_csv_response(items, headers_map, filename):
    output = StringIO()
    output.write("sep=,\n")
    writer = csv.writer(output)
    writer.writerow(list(headers_map.values()) + ["Trạng thái"])

    for item in items:
        row = []
        for field in headers_map.keys():
            val = getattr(item, field, "")
            row.append(str(val) if val is not None else "")
        is_active = getattr(item, "is_active", True)
        row.append("Hoạt động" if is_active else "Đã ẩn")
        
        writer.writerow(row)
        
    headers = {"Content-Disposition": f"attachment; filename={filename}.csv"}
    return Response(content=output.getvalue().encode("utf-8-sig"), media_type="text/csv; charset=utf-8", headers=headers)
