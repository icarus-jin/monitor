import datetime
from datetime import timedelta

import pymysql


conn = pymysql.connect(
    host='118.25.113.4',
    user='root',
    password='root',
    database='jdhydevicedb',
    port=3306,
    charset='utf8mb4',
    autocommit=False
)

cur = conn.cursor()

cur.execute('DELETE FROM `03004imb_icemassbalancebuoy`')
cur.execute('DELETE FROM `03001idb_icedriftbuoy`')
cur.execute('DELETE FROM `device_list`')

now = datetime.datetime.now().replace(microsecond=0)

devices = [
    ('南极浮标A', 'NB001', 'IR-NB001', 'buoy', -69.2, 76.3, '中科院-南极'),
    ('南极浮标B', 'NB002', 'IR-NB002', 'buoy', -70.1, 79.1, '中科院-南极'),
    ('北极浮标A', 'AB001', 'IR-AB001', 'buoy', 81.4, -145.2, '中科院-北极'),
    ('北极气象站A', 'AS001', 'IR-AS001', 'station', 82.1, -120.5, '中科院-北极'),
    ('亚太气象站A', 'AP001', 'IR-AP001', 'station', 35.3, 120.8, '青岛-亚太'),
    ('亚太气象站B', 'AP002', 'IR-AP002', 'station', 31.2, 121.6, '上海-亚太')
]

for name, devid, iridiumid, dtype, base_lat, base_lon, ownership in devices:
    sensorflag = 'aws' if dtype == 'station' else 'buoy'
    cur.execute(
        """
        INSERT INTO `device_list`
        (`name`,`devid`,`iridiumid`,`sensorflag`,`latflag`,`lat`,`lonflag`,`lon`,`workstate`,`display`,`ownership`)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            name,
            devid,
            iridiumid,
            sensorflag,
            1 if base_lat < 0 else 0,
            abs(base_lat),
            1 if base_lon < 0 else 0,
            abs(base_lon),
            1,
            1,
            ownership,
        )
    )

    for h in range(48):
        t = now - timedelta(hours=47 - h)
        lat = base_lat + (0.02 * h if dtype == 'buoy' else 0)
        lon = base_lon + (0.015 * h if dtype == 'buoy' else 0)

        latflag = 1 if lat < 0 else 0
        lonflag = 1 if lon < 0 else 0
        alat = abs(lat)
        alon = abs(lon)

        if dtype == 'buoy':
            cur.execute(
                """
                INSERT INTO `03001idb_icedriftbuoy`
                (`sn`,`devid`,`time`,`iridiumid`,`latflag`,`lat`,`lonflag`,`lon`,`board_voltage`,`board_temp`,`atmosphere`,`uploaded`)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
                """,
                (
                    10000 + h,
                    devid,
                    t,
                    iridiumid,
                    latflag,
                    alat,
                    lonflag,
                    alon,
                    12.6 - 0.01 * h,
                    -22 + 0.3 * h,
                    1008 + 0.2 * h,
                )
            )

        cur.execute(
            """
            INSERT INTO `03004imb_icemassbalancebuoy`
            (`sn`,`devid`,`time`,`iridiumid`,`latflag`,`lat`,`lonflag`,`lon`,`board_voltage`,`board_temp`,`air_temp`,`air_humid`,`atmosphere`,`wind_direct`,`wind_speed`,`uploaded`)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            """,
            (
                20000 + h,
                devid,
                t,
                iridiumid,
                latflag,
                alat,
                lonflag,
                alon,
                12.4 - 0.008 * h,
                -20 + 0.25 * h,
                -15 + 0.35 * h,
                65 + (h % 20),
                1005 + 0.15 * h,
                80 + (h % 180),
                3.2 + 0.05 * h,
            )
        )

conn.commit()
conn.close()
print('raw seed done')
