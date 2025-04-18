import pandas as pd
import numpy as np
import os
from scipy.stats import gamma, norm

# 衰减系数
a = 0.9  # Decay coefficient

# 输入与输出文件夹路径
input_folder = r'D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\PET stations'
output_folder = r'D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SWAP Output'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def classify_climate_zone(avg_precipitation):
    """Classify climate zone based on average precipitation."""
    if avg_precipitation < 200:
        return 'arid'
    elif 200 <= avg_precipitation < 400:
        return 'semi_arid'
    elif 400 <= avg_precipitation < 800:
        return 'semi_humid'
    else:
        return 'humid'

def calculate_wap(precipitation, a, N):
    """Calculate Weighted Average of Precipitation (WAP)."""
    weights = np.array([(1 - a) * a ** n for n in range(N)])
    return np.convolve(precipitation, weights[::-1], mode='valid') / weights.sum()

def standardize_wap_to_swap(wap_values):
    """Standardize WAP to SWAP using a Gamma distribution."""
    valid_wap_values = wap_values[wap_values > 0]
    
    if len(valid_wap_values) > 0:
        try:
            shape, loc, scale = gamma.fit(valid_wap_values, floc=0)
            if scale < 1e-10:
                raise ValueError("Scale parameter too small.")
            gamma_cdf = gamma.cdf(wap_values, shape, loc=loc, scale=scale)
            swap_values = norm.ppf(gamma_cdf)
            swap_values = np.clip(swap_values, -5, 5)
        except Exception as e:
            print(f"Error during SWAP calculation: {e}")
            swap_values = np.full_like(wap_values, np.nan)
    else:
        swap_values = np.full_like(wap_values, np.nan)
    
    return swap_values

# 定义区域类别
CLIMATE_ZONES = {
    'arid': {'dry_threshold': -1, 'wet_threshold': 1},
    'semi_arid': {'dry_threshold': -1, 'wet_threshold': 1},
    'semi_humid': {'dry_threshold': -1, 'wet_threshold': 1},
    'humid': {'dry_threshold': -1, 'wet_threshold': 1}
}

# 根据年均降水量判断站点所属区域
def classify_climate_zone(avg_precipitation):
    if avg_precipitation < 200:
        return 'arid'
    elif 200 <= avg_precipitation < 400:
        return 'semi_arid'
    elif 400 <= avg_precipitation < 800:
        return 'semi_humid'
    else:
        return 'humid'
# 时间尺度列表
time_scales = [21]

# 处理输入文件夹中的每个 CSV 文件
for filename in os.listdir(input_folder):
    if filename.endswith('.csv'):
        file_path = os.path.join(input_folder, filename)
        df = pd.read_csv(file_path)

        # 替换非常小的值为零
        threshold = 1e-10  # 定义一个小阈值
        df['Precipitation'] = df['Precipitation'].apply(lambda x: 0 if abs(x) < threshold else x)
        
        # 计算年均降水量（用于分类气候区域）
        avg_precipitation = df['Precipitation'].mean() * 365
        climate_zone = classify_climate_zone(avg_precipitation)
        
        precipitation = df['Precipitation'].values
        
        # 针对每个时间尺度计算 SWAP
        for time_scale in time_scales:
            column_wap = f'WAP_{time_scale}d'
            column_swap = f'SWAP_{time_scale}d'
            
            if len(precipitation) >= time_scale:
                # 计算 WAP
                wap_values = calculate_wap(precipitation, a, time_scale)
                df[column_wap] = np.nan
                df.loc[time_scale - 1:, column_wap] = wap_values

                # 标准化为 SWAP
                swap_values = standardize_wap_to_swap(wap_values)
                df[column_swap] = np.nan
                df.loc[time_scale - 1:, column_swap] = swap_values
            else:
                print(f"Not enough data points in {filename} for N = {time_scale}.")

        # 保存结果
        output_filename = filename.replace('.csv', '_SWAP.csv')
        output_file_path = os.path.join(output_folder, output_filename)
        df.to_csv(output_file_path, index=False)
        
        print(f"SWAP calculation completed and saved for {filename} as {output_filename}!")

print("All stations processed and SWAP values for multiple scales saved.")
