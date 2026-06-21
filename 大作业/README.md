# 🏅 杭州亚运会社交媒体互动数据分析

基于 **Streamlit** 构建的交互式数据可视化分析平台，对杭州亚运会相关微博的互动数据（点赞、评论、转发）进行全面分析和可视化展示。

## 📁 项目结构

```
├── app.py                 # Streamlit 交互式仪表板（仅包含 Web/UI 逻辑）
├── data_processing.py     # 数据处理与清洗模块（不依赖 Streamlit）
├── visualization.py       # 静态可视化图表生成模块（不依赖 Streamlit）
├── 原始数据.xlsx          # 原始数据集（280条微博记录）
├── output/                # 输出目录（运行后生成，已加入 .gitignore）
│   ├── cleaned_data.csv
│   ├── *_aggregation.csv
│   ├── correlation.csv
│   └── charts/            # 生成的 10 张 PNG 图表
├── requirements.txt       # Python 依赖清单
├── .gitignore             # Git 忽略规则
├── README.md
└── 论文.docx              # 大作业论文
```

### 模块职责分离

| 模块 | 依赖 | 职责 |
|------|------|------|
| `data_processing.py` | Pandas, NumPy | 数据加载、清洗、聚合、统计、导出 CSV |
| `visualization.py` | Matplotlib, Seaborn, Jieba, WordCloud | 静态图表生成（10 种图表），保存 PNG |
| `app.py` | **Streamlit** + 上述两个模块 | Web 仪表板：UI 布局、交互筛选、图表展示、数据下载 |

## 📊 数据集说明

数据集包含杭州亚运会期间社交媒体（微博）的互动数据，共 **280 条记录**，包含以下字段：

| 字段 | 说明 |
|------|------|
| 微博文本 | 微博正文内容 |
| 发布时间 | 微博发布时间戳 |
| 发布地区 | 用户所在地区 |
| 点赞数 | 点赞数量 |
| 评论数 | 评论数量 |
| 转发数 | 转发数量 |
| 话题标签 | 微博关联的话题标签 |
| 用户ID | 发帖用户标识 |

衍生字段：**总互动量** = 点赞数 + 评论数 + 转发数

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 推荐使用虚拟环境

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行交互式仪表板

```bash
streamlit run app.py
```

启动后在浏览器访问 `http://localhost:8501` 即可查看交互式仪表板。

### 运行数据处理流水线

```bash
python data_processing.py
```

执行后会完成数据加载、清洗、统计分析和多维聚合，并将结果保存到 `output/` 目录。

### 生成静态可视化图表

```bash
python visualization.py
```

执行后会生成 10 张出版物质量的图表，保存到 `output/charts/` 目录。

## ✨ 功能模块

### 📊 数据概览
- 原始数据表格预览（前100条）
- 数值列统计描述（均值、标准差、分位数等）
- 分类列统计（地区数、用户数）
- 互动量分布直方图（点赞/评论/转发）

### 🔥 互动量分析
- 各地区互动量对比（Top N 横向柱状图）
- 互动量指标箱线图分析
- 点赞/评论/转发类型占比环形图

### 📈 时间趋势
- 每日互动量变化趋势折线图
- 24小时微博发布活跃度分布（双Y轴图表）

### 🏷️ 内容分析
- 微博文本高频词云图（基于 Jieba 分词）
- 热门话题标签 Top 10 分析

### 🔗 相关性分析
- 互动指标相关性热力图
- 点赞数 vs 评论数散点图（含回归线）

### 📥 数据导出
- 按筛选条件导出 CSV 格式数据
- 互动量最高微博 Top 10 排行

## 🛠️ 交互功能

侧边栏提供以下全局筛选器：

- **日期范围筛选** — 选择分析的时间窗口
- **地区筛选** — 多选关注的地理区域
- **互动量阈值** — 过滤低互动量的微博
- **话题标签筛选** — 聚焦特定话题的内容

所有筛选器实时联动，筛选后仪表板中的全部图表和数据自动更新。

## 📈 生成的图表

| 序号 | 文件名 | 内容 |
|------|--------|------|
| 1 | `01_likes_histogram.png` | 点赞/评论/转发分布直方图（含KDE密度曲线） |
| 2 | `02_region_top10.png` | 各地区总互动量 Top 10 |
| 3 | `03_daily_trend.png` | 每日互动量趋势折线图 |
| 4 | `04_hourly_activity.png` | 24小时发布活跃度分布 |
| 5 | `05_correlation_heatmap.png` | 互动指标相关性热力图 |
| 6 | `06_scatter_likes_comments.png` | 点赞数 vs 评论数散点图（含边际直方图） |
| 7 | `07_wordcloud.png` | 微博高频词云图 |
| 8 | `08_hashtag_top10.png` | 热门话题标签 Top 10 |
| 9 | `09_boxplot.png` | 互动量指标箱线图 |
| 10 | `10_interaction_pie.png` | 互动类型占比环形图 |

## 🎨 技术栈

- **Web 框架**: Streamlit
- **数据处理**: Pandas, NumPy
- **可视化**: Matplotlib, Seaborn, WordCloud
- **中文分词**: Jieba
- **中文字体**: 自动检测 Microsoft YaHei / SimHei / Noto Sans SC 等

---

> 📝 **计算机应用大作业** | 杭州亚运会社交媒体互动数据分析平台
