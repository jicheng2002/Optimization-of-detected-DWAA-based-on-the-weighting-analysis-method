import os
import pandas as pd
import numpy as np

# 设置干湿阈值
DRY_THRESHOLD = -1
WET_THRESHOLD = 1
MIN_DURATION = 10  # 最小干湿事件持续天数
TC = 8  # 干湿交替的最大间隔天数
RHO_C = 0.2  # 强度比条件阈值

# 合并连续干湿周期的函数
def merge_periods_ic_method(periods, swap_data, tc, rho_c):
    """合并连续的干湿周期"""
    merged_periods = []
    i = 0
    while i < len(periods) - 1:
        start1, end1 = periods[i]
        start2, end2 = periods[i + 1]

        # 判断两个周期之间的间隔是否小于等于 tc
        interval_duration = start2 - end1 - 1
        if interval_duration <= tc:
            # 计算间隔期和前一段干湿周期的强度比
            si = sum([1 - abs(swap_data[j]) for j in range(end1 + 1, start2)])  # 间隔期强度
            sf = sum([1 - abs(swap_data[j]) for j in range(start1, end1 + 1)])  # 前一段周期强度

            # 检查是否满足合并条件
            if si / sf <= rho_c:
                # 合并两个周期
                merged_periods.append((start1, end2))
                i += 2  # 跳过已合并的下一个周期
                continue

        # 如果不满足合并条件，则保留当前周期
        merged_periods.append((start1, end1))
        i += 1

    # 处理最后一个未合并的周期
    if i == len(periods) - 1:
        merged_periods.append(periods[i])

    return merged_periods

# 探测旱涝急转事件的函数
def detect_dwaa_events(swap_data, dry_threshold, wet_threshold, min_duration=10, tc=8, rho_c=0.2):
    dry_periods = []
    wet_periods = []
    dry_start = None
    wet_start = None

    # 按天遍历数据
    for i in range(len(swap_data)):
        swap_value = swap_data[i]

        # 干旱事件探测
        if swap_value < dry_threshold:
            if dry_start is None:
                dry_start = i
        else:
            if dry_start is not None and i - dry_start >= min_duration:
                dry_periods.append((dry_start, i - 1))
                dry_start = None

        # 湿润事件探测
        if swap_value > wet_threshold:
            if wet_start is None:
                wet_start = i
        else:
            if wet_start is not None and i - wet_start >= min_duration:
                wet_periods.append((wet_start, i - 1))
                wet_start = None

    # 合并干湿周期
    all_periods = dry_periods + wet_periods
    all_periods.sort(key=lambda x: x[0])  # 按开始时间排序
    merged_periods = merge_periods_ic_method(all_periods, swap_data, tc, rho_c)

    # 标记每个月是否发生旱涝急转
    months_detected = np.zeros(len(swap_data), dtype=int)
    for start, end in merged_periods:
        months_detected[start:end + 1] = 1

    return months_detected

# 输入文件夹路径
input_folder_path = r"D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SWAP Output"
# 输出文件夹路径
output_folder_path = r"D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SWAP DWAA Results"

# 确保输出路径存在
os.makedirs(output_folder_path, exist_ok=True)

# 遍历文件夹中的所有CSV文件
for file_name in os.listdir(input_folder_path):
    if file_name.endswith(".csv"):
        # 读取文件
        file_path = os.path.join(input_folder_path, file_name)
        df = pd.read_csv(file_path)

        # 确保文件包含必要的列
        if 'SWAP_21d' in df.columns:
            swap_data = df['SWAP_21d'].values
            df['Year'] = pd.to_datetime(df['Date']).dt.year
            df['Month'] = pd.to_datetime(df['Date']).dt.month
            # 探测事件并记录每个月是否发生
            months_detected = detect_dwaa_events(
                swap_data, DRY_THRESHOLD, WET_THRESHOLD, MIN_DURATION, TC, RHO_C
            )

            # 将结果添加到结果表中
            df['DWAA_Detected'] = months_detected

            # 保存结果到新文件
            output_file_path = os.path.join(output_folder_path, f"DWAA_{file_name}")
            df[['Year', 'Month', 'DWAA_Detected']].to_csv(output_file_path, index=False)

            print(f"旱涝急转探测结果已保存到 {output_file_path}")

print("所有站点的旱涝急转探测结果已完成并保存。")
