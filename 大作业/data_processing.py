# -*- coding: utf-8 -*-
"""
杭州亚运会社交媒体互动数据 - 数据处理与分析模块
=====================================================
功能：
  1. 加载原始Excel数据
  2. 数据清洗与预处理（缺失值、异常值、类型转换）
  3. 基础统计描述
  4. 数据聚合分析（按地区、时间、话题等维度）
  5. 导出处理后的数据供可视化和Streamlit使用

注意：本模块不依赖 Streamlit，可独立运行。
"""

import pandas as pd
import numpy as np
import os
import jieba
from collections import Counter

# ============================================================
# 全局路径配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据文件和输出目录均在同一目录下
RAW_DATA_PATH = os.path.join(BASE_DIR, "原始数据.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    加载原始Excel数据，统一列名为中文。
    原始列名因编码问题显示为乱码，根据已知列顺序按位置重命名。
    已知列顺序: 微博文本, 发布时间, 发布地区, 点赞数, 评论数, 转发数, 话题标签, 用户ID
    """
    df = pd.read_excel(filepath)
    # 按位置重命名（原始数据固定8列，顺序确定）
    target_names = ["微博文本", "发布时间", "发布地区", "点赞数", "评论数", "转发数", "话题标签", "用户ID"]
    if len(df.columns) == len(target_names):
        df.columns = target_names
    else:
        # 兜底：列数不匹配时按关键字映射
        print(f"  ⚠ 列数({len(df.columns)})与预期(8)不符，尝试关键字映射...")
        column_mapping = {}
        for col in df.columns:
            col_str = str(col)
            if "文本" in col_str or "text" in col_str.lower():
                column_mapping[col] = "微博文本"
            elif "时间" in col_str or "date" in col_str.lower() or "time" in col_str.lower():
                column_mapping[col] = "发布时间"
            elif "地区" in col_str or "region" in col_str.lower():
                column_mapping[col] = "发布地区"
            elif "赞" in col_str or "like" in col_str.lower():
                column_mapping[col] = "点赞数"
            elif "评论" in col_str or "comment" in col_str.lower():
                column_mapping[col] = "评论数"
            elif "转发" in col_str or "repost" in col_str.lower():
                column_mapping[col] = "转发数"
            elif "话题" in col_str or "标签" in col_str or "tag" in col_str.lower():
                column_mapping[col] = "话题标签"
            elif "用户" in col_str or "user" in col_str.lower() or "id" in col_str.lower():
                column_mapping[col] = "用户ID"
        if column_mapping:
            df.rename(columns=column_mapping, inplace=True)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    数据清洗：
    - 转换发布时间为datetime类型
    - 提取日期、小时等衍生字段
    - 处理缺失值
    - 过滤异常值（互动量为负的记录）
    """
    df = df.copy()

    # 1. 发布时间转换
    df["发布时间"] = pd.to_datetime(df["发布时间"], errors="coerce")
    df["发布日期"] = df["发布时间"].dt.date
    df["发布小时"] = df["发布时间"].dt.hour
    df["发布月份"] = df["发布时间"].dt.month

    # 2. 数值列类型确认与异常值过滤
    numeric_cols = ["点赞数", "评论数", "转发数"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        df = df[df[col] >= 0]

    # 3. 计算总互动量
    df["总互动量"] = df["点赞数"] + df["评论数"] + df["转发数"]

    # 4. 文本列清洗
    if "微博文本" in df.columns:
        df["微博文本"] = df["微博文本"].fillna("").astype(str)
    if "发布地区" in df.columns:
        df["发布地区"] = df["发布地区"].fillna("未知").astype(str).str.strip()
    if "话题标签" in df.columns:
        df["话题标签"] = df["话题标签"].fillna("").astype(str).str.strip()
    if "用户ID" in df.columns:
        df["用户ID"] = df["用户ID"].fillna("未知").astype(str).str.strip()

    return df


def load_and_preprocess(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    一步完成加载+清洗，返回干净数据的DataFrame。
    这是供Streamlit app调用的便捷函数。
    """
    df_raw = load_data(filepath)
    df_clean = clean_data(df_raw)
    return df_clean


def compute_statistics(df: pd.DataFrame) -> dict:
    """
    计算基础统计指标，返回字典格式便于展示。
    """
    stats = {}
    numeric_cols = ["点赞数", "评论数", "转发数", "总互动量"]

    for col in numeric_cols:
        if col in df.columns:
            stats[col] = {
                "均值": round(df[col].mean(), 2),
                "中位数": float(df[col].median()),
                "标准差": round(df[col].std(), 2),
                "最小值": int(df[col].min()),
                "最大值": int(df[col].max()),
                "25%分位": round(df[col].quantile(0.25), 2),
                "75%分位": round(df[col].quantile(0.75), 2),
                "总和": int(df[col].sum()),
            }

    # 文本类统计
    if "发布地区" in df.columns:
        stats["地区数量"] = df["发布地区"].nunique()
    if "用户ID" in df.columns:
        stats["用户数量"] = df["用户ID"].nunique()
    stats["记录总数"] = len(df)
    if "发布时间" in df.columns:
        stats["时间范围"] = {
            "最早": str(df["发布时间"].min()),
            "最晚": str(df["发布时间"].max()),
        }

    return stats


def aggregate_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """按发布地区聚合统计"""
    agg = df.groupby("发布地区").agg(
        微博数量=("微博文本", "count"),
        平均点赞=("点赞数", "mean"),
        平均评论=("评论数", "mean"),
        平均转发=("转发数", "mean"),
        总互动量=("总互动量", "sum"),
    ).sort_values("总互动量", ascending=False)
    return agg.round(2)


def aggregate_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """按发布日期聚合统计"""
    agg = df.groupby("发布日期").agg(
        微博数量=("微博文本", "count"),
        总点赞=("点赞数", "sum"),
        总评论=("评论数", "sum"),
        总转发=("转发数", "sum"),
        总互动量=("总互动量", "sum"),
        平均点赞=("点赞数", "mean"),
        平均评论=("评论数", "mean"),
        平均转发=("转发数", "mean"),
    ).sort_index()
    return agg.round(2)


def aggregate_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """按小时聚合统计（分析发布活跃时段）"""
    agg = df.groupby("发布小时").agg(
        微博数量=("微博文本", "count"),
        总互动量=("总互动量", "sum"),
        平均互动量=("总互动量", "mean"),
    ).sort_index()
    return agg.round(2)


def aggregate_by_hashtag(df: pd.DataFrame) -> pd.DataFrame:
    """解析话题标签并按话题聚合统计"""
    records = []
    for _, row in df.iterrows():
        tags = row.get("话题标签", "")
        if not tags or pd.isna(tags):
            continue
        # 按 # 分割提取话题
        for tag in tags.split("#"):
            tag = tag.strip()
            if tag and tag != "#":
                records.append({
                    "话题": f"#{tag}",
                    "点赞数": row["点赞数"],
                    "评论数": row["评论数"],
                    "转发数": row["转发数"],
                    "总互动量": row["总互动量"],
                })

    if not records:
        return pd.DataFrame()

    tag_df = pd.DataFrame(records)
    agg = tag_df.groupby("话题").agg(
        出现次数=("总互动量", "count"),
        总互动量=("总互动量", "sum"),
        平均点赞=("点赞数", "mean"),
        平均评论=("评论数", "mean"),
        平均转发=("转发数", "mean"),
    ).sort_values("总互动量", ascending=False)
    return agg.round(2)


def compute_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """计算互动量指标的相关性矩阵"""
    corr_cols = ["点赞数", "评论数", "转发数", "总互动量"]
    available = [c for c in corr_cols if c in df.columns]
    return df[available].corr().round(4)


def top_n_posts(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """获取互动量最高的N条微博"""
    return df.nlargest(n, "总互动量")[
        ["微博文本", "发布时间", "发布地区", "点赞数", "评论数", "转发数", "总互动量", "话题标签"]
    ]


def compute_word_frequency(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    对微博文本进行 Jieba 分词并统计高频词。
    返回 DataFrame，包含"词语"和"频次"两列。
    """
    text_content = " ".join(df["微博文本"].dropna().tolist())
    if not text_content.strip():
        return pd.DataFrame(columns=["词语", "频次"])

    words = jieba.cut(text_content)
    stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
                 "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
                 "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
                 "什么", "怎么", "吗", "啊", "呢", "吧", "哦", "嗯", "哈", "呀", "哇",
                 "啦", "噢", "呗", "么", "过", "对", "让", "把", "被", "从", "以",
                 "及", "与", "或", "但", "而", "且", "因", "为", "所", "可以", "还是",
                 "已经", "这个", "那个", "这样", "那样", "一些", "一下"}
    filtered_words = [w for w in words if len(w) > 1 and w not in stopwords]

    if not filtered_words:
        return pd.DataFrame(columns=["词语", "频次"])

    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(top_n)
    return pd.DataFrame(top_words, columns=["词语", "频次"])


# ============================================================
# 主流程：运行所有数据处理步骤并保存结果
# ============================================================
def run_pipeline():
    print("=" * 60)
    print("杭州亚运会社交媒体互动数据 - 数据处理流水线")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1/6] 加载原始数据...")
    df_raw = load_data()
    print(f"  → 原始数据: {df_raw.shape[0]} 行, {df_raw.shape[1]} 列")

    # 2. 清洗数据
    print("\n[2/6] 数据清洗与预处理...")
    df = clean_data(df_raw)
    print(f"  → 清洗后: {df.shape[0]} 行, {df.shape[1]} 列")
    print(f"  → 日期范围: {df['发布时间'].min()} ~ {df['发布时间'].max()}")

    # 3. 基础统计
    print("\n[3/6] 计算基础统计指标...")
    stats = compute_statistics(df)
    for k, v in stats.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for sk, sv in v.items():
                print(f"    {sk}: {sv}")
        else:
            print(f"  {k}: {v}")

    # 4. 多维聚合
    print("\n[4/6] 多维聚合分析...")
    region_agg = aggregate_by_region(df)
    date_agg = aggregate_by_date(df)
    hour_agg = aggregate_by_hour(df)
    tag_agg = aggregate_by_hashtag(df)
    print(f"  → 地区维度: {len(region_agg)} 个地区")
    print(f"  → 日期维度: {len(date_agg)} 天")
    print(f"  → 话题维度: {len(tag_agg)} 个话题")

    # 5. 相关性分析
    print("\n[5/6] 相关性分析...")
    corr = compute_correlation(df)
    print(corr.to_string())

    # 6. 保存输出
    print("\n[6/6] 保存处理结果...")
    df.to_csv(os.path.join(OUTPUT_DIR, "cleaned_data.csv"), index=False, encoding="utf-8-sig")
    region_agg.to_csv(os.path.join(OUTPUT_DIR, "region_aggregation.csv"), encoding="utf-8-sig")
    date_agg.to_csv(os.path.join(OUTPUT_DIR, "date_aggregation.csv"), encoding="utf-8-sig")
    hour_agg.to_csv(os.path.join(OUTPUT_DIR, "hour_aggregation.csv"), encoding="utf-8-sig")
    if not tag_agg.empty:
        tag_agg.to_csv(os.path.join(OUTPUT_DIR, "hashtag_aggregation.csv"), encoding="utf-8-sig")
    corr.to_csv(os.path.join(OUTPUT_DIR, "correlation.csv"), encoding="utf-8-sig")
    print(f"  → 所有结果已保存至: {OUTPUT_DIR}")
    print("\n[完成] 数据处理流水线完成!")
    return df, stats


if __name__ == "__main__":
    run_pipeline()
