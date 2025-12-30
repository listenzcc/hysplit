import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.interpolate import griddata
import os


def read_hysplit_Clentration_file(filename):
    """
    读取HYSPLIT浓度数据文件

    Args:
        filename: 数据文件名（如 Clentration.txt_122_18）

    Returns:
        DataFrame: 包含经纬度和浓度值的数据框
    """
    print(f"正在读取文件: {filename}")

    try:
        # 方法1：使用pandas读取（如果格式规整）
        with open(filename, 'r') as f:
            first_line = f.readline().strip()

        # 解析列名
        columns = first_line.split()

        # 读取数据
        df = pd.read_csv(
            filename,
            delim_whitespace=True,
            skiprows=1,
            names=columns,
            engine='python'
        )

        print(f"成功读取 {len(df)} 行数据")
        print(f"列名: {df.columns.tolist()}")
        print(f"数据预览:")
        print(df.head())

        return df

    except Exception as e:
        print(f"标准读取方式失败: {e}")
        print("尝试备用读取方式...")

        # 方法2：手动读取（更灵活）
        data = []
        with open(filename, 'r') as f:
            # 跳过标题行
            header = f.readline()

            for line in f:
                line = line.strip()
                if line:  # 跳过空行
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            # 转换为数值
                            day = int(float(parts[0]))
                            hour = int(float(parts[1]))
                            lat = float(parts[2])
                            lon = float(parts[3])
                            Cl = float(parts[4])

                            data.append({
                                'DAY': day,
                                'HR': hour,
                                'LAT': lat,
                                'LON': lon,
                                'Cl': Cl
                            })
                        except:
                            continue

        if data:
            df = pd.DataFrame(data)
            print(f"备用方式读取成功: {len(df)} 行数据")
            return df
        else:
            raise ValueError(f"无法读取文件 {filename}")


def create_contour_plot(df, output_file='Clentration_contour.png',
                        title=None, cmap='hot_r', levels=20,
                        interpolation='linear', add_colorbar=True):
    """
    创建浓度等高线图

    Args:
        df: 包含数据的DataFrame
        output_file: 输出图片文件名
        title: 图表标题
        cmap: 颜色映射
        levels: 等高线层级数
        interpolation: 插值方法 ('linear', 'cubic', 'nearest')
        add_colorbar: 是否添加颜色条
    """

    # 提取数据
    lats = df['LAT'].values
    lons = df['LON'].values
    Cls = df['Cl'].values

    print(f"数据范围:")
    print(f"  纬度: {lats.min():.3f} ~ {lats.max():.3f}")
    print(f"  经度: {lons.min():.3f} ~ {lons.max():.3f}")
    print(f"  浓度: {Cls.min():.2e} ~ {Cls.max():.2e}")

    # 创建规则网格
    lat_grid = np.linspace(lats.min(), lats.max(), 200)
    lon_grid = np.linspace(lons.min(), lons.max(), 200)
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

    # 插值到规则网格
    print(f"正在插值到规则网格 ({interpolation} 方法)...")
    Cl_grid = griddata(
        (lons, lats),  # 原始点坐标
        Cls,         # 原始点值
        (lon_mesh, lat_mesh),  # 目标网格
        method=interpolation,
        fill_value=0  # 填充值
    )

    # 创建图形
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 子图1：等高线填充图
    ax1 = axes[0]
    contourf = ax1.contourf(
        lon_mesh, lat_mesh, Cl_grid,
        levels=levels,
        cmap=cmap,
        extend='both'
    )

    # 添加等高线
    contour_lines = ax1.contour(
        lon_mesh, lat_mesh, Cl_grid,
        levels=levels,
        colors='black',
        linewidths=0.5,
        alpha=0.5
    )

    # 添加等高线标签
    ax1.clabel(contour_lines, inline=True, fontsize=8, fmt='%.1e')

    # 添加原始数据点
    ax1.scatter(lons, lats, c='blue', s=10, alpha=0.3, label='数据点')

    ax1.set_xlabel('经度 (°E)', fontsize=12)
    ax1.set_ylabel('纬度 (°N)', fontsize=12)
    if title:
        ax1.set_title(f'{title} - 等高线填充图', fontsize=14)
    else:
        day = df['DAY'].iloc[0] if 'DAY' in df.columns else '未知'
        hour = df['HR'].iloc[0] if 'HR' in df.columns else '未知'
        ax1.set_title(f'浓度分布 - 第{day}天 {hour:02d}:00 UTC', fontsize=14)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper right')

    # 添加颜色条
    if add_colorbar:
        cbar = fig.colorbar(contourf, ax=ax1, orientation='vertical', pad=0.1)
        cbar.set_label('浓度', fontsize=12)

    # 子图2：3D曲面图
    ax2 = axes[1]
    ax2 = fig.add_subplot(122, projection='3d')

    # 绘制3D曲面
    surf = ax2.plot_surface(
        lon_mesh, lat_mesh, Cl_grid,
        cmap=cmap,
        edgecolor='none',
        alpha=0.8,
        antialiased=True
    )

    ax2.set_xlabel('经度 (°E)', fontsize=10)
    ax2.set_ylabel('纬度 (°N)', fontsize=10)
    ax2.set_zlabel('浓度', fontsize=10)
    ax2.set_title('3D浓度曲面', fontsize=14)

    # 添加颜色条
    if add_colorbar:
        fig.colorbar(surf, ax=ax2, shrink=0.5, aspect=5, label='浓度')

    plt.tight_layout()

    # 保存图像
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"图表已保存为: {output_file}")

    plt.show()

    return fig, axes


def create_simple_contour(df, output_file='simple_contour.png'):
    """
    创建简单的等高线图
    """
    # 创建规则网格
    xi = np.linspace(df['LON'].min(), df['LON'].max(), 100)
    yi = np.linspace(df['LAT'].min(), df['LAT'].max(), 100)
    xi, yi = np.meshgrid(xi, yi)

    # 插值
    zi = griddata((df['LON'], df['LAT']), df['Cl'], (xi, yi), method='cubic')

    # 创建图形
    plt.figure(figsize=(10, 8))

    # 填充等高线
    contour = plt.contourf(xi, yi, zi, 15, cmap=plt.cm.viridis, alpha=0.8)

    # 等高线
    plt.contour(xi, yi, zi, 15, colors='black', linewidths=0.5, alpha=0.5)

    # 原始数据点
    plt.scatter(df['LON'], df['LAT'], c='red', s=20,
                marker='o', edgecolors='black', label='采样点')

    plt.colorbar(contour, label='浓度')
    plt.xlabel('经度')
    plt.ylabel('纬度')

    # 自动生成标题
    day = df['DAY'].iloc[0] if 'DAY' in df.columns else 'N/A'
    hour = df['HR'].iloc[0] if 'HR' in df.columns else 'N/A'
    plt.title(f'HYSPLIT浓度分布 - 第{day}天 {hour:02d}:00 UTC')

    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.show()

    print(f"简单等高线图已保存为: {output_file}")


def analyze_Clentration_data(df):
    """
    分析浓度数据
    """
    print("\n" + "="*50)
    print("数据分析报告")
    print("="*50)

    # 基本统计
    print(f"数据点数: {len(df)}")
    print(f"浓度统计:")
    print(f"  平均值: {df['Cl'].mean():.2e}")
    print(f"  最大值: {df['Cl'].max():.2e} (位置: {df.loc[df['Cl'].idxmax(), 'LAT']:.2f}°N, {df.loc[df['Cl'].idxmax(), 'LON']:.2f}°E)")
    print(f"  最小值: {df['Cl'].min():.2e}")
    print(f"  标准差: {df['Cl'].std():.2e}")

    # 浓度分布
    print(f"\n浓度分布百分位数:")
    percentiles = [0, 25, 50, 75, 90, 95, 99, 100]
    print(df)
    for p in percentiles:
        value = np.percentile(df['Cl'], p)
        print(f"  {p:3d}%: {value:.2e}")

    # 空间范围
    print(f"\n空间范围:")
    print(f"  纬度: {df['LAT'].min():.3f} ~ {df['LAT'].max():.3f}")
    print(f"  经度: {df['LON'].min():.3f} ~ {df['LON'].max():.3f}")

    # 时间信息
    if 'DAY' in df.columns and 'HR' in df.columns:
        print(f"\n时间信息:")
        print(f"  第 {df['DAY'].iloc[0]} 天, {df['HR'].iloc[0]:02d}:00 UTC")


def main():
    """
    主函数：读取文件并绘制等高线图
    """
    # 设置中文字体（如果需要）
    plt.rcParams['font.sans-serif'] = ['SimHei',
                                       'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 设置要读取的文件名
    # 替换为你的实际文件名
    filename = "concentration.txt_122_18"

    try:
        # 1. 读取数据
        df = read_hysplit_Clentration_file(filename)

        # 2. 数据分析
        analyze_Clentration_data(df)

        # 3. 创建完整等高线图
        fig1, axes1 = create_contour_plot(
            df,
            output_file='detailed_Clentration_contour.png',
            title='HYSPLIT污染物浓度分布',
            cmap='RdYlGn_r',  # 红-黄-绿，反转
            levels=30,
            interpolation='cubic'
        )

        # 4. 创建简单版本
        create_simple_contour(
            df, output_file='simple_Clentration_contour.png')

        # 5. 可选：创建其他可视化
        create_additional_plots(df)

    except FileNotFoundError:
        print(f"错误：文件 '{filename}' 未找到！")
        print("请检查：")
        print(f"  1. 文件是否存在")
        print(f"  2. 当前目录: {os.getcwd()}")
        print(
            f"  3. 可用文件: {[f for f in os.listdir('.') if f.startswith('Clentration.txt_')]}")
    except Exception as e:
        print(f"运行过程中出错: {e}")
        import traceback
        traceback.print_exc()


def create_additional_plots(df):
    """
    创建额外的可视化图表
    """
    # 1. 散点图（颜色表示浓度）
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(df['LON'], df['LAT'],
                          c=df['Cl'],
                          cmap='plasma',
                          s=50,
                          alpha=0.7,
                          edgecolors='black',
                          linewidth=0.5)
    plt.colorbar(scatter, label='浓度')
    plt.xlabel('经度')
    plt.ylabel('纬度')
    plt.title('浓度散点分布图')
    plt.grid(True, alpha=0.3)
    plt.savefig('Clentration_scatter.png', dpi=150, bbox_inches='tight')
    plt.show()

    # 2. 直方图（浓度分布）
    plt.figure(figsize=(10, 6))
    plt.hist(np.log10(df['Cl'][df['Cl'] > 0]), bins=50,
             edgecolor='black', alpha=0.7)
    plt.xlabel('log10(浓度)')
    plt.ylabel('频数')
    plt.title('浓度对数分布直方图')
    plt.grid(True, alpha=0.3)
    plt.savefig('Clentration_histogram.png', dpi=150, bbox_inches='tight')
    plt.show()


def batch_process_files(file_pattern="Clentration.txt_*"):
    """
    批量处理多个文件
    """
    import glob

    files = glob.glob(file_pattern)
    print(f"找到 {len(files)} 个文件")

    for i, filename in enumerate(sorted(files), 1):
        print(f"\n处理文件 {i}/{len(files)}: {filename}")
        try:
            df = read_hysplit_Clentration_file(filename)

            # 创建输出文件名
            base_name = os.path.splitext(filename)[0]
            output_png = f"{base_name}_contour.png"

            # 绘制图表
            create_simple_contour(df, output_file=output_png)

            print(f"完成: {output_png}")

        except Exception as e:
            print(f"处理 {filename} 失败: {e}")


if __name__ == "__main__":
    # 运行主程序
    main()

    # 如果需要批量处理，取消注释下面这行
    # batch_process_files("Clentration.txt_*")
