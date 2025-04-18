import os
import pandas as pd

# 文件夹路径
swap_folder = r"D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SWAP DWAA Results"
spi_folder = r"D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SPI DWAA Results"
spei_folder = r"D:\A-Projects\DWAA Project\2 Optimization of detected DWAA based on the weighting analysis method\SPEI DWAA Results"

# 提取事件的开始和结束时间
def extract_events(data):
    events = []
    in_event = False
    start_date = None

    for i, detected in enumerate(data['DWAA_Detected']):
        if detected == 1 and not in_event:
            # 事件开始
            start_date = data['Full_Date'].iloc[i]
            in_event = True
        elif detected == 0 and in_event:
            # 事件结束
            end_date = data['Full_Date'].iloc[i - 1]
            events.append((start_date, end_date))
            in_event = False

    # 如果最后一天仍在事件中
    if in_event:
        end_date = data['Full_Date'].iloc[-1]
        events.append((start_date, end_date))

    return events

# 计算严格的事件交集（仅统计被三种指数同时探测到的事件）
def calculate_strict_intersection(events1, events2, events3):
    intersection_events = []

    for event1 in events1:
        for event2 in events2:
            for event3 in events3:
                # 判断三者是否有完全重叠的时间段
                overlap_start = max(pd.to_datetime(event1[0]), pd.to_datetime(event2[0]), pd.to_datetime(event3[0]))
                overlap_end = min(pd.to_datetime(event1[1]), pd.to_datetime(event2[1]), pd.to_datetime(event3[1]))
                if overlap_start <= overlap_end:
                    intersection_events.append((overlap_start, overlap_end))
                    break  # 确保每个事件只统计一次

    return intersection_events

# 合并和匹配函数
def match_and_calculate_e1_e3(swap_folder, spi_folder, spei_folder):
    # 初始化结果存储
    results = []

    # 遍历 SWAP 文件夹中的所有文件
    for swap_file in os.listdir(swap_folder):
        if swap_file.endswith(".csv"):
            # 提取站点 ID，例如 "station_50246" 从文件名中提取
            station_id = "_".join(swap_file.split("_")[:2])  # 提取前两个部分作为站点 ID

            # 找到对应的 SPI 和 SPEI 文件
            spi_file = next((f for f in os.listdir(spi_folder) if station_id in f), None)
            spei_file = next((f for f in os.listdir(spei_folder) if station_id in f), None)

            # 如果找不到对应文件，则跳过
            if not spi_file or not spei_file:
                print(f"无法找到站点 {station_id} 的 SPI 或 SPEI 文件，跳过...")
                continue

            # 构造文件路径
            swap_path = os.path.join(swap_folder, swap_file)
            spi_path = os.path.join(spi_folder, spi_file)
            spei_path = os.path.join(spei_folder, spei_file)

            # 读取数据
            swap_df = pd.read_csv(swap_path)
            spi_df = pd.read_csv(spi_path)
            spei_df = pd.read_csv(spei_path)

            # 创建完整日期列
            for df in [swap_df, spi_df, spei_df]:
                df['Full_Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-01')

            # 提取事件时间段
            swap_events = extract_events(swap_df)
            spi_events = extract_events(spi_df)
            spei_events = extract_events(spei_df)

            # 计算 E1（各指数独立探测的事件数）
            e1_swap = len(swap_events)
            e1_spi = len(spi_events)
            e1_spei = len(spei_events)

            # 计算 E3（三种指数同时探测的事件数）
            intersection_events = calculate_strict_intersection(swap_events, spi_events, spei_events)
            e3 = len(intersection_events)

            # 计算 E3/E1 比例
            e3_e1_swap = e3 / e1_swap if e1_swap > 0 else 0
            e3_e1_spi = e3 / e1_spi if e1_spi > 0 else 0
            e3_e1_spei = e3 / e1_spei if e1_spei > 0 else 0

            # 保存结果
            results.append({
                'Station': station_id,
                'E1_SWAP': e1_swap,
                'E1_SPI': e1_spi,
                'E1_SPEI': e1_spei,
                'E3': e3,
                'E3/E1_SWAP': e3_e1_swap,
                'E3/E1_SPI': e3_e1_spi,
                'E3/E1_SPEI': e3_e1_spei
            })

    # 转为 DataFrame 并返回
    return pd.DataFrame(results)

# 运行匹配和计算
result_df = match_and_calculate_e1_e3(swap_folder, spi_folder, spei_folder)

# 保存结果
output_path = r"D:\A-Projects\DWAA Project\E1_E3_Results.csv"
result_df.to_csv(output_path, index=False)
print(f"E1 和 E3 计算结果已保存到 {output_path}")