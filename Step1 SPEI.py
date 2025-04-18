import os
import numpy as np
import pandas as pd
from scipy.stats import gamma, norm

# 输入与输出文件夹路径
input_folder = r'D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\PET stations'  # 输入站点数据文件夹
output_folder = r'D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SPEI Output'  # SPEI 输出文件夹

# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 时间尺度列表
time_scales = [21]  # SPEI 计算的时间窗口

# 数据清理阈值
threshold = 1e-10  # 将非常小的值替换为 0

# SPEI 计算函数
def calculate_spei(df, time_scale):
    """计算指定时间尺度的 SPEI 值"""
    # 计算每日水分盈亏 D = P - PET
    df['D'] = df['Precipitation'] - df['PET']
    df[f'SPEI_{time_scale}'] = np.nan

    # 滑动窗口累积 D
    cumulative_d = df['D'].rolling(window=time_scale, min_periods=1).sum()

    # 标准化为 SPEI
    valid_values = cumulative_d[cumulative_d > 0].dropna()
    if len(valid_values) > 0:
        try:
            shape, loc, scale = gamma.fit(valid_values, floc=0)  # Gamma 分布拟合
            cdf = gamma.cdf(cumulative_d, shape, loc=loc, scale=scale)  # 计算 CDF
            spei_values = norm.ppf(cdf)  # 转换为标准正态分布值
            df[f'SPEI_{time_scale}'] = spei_values
        except Exception as e:
            print(f"Error during SPEI calculation for time scale {time_scale}: {e}")
            df[f'SPEI_{time_scale}'] = np.nan
    else:
        print(f"Insufficient valid data for SPEI calculation at time scale {time_scale}.")
        df[f'SPEI_{time_scale}'] = np.nan

    return df

# 处理每个站点文件
for filename in os.listdir(input_folder):
    if filename.endswith('.csv'):
        file_path = os.path.join(input_folder, filename)
        df = pd.read_csv(file_path)

        # 数据清理：替换非常小的降水值为 0
        df['Precipitation'] = df['Precipitation'].apply(lambda x: 0 if abs(x) < threshold else x)

        # 检查数据列是否存在
        if 'Precipitation' not in df.columns or 'PET' not in df.columns:
            print(f"Missing required columns in {filename}. Skipping...")
            continue

        # 针对每个时间尺度计算 SPEI
        for time_scale in time_scales:
            df = calculate_spei(df, time_scale)

        # 保存 SPEI 计算结果
        output_path = os.path.join(output_folder, f"{filename.replace('.csv', '_spei.csv')}")
        df.to_csv(output_path, index=False)
        print(f"Processed and saved SPEI for {filename}.")

print("All station files processed.")
