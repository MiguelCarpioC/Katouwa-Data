# KATOUWA NASA 自主取数 Agent Pipeline

**状态：程序已完成离线单元测试，但在当前工作环境中未成功连接 NASA API。仓库不包含任何伪装成真实 NASA 观测的数值。**

## 本次实际采用的两个红树林观察位置

**严格只使用你之前选定的 P1、P2；旧配置里的其他采样点已移除。**

| 点位 | 纬度 | 经度 | 状态 |
|---|---:|---:|---|
| P1 | 10.705247 | -71.587554 | 你选定的红树林位置；尚未验证 250 m MODIS 像元土地覆盖 |
| P2 | 10.700986 | -71.581910 | 同上 |

坐标保留 **6 位小数**。文献和地图提供位置线索，但不能替代现场样地/高分辨率地表分类。

## 目标

用五个模块（Research Planner / Satellite Collector / Climate Collector / Quality & Statistics / Reporter）自动获取并处理真实 NASA 数据，为 KATOUWA 的 *Earth System Trend Detective* 演示提供可追溯的研究数据。Agent 在这里指独立任务执行模块，并不是五个需要额外支付 token 费用的 LLM。

## 立即运行（macOS、Linux、42 机房网络允许时）

```bash
unzip KATOUWA_Agent_Pipeline.zip
cd KATOUWA_Agent_Pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 先试 P1 的七年（为趋势检验保留至少六个年份），快速验证接口
python run_agents.py --source modis --start 2019 --end 2025 --site MANGROVE_POINT_1
# 再做完整自动分析
python run_agents.py --start 2019 --end 2025
# 展示界面（选择 Agent-fetched NASA data）
streamlit run app.py
```

**关键要求：必须有网络。** 程序自动对 P1/P2（默认两处）做日期查询、每批不超过8个 MODIS 日期的切片请求、缓存原始 JSON、提取中心像元 NDVI / EVI / QA、质量筛查、统计趋势，并生成 CSV 与 PNG。运行时请让命令完成，不要在网络失败时把测试数据当成真实数据。

## 五个 Agent 的职责

| 模块 | 输入 | 输出 |
|---|---|---|
| Planner | 年份、研究候选点 | 研究范围与风险说明 |
| Satellite Collector | NASA ORNL MOD13Q1 API | NDVI、EVI 原始和 QA CSV；缓存 JSON |
| Climate Collector | NASA POWER 月度 API | 气温 T2M、降水 PRECTOTCORR 月度 CSV |
| Quality & Statistics | 上游原始数据 | QA 过滤、年度指标、Theil–Sen / Kendall |
| Reporter | 统计数据 | 年度曲线 PNG、趋势 summary、运行日志 |

## 输入数据源与核实链接

1. NASA ORNL DAAC TESViS API 文档：https://modis.ornl.gov/data/modis_webservice.html。提供 `/MOD13Q1/dates` 和 `/MOD13Q1/subset`；官方说明单次 `/subset` 只能请求最多10个合成日期。程序每批8个日期，避免超过限制。
2. NASA POWER Monthly API 文档：https://power.larc.nasa.gov/docs/services/api/temporal/monthly/。提供 `T2M` 和 `PRECTOTCORR` 月度时间序列。
3. MODIS MOD13Q1 产品：https://doi.org/10.5067/MODIS/MOD13Q1.061。植被指数通常需要从存储整数乘以 0.0001，程序只进行一次缩放。
4. 马拉开波市沿岸红树林保护条例（2021年，第21条）：https://concejomunicipaldemaracaibo.org/wp-content/uploads/2022/01/Ordenanza-para-la-Proteccion-del-Ecosistema-Manglar-y-Costero-del-Municipio-Maracaibo-Sancionada-26.07.2021-1.docx-1.pdf。条例给出 Santa Rosa de Agua–Isla Dorada 和 Las Peonías 沿岸区域的端点；当前两个社区选定点仅供试验，未验证为真实红树林像元。
5. Santa Rosa de Agua 地点坐标来源：https://mapcarta.com/es/19927348。

## 下载结果的位置

- `data/raw/cache/*.json`：**原始 API 响应**，带 SHA-256 记录在 `reports/run_manifest.json`。
- `data/raw/*MODIS_OBSERVATIONS_WITH_QA.csv`：NASA MODIS 各期 NDVI/EVI 原始数值、缩放值、像元可靠性和 QA 结果。
- `data/raw/*POWER_OBSERVATIONS.csv`：NASA POWER 真实数据（气候模型/同化值）。
- `data/processed/real_nasa_observations.csv`：通过 QA 的真实数据，适配 `app.py`。
- `data/processed/annual_summaries.csv`：年度时间序列。
- `reports/trend_summary.csv`：趋势斜率、Kendall p 值、样本量和限制。
- `reports/*.png`：实测数据生成的趋势图。
- `reports/run_manifest.json`：**下载成功或失败**、API 来源、缓存路径、追溯记录。

**如果所有 API 都失败**：返回 `NO_DATA_RETRIEVED`，不生成假趋势和假报告。`data/processed/` 初始是空的。

## 科学边界（答辩请明确说出）

- 使用的是约250米 MODIS 中心像元；它可能混合建筑、水和植被。采样点未经过野外调查或高分辨率土地覆盖核验，**不能直接声称观测到了红树林退化**。
- 只对 `pixel_reliability == 0`、NDVI/EVI 在有效数值范围的数据进行计算；质量较差的观测将出现在原始 QA 表而不会进入统计。
- 年度聚合至少要求每年10个合格样本；至少6个完整年份才报告探索性趋势检验。
- Theil–Sen 斜率和 Kendall p 值没有校正剩余时间自相关、空间多重检验，因此 p<0.05 只是探索性结果，不代表因果解释。
- `PRECTOTCORR` 是月平均降水率（常为 mm/day），不是未经转换的月累计降水量；`T2M` 是2米高度气温。NASA POWER 属于模型/再分析数据，附近多个点可能共用粗网格，不应视为独立气象站。
- 没有生成像元级趋势栅格地图，没有测量水污染，没有测量社区文化变化，没有自动合成原住民证词。
- 更精细的红树林变化需要经过核实的红树林多边形、Landsat/HLS 30米影像、云/水体掩膜和独立验证。

## 测试

```bash
python -m unittest discover -s tests -v
python -m py_compile run_agents.py agents/*.py app.py
```

### 常见故障

- `NameResolutionError`：运行环境不能访问网络或 DNS；不是有数据但数值为零。
- `429`：API 限流；缓存保留已完成请求，稍后重新执行即可继续。不要猛烈并发。
- `400`：坐标、日期、产品/接口参数错误，先仅试一个站点三年。
- `No MODIS composites`：该采样点或区间无有效合成日期。
- `No years with ≥10 observations`：统计 Agent 会拒绝输出趋势，而不是编造结果。

## 未来补充的 Agent

可以在获取到可靠 ROI 边界以后增加：HLS 30米影像下载器、土地覆盖分类、逐像元变化栅格、社区授权资料的时间/空间对比和不确定性报告。**不建议在首轮 Hackathon 就加入尚未验证的 IMCT 指数。**

## 启动和版本建议（macOS）

使用独立的 Python 虚拟环境，不要修改 42/Poetry 现有项目：

```bash
cd KATOUWA_Agent_Pipeline
bash START_KATOUWA_MAC.command
```

若命令需要安装依赖，请确保 Mac 能访问 Python 包仓库。启动后，左侧可直接选择“Both P1 + P2”，点击 NASA MODIS 采集按钮。这个按钮会真正访问 NASA API，无法联网时会明确报告失败。离线排练只能选择红色警告的 **SYNTHETIC interface test**，不能用于证明环境变化。

数据平台扩展（已研究但未自动采集）：NASA Giovanni（气候/环境 CSV）、AppEEARS（点/多边形数据与 QA）、NASA Hydrology、KNMI Climate Explorer。它们都是潜在数据来源，但只有已成功获取、具备明确时空定义和单位的数据才允许进入结果。注意：MODIS 250 m 与 NASA HLS/Landsat 30 m 不是同一套已运行的分析。
