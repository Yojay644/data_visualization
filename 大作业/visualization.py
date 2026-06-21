# -*- coding: utf-8 -*-
"""
杭州亚运会社交媒体互动数据 - 可视化模块
=============================================
提供所有静态可视化图表生成函数，供 Jupyter Notebook 和 Streamlit 共同调用。
使用 matplotlib + seaborn 生成出版物质量的图表，支持中文字体。

注意：本模块不依赖 Streamlit，可独立运行。
"""

import matplotlib
matplotlib.use("Agg")  # 非交互式后端，支持服务器环境

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd
import os
from wordcloud import WordCloud
import jieba

# ============================================================
# 中文字体配置（兼容 Windows / macOS / Linux / Streamlit Cloud）
# ============================================================
# 删除旧字体缓存，确保字体列表最新
import glob as _glob
_cache_dir = os.path.join(os.path.expanduser("~"), ".matplotlib")
for _cache_file in _glob.glob(os.path.join(_cache_dir, "fontlist*.json")):
    try:
        os.remove(_cache_file)
    except Exception:
        pass

# 重新加载字体管理器
matplotlib.font_manager._load_fontmanager(try_read_cache=False)

# ── 获取系统中所有可用的字体列表 ──
_AVAILABLE_FONTS = {f.name for f in matplotlib.font_manager.fontManager.ttflist}

# ── 按优先级排序的中文字体名候选 ──
_CN_FONT_CANDIDATES = [
    # Windows
    "Microsoft YaHei", "SimHei", "KaiTi", "FangSong", "SimSun",
    # macOS
    "PingFang SC", "Heiti SC", "STHeiti", "STXihei",
    # Linux / Streamlit Cloud (fonts-noto-cjk)
    "Noto Sans CJK SC", "Noto Sans SC", "Noto Serif CJK SC",
    "Noto Sans CJK TC", "Noto Sans CJK JP",
    "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
    "AR PL UMing CN", "AR PL UKai CN",
]

_CN_FONT = None
_CN_FONT_PATH = None

# 第一轮：按候选名精确匹配
for _fname in _CN_FONT_CANDIDATES:
    if _fname in _AVAILABLE_FONTS:
        _CN_FONT = _fname
        _CN_FONT_PATH = matplotlib.font_manager.findfont(_fname, fallback_to_default=False)
        break

# 第二轮：如果精确匹配失败，扫描字体路径中包含 CJK/CN/SC 关键字的字体
if _CN_FONT is None:
    for _f in matplotlib.font_manager.fontManager.ttflist:
        _name_lower = _f.name.lower()
        if any(_kw in _name_lower for _kw in ["cjk", "noto sans", "wenquan", "hei", "ming", "song", "kai", "fang"]):
            try:
                _test_path = _f.fname
                if os.path.exists(_test_path):
                    _CN_FONT = _f.name
                    _CN_FONT_PATH = _test_path
                    break
            except Exception:
                continue

# 第三轮：兜底 — 自动下载开源中文字体（单个轻量字体文件）
if _CN_FONT is None:
    _FONT_DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".fonts")
    _FONT_DOWNLOAD_PATH = os.path.join(_FONT_DOWNLOAD_DIR, "NotoSansSC-Regular.ttf")

    if not os.path.exists(_FONT_DOWNLOAD_PATH):
        print("[可视化] 未找到系统中文字体，正在自动下载...")
        os.makedirs(_FONT_DOWNLOAD_DIR, exist_ok=True)
        try:
            from urllib.request import urlopen
            # 单个 Noto Sans SC Regular 字体文件（约 5MB）
            _FONT_URLS = [
                "https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
                "https://cdn.jsdelivr.net/gh/AimeeMao/Fonts@main/NotoSansSC-Regular.otf",
            ]
            for _url in _FONT_URLS:
                try:
                    _resp = urlopen(_url, timeout=30)
                    with open(_FONT_DOWNLOAD_PATH, "wb") as _ff:
                        _ff.write(_resp.read())
                    print(f"[可视化] 字体下载成功: {_FONT_DOWNLOAD_PATH}")
                    break
                except Exception:
                    continue

            if not os.path.exists(_FONT_DOWNLOAD_PATH):
                print("[可视化] 自动下载失败，请手动安装中文字体")
        except Exception as _e:
            print(f"[可视化] 字体下载失败: {_e}")

    # 注册下载的字体
    if os.path.exists(_FONT_DOWNLOAD_PATH):
        try:
            _fp = matplotlib.font_manager.FontProperties(fname=_FONT_DOWNLOAD_PATH)
            _CN_FONT = _fp.get_name()
            _CN_FONT_PATH = _FONT_DOWNLOAD_PATH
            matplotlib.font_manager.fontManager.addfont(_FONT_DOWNLOAD_PATH)
        except Exception:
            pass

# ── 应用字体配置 ──
if _CN_FONT:
    plt.rcParams["font.sans-serif"] = [_CN_FONT, "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    print(f"[可视化] 使用中文字体: {_CN_FONT}")
else:
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    print("[可视化] ⚠ 未找到中文字体，图表中文将无法正常显示。"
          "请安装中文字体或运行: pip install matplotlib --upgrade")

plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# Seaborn 样式（在字体设置之后，避免覆盖字体配置）
sns.set_style("whitegrid")
sns.set_palette("Set2")
# 再次确认字体配置未被覆盖
if _CN_FONT:
    plt.rcParams["font.sans-serif"] = [_CN_FONT, "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"

# 输出目录（在同一目录下）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 全局配色方案
COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8"]


def get_cn_font() -> str:
    """获取当前配置的中文字体名称"""
    return _CN_FONT


def _save_and_close(fig, filename: str, dpi: int = 150):
    """保存图表到 output/charts/ 并关闭"""
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ============================================================
# 1. 互动量分布直方图
# ============================================================
def plot_likes_histogram(df: pd.DataFrame, save: bool = True):
    """点赞数分布直方图（带KDE密度曲线）"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for ax, col, title, color in zip(
        axes,
        ["点赞数", "评论数", "转发数"],
        ["点赞数分布", "评论数分布", "转发数分布"],
        ["#FF6B6B", "#4ECDC4", "#45B7D1"],
    ):
        ax.hist(df[col], bins=25, color=color, alpha=0.7, edgecolor="white", density=True)
        # KDE 叠加
        try:
            sns.kdeplot(data=df, x=col, ax=ax, color="darkblue", linewidth=2)
        except Exception:
            pass
        ax.axvline(df[col].mean(), color="red", linestyle="--", linewidth=1.5, label=f"均值={df[col].mean():.0f}")
        ax.axvline(df[col].median(), color="orange", linestyle="--", linewidth=1.5, label=f"中位数={df[col].median():.0f}")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("数量")
        ax.set_ylabel("密度")
        ax.legend(fontsize=8)

    fig.suptitle("杭州亚运会微博互动量分布", fontsize=16, fontweight="bold")
    plt.tight_layout()
    if save:
        return _save_and_close(fig, "01_likes_histogram.png")
    return fig


# ============================================================
# 2. 地区互动量TOP10柱状图
# ============================================================
def plot_region_top10(region_agg: pd.DataFrame, save: bool = True):
    """各地区总互动量Top10柱状图"""
    top10 = region_agg.head(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(top10)))
    bars = ax.barh(top10.index[::-1], top10["总互动量"].values[::-1], color=colors[::-1], edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, top10["总互动量"].values[::-1]):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", va="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("总互动量（点赞+评论+转发）", fontsize=12)
    ax.set_title("各地区微博总互动量 Top 10", fontsize=15, fontweight="bold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.tight_layout()
    if save:
        return _save_and_close(fig, "02_region_top10.png")
    return fig


def plot_region_top_n(region_agg: pd.DataFrame, n: int = 10):
    """
    各地区总互动量 Top N 柱状图（供 Streamlit 交互式调用）。
    返回 matplotlib figure，不保存文件。
    """
    top_n = region_agg.head(n)
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(top_n)))
    bars = ax.barh(top_n.index[::-1], top_n["总互动量"].values[::-1],
                   color=colors[::-1], edgecolor="white")
    for bar, val in zip(bars, top_n["总互动量"].values[::-1]):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", va="center", fontsize=9, fontweight="bold")
    ax.set_xlabel("总互动量")
    ax.set_title(f"各地区总互动量 Top {n}", fontsize=13, fontweight="bold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.tight_layout()
    return fig


# ============================================================
# 3. 每日互动量趋势折线图
# ============================================================
def plot_daily_trend(date_agg: pd.DataFrame, save: bool = True):
    """每日互动量变化趋势（点赞/评论/转发三条折线）"""
    fig, ax1 = plt.subplots(figsize=(14, 6))

    x = range(len(date_agg))
    labels = [str(d) for d in date_agg.index]
    # 每5个标签显示一个避免拥挤
    tick_positions = list(range(0, len(labels), max(1, len(labels) // 8)))
    tick_labels = [labels[i] for i in tick_positions]

    ax1.plot(x, date_agg["总点赞"].values, "o-", color="#FF6B6B", linewidth=2, markersize=4, label="点赞数")
    ax1.plot(x, date_agg["总评论"].values, "s-", color="#4ECDC4", linewidth=2, markersize=4, label="评论数")
    ax1.plot(x, date_agg["总转发"].values, "^-", color="#45B7D1", linewidth=2, markersize=4, label="转发数")

    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=45, ha="right")
    ax1.set_ylabel("互动量", fontsize=12)
    ax1.set_title("杭州亚运会微博每日互动量变化趋势", fontsize=15, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=10)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()
    if save:
        return _save_and_close(fig, "03_daily_trend.png")
    return fig


# ============================================================
# 4. 小时活跃度分布
# ============================================================
def plot_hourly_activity(hour_agg: pd.DataFrame, save: bool = True):
    """24小时发布活跃度分布（柱状图+折线）"""
    fig, ax1 = plt.subplots(figsize=(12, 6))

    hours = hour_agg.index.tolist()
    bar_colors = ["#FFD93D" if 6 <= h < 22 else "#6C5B7B" for h in hours]  # 白天金黄色，夜晚暗紫色

    bars = ax1.bar(hours, hour_agg["微博数量"].values, color=bar_colors, alpha=0.8, edgecolor="white", label="微博数量")
    ax1.set_xlabel("小时", fontsize=12)
    ax1.set_ylabel("微博数量", fontsize=12, color="#FF6B6B")
    ax1.tick_params(axis="y", labelcolor="#FF6B6B")

    ax2 = ax1.twinx()
    ax2.plot(hours, hour_agg["总互动量"].values, "o-", color="#45B7D1", linewidth=2.5, markersize=6, label="总互动量")
    ax2.set_ylabel("总互动量", fontsize=12, color="#45B7D1")
    ax2.tick_params(axis="y", labelcolor="#45B7D1")

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.set_title("24小时微博发布活跃度分布", fontsize=15, fontweight="bold")
    ax1.set_xticks(range(0, 24))
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))

    plt.tight_layout()
    if save:
        return _save_and_close(fig, "04_hourly_activity.png")
    return fig


# ============================================================
# 5. 相关性热力图
# ============================================================
def plot_correlation_heatmap(corr_df: pd.DataFrame, save: bool = True):
    """点赞数、评论数、转发数之间的相关性热力图"""
    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr_df, dtype=bool))
    sns.heatmap(
        corr_df,
        annot=True,
        fmt=".3f",
        cmap="RdBu_r",
        center=0,
        mask=mask,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
        ax=ax,
        annot_kws={"fontsize": 13, "fontweight": "bold"},
    )
    ax.set_title("微博互动指标相关性热力图", fontsize=15, fontweight="bold", pad=20)
    plt.tight_layout()
    if save:
        return _save_and_close(fig, "05_correlation_heatmap.png")
    return fig


# ============================================================
# 6. 互动量散点图 (点赞 vs 评论)
# ============================================================
def plot_scatter_likes_comments(df: pd.DataFrame, save: bool = True):
    """点赞数 vs 评论数散点图（带回归线和边际直方图）"""
    fig = plt.figure(figsize=(10, 8))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    ax_main = fig.add_subplot(gs[1:, :2])
    ax_top = fig.add_subplot(gs[0, :2], sharex=ax_main)
    ax_right = fig.add_subplot(gs[1:, 2], sharey=ax_main)

    # 主散点图
    ax_main.scatter(df["点赞数"], df["评论数"], alpha=0.5, s=20, c="#4ECDC4", edgecolors="white", linewidth=0.3)
    # 回归线
    try:
        from numpy.polynomial.polynomial import polyfit
        b, m = polyfit(df["点赞数"], df["评论数"], 1)
        x_line = np.linspace(df["点赞数"].min(), df["点赞数"].max(), 100)
        ax_main.plot(x_line, b + m * x_line, "r--", linewidth=1.5, label=f"y={m:.4f}x+{b:.1f}")
    except Exception:
        pass
    ax_main.set_xlabel("点赞数", fontsize=12)
    ax_main.set_ylabel("评论数", fontsize=12)
    ax_main.legend(fontsize=9)

    # 顶部直方图（点赞数）
    ax_top.hist(df["点赞数"], bins=30, color="#FF6B6B", alpha=0.6, edgecolor="white")
    ax_top.set_ylabel("频数", fontsize=9)
    ax_top.tick_params(labelbottom=False)

    # 右侧直方图（评论数）
    ax_right.hist(df["评论数"], bins=30, orientation="horizontal", color="#45B7D1", alpha=0.6, edgecolor="white")
    ax_right.set_xlabel("频数", fontsize=9)
    ax_right.tick_params(labelleft=False)

    fig.suptitle("点赞数与评论数关系散点图", fontsize=15, fontweight="bold")
    if save:
        return _save_and_close(fig, "06_scatter_likes_comments.png")
    return fig


# ============================================================
# 7. 话题词云图
# ============================================================
def plot_wordcloud(df: pd.DataFrame, save: bool = True):
    """基于微博文本生成词云图"""
    # 合并所有微博文本
    text = " ".join(df["微博文本"].dropna().tolist())
    if not text.strip():
        text = "杭州亚运会 社交媒体 互动数据"

    # 中文分词
    words = jieba.cut(text)
    # 过滤停用词和短词
    stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
                 "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
                 "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "怎么", "吗", "啊",
                 "呢", "吧", "哦", "嗯", "哈", "呀", "哇", "啦", "噢", "呗", "么", "过", "对",
                 "让", "把", "被", "从", "以", "及", "与", "或", "但", "而", "且", "因", "为",
                 "所", "可以", "还是", "已经", "这个", "那个", "这样", "那样", "一些", "一下"}
    filtered = [w for w in words if len(w) > 1 and w not in stopwords]
    filtered_text = " ".join(filtered)

    if not filtered_text.strip():
        filtered_text = "杭州 亚运会 社交媒体 互动 数据 分析"

    # 查找中文字体路径用于词云（优先复用全局已找到的字体路径）
    _wc_font_path = _CN_FONT_PATH if _CN_FONT_PATH and os.path.exists(_CN_FONT_PATH) else None
    if _wc_font_path is None:
        for _fname in ["SimHei", "Microsoft YaHei", "STXihei", "Noto Sans SC", "Noto Sans CJK SC", "WenQuanYi Micro Hei"]:
            try:
                _p = matplotlib.font_manager.findfont(_fname, fallback_to_default=False)
                if _p and os.path.exists(_p) and _p != matplotlib.font_manager.findfont("DejaVu Sans"):
                    _wc_font_path = _p
                    break
            except Exception:
                continue
    # 兜底：扫描字体目录
    if _wc_font_path is None:
        for _f in matplotlib.font_manager.fontManager.ttflist:
            _n = _f.name.lower()
            if any(_kw in _n for _kw in ["cjk", "noto", "hei", "song", "kai", "ming", "wenquan"]):
                _wc_font_path = _f.fname
                break

    # 生成词云
    wc = WordCloud(
        font_path=_wc_font_path,  # 指定中文字体
        width=1000,
        height=600,
        background_color="white",
        max_words=100,
        colormap="Reds",
        contour_width=1,
        contour_color="steelblue",
        collocations=False,
    ).generate(filtered_text)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("杭州亚运会微博高频词云图", fontsize=18, fontweight="bold", pad=20)
    plt.tight_layout()
    if save:
        return _save_and_close(fig, "07_wordcloud.png")
    return fig


# ============================================================
# 8. 话题热度Top10
# ============================================================
def plot_hashtag_top10(tag_agg: pd.DataFrame, save: bool = True):
    """话题标签热度Top10横向柱状图"""
    if tag_agg.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "暂无话题数据", ha="center", va="center", fontsize=16, transform=ax.transAxes)
        ax.axis("off")
        if save:
            return _save_and_close(fig, "08_hashtag_top10.png")
        return fig

    top10 = tag_agg.head(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Oranges(np.linspace(0.3, 0.95, len(top10)))
    bars = ax.barh(top10.index[::-1], top10["总互动量"].values[::-1], color=colors[::-1], edgecolor="white")

    for bar, val in zip(bars, top10["总互动量"].values[::-1]):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", va="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("总互动量", fontsize=12)
    ax.set_title("热门话题标签 Top 10", fontsize=15, fontweight="bold")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.tight_layout()
    if save:
        return _save_and_close(fig, "08_hashtag_top10.png")
    return fig


# ============================================================
# 9. 互动量指标箱线图
# ============================================================
def plot_boxplot(df: pd.DataFrame, save: bool = True):
    """点赞数、评论数、转发数的箱线图（去除极端值）"""
    fig, ax = plt.subplots(figsize=(10, 6))
    data_to_plot = [df["点赞数"].values, df["评论数"].values, df["转发数"].values]
    bp = ax.boxplot(data_to_plot, patch_artist=True, widths=0.5,
                    showfliers=True,  # 显示离群值
                    medianprops={"color": "red", "linewidth": 2})
    ax.set_xticklabels(["点赞数", "评论数", "转发数"])

    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax.set_ylabel("互动量", fontsize=12)
    ax.set_title("互动量指标箱线图分析", fontsize=15, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    if save:
        return _save_and_close(fig, "09_boxplot.png")
    return fig


# ============================================================
# 10. 互动量占比饼图
# ============================================================
def plot_interaction_pie(df: pd.DataFrame, save: bool = True):
    """点赞/评论/转发占比环形图"""
    totals = [df["点赞数"].sum(), df["评论数"].sum(), df["转发数"].sum()]
    labels = ["点赞数", "评论数", "转发数"]
    colors_pie = ["#FF6B6B", "#4ECDC4", "#45B7D1"]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        totals,
        labels=labels,
        colors=colors_pie,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"width": 0.4, "edgecolor": "white", "linewidth": 2},
        textprops={"fontsize": 13},
    )
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_fontsize(12)
    ax.set_title("微博互动类型占比（环形图）", fontsize=15, fontweight="bold", pad=20)
    if save:
        return _save_and_close(fig, "10_interaction_pie.png")
    return fig


# ============================================================
# 批量生成所有图表
# ============================================================
def generate_all_charts(df: pd.DataFrame, region_agg: pd.DataFrame,
                        date_agg: pd.DataFrame, hour_agg: pd.DataFrame,
                        tag_agg: pd.DataFrame, corr_df: pd.DataFrame) -> list:
    """批量生成所有图表，返回保存路径列表"""
    paths = []
    print("生成可视化图表...")

    print("  [1/10] 互动量分布直方图")
    paths.append(plot_likes_histogram(df))

    print("  [2/10] 地区Top10柱状图")
    paths.append(plot_region_top10(region_agg))

    print("  [3/10] 每日趋势折线图")
    paths.append(plot_daily_trend(date_agg))

    print("  [4/10] 小时活跃度分布")
    paths.append(plot_hourly_activity(hour_agg))

    print("  [5/10] 相关性热力图")
    paths.append(plot_correlation_heatmap(corr_df))

    print("  [6/10] 点赞vs评论散点图")
    paths.append(plot_scatter_likes_comments(df))

    print("  [7/10] 词云图")
    paths.append(plot_wordcloud(df))

    print("  [8/10] 话题热度Top10")
    paths.append(plot_hashtag_top10(tag_agg))

    print("  [9/10] 箱线图")
    paths.append(plot_boxplot(df))

    print("  [10/10] 互动占比环形图")
    paths.append(plot_interaction_pie(df))

    print(f"\n[完成] 所有图表已保存至: {OUTPUT_DIR}")
    return paths


if __name__ == "__main__":
    import data_processing
    df, stats = data_processing.run_pipeline()
    generate_all_charts(
        df,
        data_processing.aggregate_by_region(df),
        data_processing.aggregate_by_date(df),
        data_processing.aggregate_by_hour(df),
        data_processing.aggregate_by_hashtag(df),
        data_processing.compute_correlation(df),
    )
