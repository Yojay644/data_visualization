# -*- coding: utf-8 -*-
"""
杭州亚运会社交媒体互动数据 - Streamlit 交互式仪表板
=========================================================
本模块只包含 Streamlit 及其相关库的调用（UI 布局、交互控件、数据展示）。
所有数据处理委托给 data_processing 模块，所有图表生成委托给 visualization 模块。

运行方式: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os

# ============================================================
# 导入项目模块（数据处理和可视化，均不依赖 Streamlit）
# ============================================================
import data_processing as dp
import visualization as viz

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="杭州亚运会社交媒体互动数据分析",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 数据加载与预处理（带缓存，委托给 data_processing 模块）
# ============================================================
@st.cache_data
def load_data():
    """加载并预处理原始数据"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RAW_DATA_PATH = os.path.join(BASE_DIR, "原始数据.xlsx")

    if not os.path.exists(RAW_DATA_PATH):
        st.error(f"❌ 找不到数据文件: {RAW_DATA_PATH}")
        st.stop()

    return dp.load_and_preprocess(RAW_DATA_PATH)


df = load_data()

# ============================================================
# 侧边栏 —— 全局筛选器
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/olympic-medal.png", width=64)
    st.title("🏅 控制面板")
    st.markdown("---")

    # 日期范围筛选
    st.subheader("📅 日期筛选")
    date_min = df["发布时间"].min().date()
    date_max = df["发布时间"].max().date()
    date_range = st.date_input(
        "选择日期范围",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    # 地区筛选
    st.subheader("📍 地区筛选")
    all_regions = sorted(df["发布地区"].unique().tolist())
    selected_regions = st.multiselect(
        "选择地区（可多选）",
        options=all_regions,
        default=all_regions[:5] if len(all_regions) > 5 else all_regions,
        help="选择要分析的地区，留空表示全选",
    )

    # 互动量阈值筛选
    st.subheader("🔢 互动量阈值")
    interaction_min = st.slider(
        "最小总互动量",
        min_value=0,
        max_value=int(df["总互动量"].max()),
        value=0,
        step=500,
    )

    # 话题筛选
    st.subheader("🏷️ 话题筛选")
    all_tags = set()
    for tags_str in df["话题标签"].dropna():
        for t in tags_str.split("#"):
            t = t.strip()
            if t:
                all_tags.add(f"#{t}")
    all_tags = sorted(all_tags)
    selected_tags = st.multiselect(
        "选择话题标签",
        options=all_tags if len(all_tags) <= 20 else list(all_tags)[:20],
        default=[],
        help="筛选包含指定话题的微博",
    )

    st.markdown("---")
    st.caption(f"📊 数据集: {len(df)} 条记录")
    st.caption(f"📅 时间范围: {date_min} ~ {date_max}")
    st.caption(f"👥 用户数: {df['用户ID'].nunique()}")
    st.caption(f"📍 地区数: {df['发布地区'].nunique()}")

# ============================================================
# 根据筛选条件过滤数据
# ============================================================
filtered_df = df.copy()

if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["发布时间"].dt.date >= date_range[0]) &
        (filtered_df["发布时间"].dt.date <= date_range[1])
    ]

if selected_regions:
    filtered_df = filtered_df[filtered_df["发布地区"].isin(selected_regions)]

filtered_df = filtered_df[filtered_df["总互动量"] >= interaction_min]

if selected_tags:
    tag_mask = filtered_df["话题标签"].apply(
        lambda x: any(tag in str(x) for tag in selected_tags)
    )
    filtered_df = filtered_df[tag_mask]

# ============================================================
# 页面标题
# ============================================================
st.title("🏅 杭州亚运会社交媒体互动数据分析")
st.markdown("---")

# ============================================================
# 顶部 KPI 指标卡片
# ============================================================
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📝 微博总数", f"{len(filtered_df):,}")
with col2:
    st.metric("👍 平均点赞", f"{filtered_df['点赞数'].mean():,.0f}")
with col3:
    st.metric("💬 平均评论", f"{filtered_df['评论数'].mean():,.0f}")
with col4:
    st.metric("🔄 平均转发", f"{filtered_df['转发数'].mean():,.0f}")
with col5:
    st.metric("🔥 总互动量", f"{filtered_df['总互动量'].sum():,}")

st.markdown("---")

# ============================================================
# Tab 布局
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 数据概览",
    "🔥 互动量分析",
    "📈 时间趋势",
    "🏷️ 内容分析",
    "📥 数据导出",
])

# ============================================================
# Tab 1: 数据概览
# ============================================================
with tab1:
    st.subheader("📋 原始数据预览")
    cols_to_show = [c for c in ["微博文本", "发布时间", "发布地区", "点赞数", "评论数", "转发数", "话题标签", "用户ID"]
                    if c in filtered_df.columns]
    st.dataframe(
        filtered_df[cols_to_show].head(100),
        use_container_width=True,
        height=400,
    )

    st.markdown("---")
    st.subheader("📊 统计摘要")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**数值列统计描述**")
        numeric_cols = [c for c in ["点赞数", "评论数", "转发数", "总互动量"] if c in filtered_df.columns]
        st.dataframe(filtered_df[numeric_cols].describe().round(2), use_container_width=True)

    with col_b:
        st.write("**分类列统计**")
        cat_stats = {
            "字段": ["发布地区", "话题标签(非空)", "用户ID"],
            "唯一值数": [
                filtered_df["发布地区"].nunique() if "发布地区" in filtered_df.columns else 0,
                filtered_df[filtered_df["话题标签"].notna() & (filtered_df["话题标签"] != "")].shape[0],
                filtered_df["用户ID"].nunique() if "用户ID" in filtered_df.columns else 0,
            ],
        }
        st.dataframe(pd.DataFrame(cat_stats), use_container_width=True, hide_index=True)

    # 互动量分布图 → visualization 模块
    st.markdown("---")
    st.subheader("📊 互动量分布")
    st.pyplot(viz.plot_likes_histogram(filtered_df, save=False))

# ============================================================
# Tab 2: 互动量分析
# ============================================================
with tab2:
    st.subheader("📍 各地区互动量对比")

    # 数据聚合 → data_processing 模块
    region_agg = dp.aggregate_by_region(filtered_df)

    col_top, col_chart = st.columns([1, 2])
    with col_top:
        n_top = st.slider("显示Top N地区", min_value=5, max_value=min(20, len(region_agg)), value=10)
        st.dataframe(region_agg.head(n_top).round(0).astype(int), use_container_width=True)

    with col_chart:
        # 图表 → visualization 模块
        st.pyplot(viz.plot_region_top_n(region_agg, n_top))

    st.markdown("---")
    st.subheader("📦 互动量箱线图")
    st.pyplot(viz.plot_boxplot(filtered_df, save=False))

    # 互动量占比
    st.markdown("---")
    st.subheader("🥧 互动类型占比")
    col_pie1, col_pie2 = st.columns([1, 1])
    with col_pie1:
        st.pyplot(viz.plot_interaction_pie(filtered_df, save=False))
    with col_pie2:
        st.write("**互动类型统计**")
        totals_pie = [filtered_df["点赞数"].sum(), filtered_df["评论数"].sum(), filtered_df["转发数"].sum()]
        pie_stats = pd.DataFrame({
            "类型": ["点赞数", "评论数", "转发数"],
            "总数": totals_pie,
            "占比": [f"{t / sum(totals_pie) * 100:.1f}%" for t in totals_pie],
        })
        st.dataframe(pie_stats, use_container_width=True, hide_index=True)

# ============================================================
# Tab 3: 时间趋势
# ============================================================
with tab3:
    st.subheader("📈 每日互动量变化趋势")
    daily = dp.aggregate_by_date(filtered_df)
    st.pyplot(viz.plot_daily_trend(daily, save=False))

    st.markdown("---")
    st.subheader("🕐 24小时发布活跃度")
    hourly = dp.aggregate_by_hour(filtered_df).reindex(range(24), fill_value=0)
    st.pyplot(viz.plot_hourly_activity(hourly, save=False))

# ============================================================
# Tab 4: 内容分析
# ============================================================
with tab4:
    st.subheader("☁️ 微博内容词云")

    col_wc1, col_wc2 = st.columns([2, 1])
    with col_wc1:
        st.pyplot(viz.plot_wordcloud(filtered_df, save=False))

    with col_wc2:
        st.write("**词频统计 Top 20**")
        word_df = dp.compute_word_frequency(filtered_df, top_n=20)
        if not word_df.empty:
            st.dataframe(word_df, use_container_width=True, hide_index=True)
        else:
            st.info("当前筛选条件下文本内容不足，无法生成词频统计")

    # 话题标签分析
    st.markdown("---")
    st.subheader("🏷️ 热门话题标签分析")
    tag_agg = dp.aggregate_by_hashtag(filtered_df)

    if not tag_agg.empty:
        col_tag1, col_tag2 = st.columns([1, 1])
        with col_tag1:
            st.dataframe(tag_agg.head(10).round(0).astype(int), use_container_width=True)
        with col_tag2:
            st.pyplot(viz.plot_hashtag_top10(tag_agg, save=False))
    else:
        st.info("当前筛选条件下没有话题标签数据")

# ============================================================
# Tab 5: 数据导出 & 相关性
# ============================================================
with tab5:
    st.subheader("🔗 互动指标相关性分析")

    col_corr1, col_corr2 = st.columns([1, 1])
    with col_corr1:
        corr_matrix = dp.compute_correlation(filtered_df)
        st.dataframe(corr_matrix.round(4), use_container_width=True)

    with col_corr2:
        st.pyplot(viz.plot_correlation_heatmap(corr_matrix, save=False))

    # 点赞 vs 评论散点图
    st.markdown("---")
    st.subheader("📌 点赞数与评论数关系散点图")
    st.pyplot(viz.plot_scatter_likes_comments(filtered_df, save=False))

    # 数据下载
    st.markdown("---")
    st.subheader("📥 数据导出")
    csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇️ 下载当前筛选后的数据 (CSV格式)",
        data=csv_data,
        file_name="杭州亚运会社交媒体数据_筛选结果.csv",
        mime="text/csv",
    )

    # 热门微博
    st.markdown("---")
    st.subheader("🔥 互动量最高的微博 Top 10")
    top_posts = dp.top_n_posts(filtered_df, 10)
    cols_show = [c for c in ["微博文本", "发布时间", "发布地区", "点赞数", "评论数", "转发数", "总互动量"]
                 if c in top_posts.columns]
    st.dataframe(top_posts[cols_show], use_container_width=True)

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #999; font-size: 13px;'>"
    "🏅 杭州亚运会社交媒体互动数据分析平台 | 计算机应用大作业 | Powered by Streamlit<br>"
    "数据来源：杭州亚运会社交媒体互动数据 | 数据集 280 条记录"
    "</div>",
    unsafe_allow_html=True,
)
