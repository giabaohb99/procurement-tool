# -*- coding: utf-8 -*-
"""Đồng bộ DB local -> 192.168.1.60 (GHI ĐÈ). Copy CẢ schema + data (khớp migration mới).
Chạy từ Windows host: python data/sync_to_60.py
(Docker Desktop Windows không route được LAN nên phải chạy ở host qua pymysql.)
"""
import pymysql

SRC = dict(host="127.0.0.1",    port=3306, user="app", password="app_password", db="procurement")
DST = dict(host="192.168.1.60", port=3306, user="app", password="app_password", db="procurement")


def conn(c):
    return pymysql.connect(host=c["host"], port=c["port"], user=c["user"],
                           password=c["password"], database=c["db"], charset="utf8mb4", autocommit=False)


src = conn(SRC); dst = conn(DST)
sc = src.cursor(); dc = dst.cursor()

sc.execute("select table_name from information_schema.tables "
           "where table_schema=%s and table_type='BASE TABLE'", (SRC["db"],))
tables = [r[0] for r in sc.fetchall()]
print("Bang local:", len(tables))

dc.execute("SET FOREIGN_KEY_CHECKS=0")
total = 0
for t in tables:
    sc.execute("SHOW CREATE TABLE `%s`" % t)
    ddl = sc.fetchone()[1]
    dc.execute("DROP TABLE IF EXISTS `%s`" % t)
    dc.execute(ddl)
    sc.execute("SELECT * FROM `%s`" % t)
    rows = sc.fetchall()
    if rows:
        ph = ",".join(["%s"] * len(rows[0]))
        sql = "INSERT INTO `%s` VALUES (%s)" % (t, ph)
        for i in range(0, len(rows), 500):
            dc.executemany(sql, rows[i:i + 500])
    total += len(rows)
    print("  %-34s %6d dong" % (t, len(rows)))
dc.execute("SET FOREIGN_KEY_CHECKS=1")
dst.commit()
print("XONG. Tong dong copy:", total)
src.close(); dst.close()
