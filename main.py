# %%
import os
import time
import uuid
import subprocess
from pathlib import Path

from mk_control import mk_control, mk_emitimes

# %%


def prepare_files(dst: str, points: list, simulation_date: dict):
    """
    准备HYSPLIT所需的输入文件
    dst: 目标目录
    """
    # Path
    src_path = Path('./example')
    dst_path = Path(dst)
    dst_path.mkdir(parents=True, exist_ok=True)

    # Date
    year = simulation_date['year']
    month = simulation_date['month']
    day = simulation_date['day']
    start_hour = simulation_date['start_hour']
    duration_hours = simulation_date['duration_hours']

    for name in ['SETUP.CFG', 'ASCDATA.CFG']:
        (dst_path / name).write_bytes((src_path / name).read_bytes())

    # 生成CONTROL文件，并保存文件
    control_content = mk_control(
        points=points,
        year=year,
        month=month,
        day=day,
        start_hour=start_hour,
        duration_hours=duration_hours,
        meteorology_dir="D:/WeatherData/",
        output_dir="./",
        output_file="cdump"
    )

    with open(dst_path / 'CONTROL', "w", encoding="utf-8") as f:
        f.write(control_content)
        f.write('\n')

    # 生成EMITIMES文件，并保存文件
    emitimes_content = mk_emitimes(
        points, year, month, day, start_hour, 0, duration_hours, 0)

    with open(dst_path / 'EMITIMES', "w", encoding="utf-8") as f:
        f.write(emitimes_content)
        f.write('\n')

    # Generate concplot.bat
    with open(dst_path / 'concplot.bat', 'w', encoding='utf-8') as f:
        f.writelines([
            'echo off\n',
            'C:/hysplit/exec/concplot.exe +g1 -81  -i./cdump -oconcplot.html -jC:/hysplit/graphics/arlmap -f0  -b100 -t100 -e0 -d1 -r1 -c0 -k1 -m0 -s1 -x1.0 -y1.0  -z50 -u -a0 -: -: -: -: -:'
        ])

    # Generate conctxt.bat
    with open(dst_path / 'conctxt.bat', 'w', encoding='utf-8') as f:
        f.writelines([
            'echo off\n',
            'C:/hysplit/exec/con2asc.exe -i./cdump -oconcentration.txt'
        ])

    return


# %%
points = [
    {
        'lat': 32.03,
        'lon': 118.46,
        'height': 10,
        'mass': 100.0,
        'gas': 'Cl',
        'name': '南京'
    },
    {
        'lat': 31.23,
        'lon': 121.47,
        'height': 10,
        'mass': 1.0,
        'gas': 'Cl',
        'name': '上海'
    }
]

simulation_date = {
    'year': 2024,
    'month': 5,
    'day': 2,
    'start_hour': 0,
    'duration_hours': 24
}

# 运行HYSPLIT
session = '-'.join([str(e) for e in [time.time(), uuid.uuid4()]])
dst = f'./hysplit_simulation/{session}'
prepare_files(dst, points, simulation_date)
# subprocess.run(['./hycs_std'], stdin=open('CONTROL'))
# 切换到目标目录执行命令

# os.chdir(dst)

result = subprocess.run(
    ['ls'],        # 命令
    cwd=dst,  # 切换到此目录
    capture_output=True,
    text=True
)
print(result)

result = subprocess.run(
    ["c:\\hysplit\\exec\\hycs_std.exe"],        # 命令
    # stdin=open(Path(dst) / "CONTROL"),  # 输入文件
    cwd=dst,  # 切换到此目录
    capture_output=True,
    text=True
)
print(result)

result = subprocess.run(
    ['cmd.exe', '/c', 'concplot.bat'],
    cwd=dst,  # 切换到此目录
    capture_output=True,
    text=True
)
print(result)

result = subprocess.run(
    ['cmd.exe', '/c', 'conctxt.bat'],
    cwd=dst,  # 切换到此目录
    capture_output=True,
    text=True
)
print(result)

result = subprocess.run(
    ['cmd.exe', '/c', 'start', 'concplot.html'],
    cwd=dst,  # 切换到此目录
    capture_output=True,
    text=True
)
