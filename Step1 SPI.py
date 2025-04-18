import pandas as pd
import numpy as np
import os
from scipy.stats import gamma, norm

# 输入与输出文件夹路径
input_folder = r'D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\PET stations'
output_folder_spi = r'D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SPI Output'

# 如果输出文件夹不存在，则创建
if not os.path.exists(output_folder_spi):
    os.makedirs(output_folder_spi)


def calculate_spi(precipitation):
    """
    计算标准化降水指数（SPI）。
    :param precipitation: 一个包含累积降水量的数组
    :return: 计算后的 SPI 值数组
    """
    valid_precipitation = precipitation[precipitation > 0]

    if len(valid_precipitation) > 0:
        try:
            # 拟合 Gamma 分布
            shape, loc, scale = gamma.fit(valid_precipitation, floc=0)
            gamma_cdf = gamma.cdf(precipitation, shape, loc=loc, scale=scale)

            # 转换为标准正态分布（SPI）
            spi_values = norm.ppf(gamma_cdf)
            spi_values = np.clip(spi_values, -5, 5)  # 限制 SPI 值范围，便于可视化
        except Exception as e:
            print(f"SPI 计算时出错: {e}")
            spi_values = np.full_like(precipitation, np.nan)
    else:
        spi_values = np.full_like(precipitation, np.nan)

    return spi_values


# 时间尺度列表
time_scales = [21]

# 遍历输入文件夹中的每个 CSV 文件
for filename in os.listdir(input_folder):
    if filename.endswith('.csv'):
        file_path = os.path.join(input_folder, filename)
        df = pd.read_csv(file_path)

        # 替换非常小的值为零
        threshold = 1e-10
        df['Precipitation'] = df['Precipitation'].apply(lambda x: 0 if abs(x) < threshold else x)

        # 为每个时间尺度计算 SPI
        for time_scale in time_scales:
            # 计算累积降水量
            df[f'Accumulated_Precipitation_{time_scale}d'] = df['Precipitation'].rolling(window=time_scale,
                                                                                         min_periods=1).sum()

            # 提取累积降水量并计算 SPI
            accumulated_precipitation = df[f'Accumulated_Precipitation_{time_scale}d'].values
            df[f'SPI_{time_scale}d'] = calculate_spi(accumulated_precipitation)

        # 保存结果
        output_filename = filename.replace('.csv', '_SPI_Multiple_Scales.csv')
        output_file_path_spi = os.path.join(output_folder_spi, output_filename)
        df.to_csv(output_file_path_spi, index=False)

        print(f"已完成 {filename} 的 SPI 计算，并保存为 {output_filename}！")

