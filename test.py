import os
import subprocess


def foo():
    # os.chdir('example')
    result = subprocess.run(
        ['ls'],        # 命令
        cwd='example',  # 切换到此目录
        capture_output=True,
        text=True
    )
    print(result)


result = subprocess.run(
    ['ls'],        # 命令
    capture_output=True,
    text=True
)
print(1, result)

foo()

result = subprocess.run(
    ['ls'],        # 命令
    capture_output=True,
    text=True
)
print(2, result)
