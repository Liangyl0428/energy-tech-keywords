# 技术词归类方法与 Topic → 子方向 映射

本文是 [README](../README.md) 中「归类方法」与「Topic → 子方向」两节的独立版本，并补充 2026-10-31 对 `openalex_energy_fetch` 语料的 Topic 覆盖核对结果。词表的机器可读映射保存在仓库根目录的 [_meta.json](../_meta.json)。

## 一、归类方法

- 每个 OpenAlex topic 归入一个子方向（映射见 `_meta.json` 与下表）；
- 每个技术词按“最能代表它的 topic”（相对排序最靠前）归入该 topic 的子方向，**一词一表，不重复**；
- 2026-10-29 修订：在上述自动归类基础上，按[《术语审核报告》](术语审核报告.md)执行了人工归位（移动）与清洗（删除噪声、修订中英错位、统一缩写），原始 topic→子方向映射未变。

## 二、语料 Topic 覆盖核对（2026-10-31）

### 2.1 统计对象与口径

- 语料：`openalex_energy_fetch/data/article/`，4,968 个 CSV（92 个采集主题 × 54 个半年窗口，2000 上半年—2026 下半年，每个主题 54 个文件）+ 2,472 个 `.meta.json` 旁文件，合计约 129 GB。
- 三个口径不是同一件事，混用会误判"统计是否全面"：
  1. **采集主题**：CSV 文件名前缀 / `matched_query` 列中的 topic id。每篇文献只属于 1 个采集主题，它决定该文献在这套词表体系中的归属；
  2. **`topics` 字段**：OpenAlex 给每篇论文打的最多 3 个 topic（`raw_topics`）；
  3. **`primary_topic`**：上述 3 个中 OpenAlex 判定最贴合的那一个（`raw_primary_topic`）。

### 2.2 统计结果

| 口径 | 不同 topic id 数 | 已对应到子方向 | 说明 |
|---|---:|---:|---|
| 采集主题（文件名 / `matched_query`） | **92** | **92（100%）** | 与本表 92 行一一对应：无遗漏、无多余，每个 topic 只映射到 1 个子方向 |
| 文献 `topics` 字段（每篇 ≤3 个） | 4,433 | 92 | 相当于 OpenAlex 全库 4,516 个 topic 的 98.2% |
| 其中 `primary_topic` | 4,206 | 92 | 按"最主主题"口径统计，同样只有 92 个属于采集主题 |

复现方式（在 `openalex_energy_fetch` 仓库根目录执行；全量 grep 约 129 GB，需数分钟）：

```bash
# 采集主题数：92
ls data/article/*.csv | sed -E 's#.*/(T[0-9]+)_.*#\1#' | sort -u | wc -l

# 语料内出现的全部 topic id：4,433
grep -rhoE 'openalex\.org/T[0-9]{5}' data/article/T*.csv | sort -u | wc -l

# primary_topic 口径：4,206（需逐行解析 raw_primary_topic 列）
```

### 2.3 为什么 4,341 个非采集主题不需要再补映射

结论：**采集主题 92/92 已全部对应到子方向；文献自带的次级主题不参与映射。**

1. 归类方法规定"每个技术词按最能代表它的 topic 归入该 topic 的子方向"，承担归类职责的是**采集主题**：1,811 个词条的主体由这 92 个主题派生（另有 9 个子方向的词条来自人工补充，见第四节）。
2. 采集按 topic 检索召回：只要文献 `topics` 列表（最多 3 个）中命中采集主题就会被收录，所以「采集主题」与「`primary_topic`」经常不是同一个。例如 `T14502_High-Voltage_Power_Transmission_Systems_2026_early.csv` 的 703 篇文献主主题分别是 T11102（145 篇）、T10972（58 篇）、T12451（51 篇）……只有 39 篇以 T14502 为主主题。这些主主题与"该文献为什么被归入这个采集主题"无关，也无法反过来推导词条归属。
3. 4,433 种 topic 已覆盖 OpenAlex 全库 98% 的分类，把它们逐一塞进 33 个子方向既没有操作意义，也会破坏"一个 topic 一个去向"的可核查性。

若日后要按主题做文献计量，请以**文件名前缀或 `matched_query`** 为准（每篇文献唯一、可回溯），不要用 `primary_topic`。

高频非采集主题示例（按出现的采集文件数排序，可见其多为相邻领域或方法类主题）：

| Topic ID | OpenAlex 官方英文名 | 出现文件数 |
|---|---|---:|
| T10278 | Electric Motor Design and Analysis | 2,012 |
| T11529 | Refrigeration and Air Conditioning Technologies | 1,741 |
| T10121 | Building Energy and Comfort Optimization | 1,729 |
| T10998 | Heat Transfer and Optimization | 1,712 |
| T10780 | Reliability and Maintenance Optimization | 1,681 |
| T10435 | Environmental Impact and Sustainability | 1,669 |
| T10310 | Corrosion Behavior and Inhibition | 1,637 |
| T10495 | Catalysts for Methane Reforming | 1,454 |
| T11808 | Superconducting Materials and Applications | 1,447 |
| T10197 | Membrane Separation Technologies | 1,439 |
| T10100 | Metaheuristic Optimization Algorithms Research | 1,361 |
| T10791 | Advanced Control Systems Optimization | 1,338 |

### 2.4 与 OpenAlex 官方主题名核对

- 92 个 topic id 已逐一调用官方接口 `https://api.openalex.org/topics/{id}` 核对，下表的"主题英文名"均为 2026-10-31 的官方 `display_name`。
- OpenAlex 不提供中文名，下表的"主题中文名"为本地译名（沿用 2026-10-29 版本，未作改动）。

## 三、Topic → 子方向

92 个采集主题的完整映射（与根目录 `_meta.json` 的 `topic_map` 一致）：

| Topic ID | 主题英文名（OpenAlex 官方） | 主题中文名 | 归入子方向 |
|---|---|---|---|
| T10018 | Advancements in Battery Materials | 电池材料研究进展 | 1.2 新型储能技术与装备 |
| T10024 | TiO2 Photocatalysis and Solar Cells | 二氧化钛光催化与太阳能电池 | 7.2 太阳能发电 |
| T10030 | Electrocatalysts for Energy Conversion | 能源转换电催化剂 | 7.6 氢能与燃料电池 |
| T10045 | Organic Electronics and Photovoltaics | 有机电子学与光伏 | 7.2 太阳能发电 |
| T10078 | Advanced Photocatalysis Techniques | 先进光催化技术 | 9.3 催化与电化学基础 |
| T10088 | Thermochemical Biomass Conversion Processes | 生物质热化学转化过程 | 7.4 生物质与地热 |
| T10175 | Advanced DC-DC Converters | 先进直流-直流变换器 | 6.2 电力电子化电力系统与稳定控制 |
| T10179 | Supercapacitor Materials and Fabrication | 超级电容器材料与制造 | 1.2 新型储能技术与装备 |
| T10223 | Microgrid Control and Optimization | 微电网控制与优化 | 6.5 配电网与微电网 |
| T10228 | Multilevel Inverters and Converters | 多电平逆变器与变换器 | 6.2 电力电子化电力系统与稳定控制 |
| T10247 | Perovskite Materials and Applications | 钙钛矿材料与应用 | 7.2 太阳能发电 |
| T10281 | Advanced Battery Materials and Technologies | 先进电池材料与技术 | 1.2 新型储能技术与装备 |
| T10284 | Anaerobic Digestion and Biogas Production | 厌氧消化与沼气生产 | 7.4 生物质与地热 |
| T10305 | Power System Optimization and Stability | 电力系统优化与稳定性 | 1.1 新型电力系统建模仿真与运行分析 |
| T10311 | Advancements in Solid Oxide Fuel Cells | 固体氧化物燃料电池研究进展 | 7.6 氢能与燃料电池 |
| T10346 | Magnetic confinement fusion research | 磁约束聚变研究 | 7.5 核电与聚变 |
| T10361 | Silicon Carbide Semiconductor Technologies | 碳化硅半导体技术 | 6.2 电力电子化电力系统与稳定控制 |
| T10409 | Fuel Cells and Related Materials | 燃料电池及相关材料 | 7.6 氢能与燃料电池 |
| T10424 | Electric Power System Optimization | 电力系统优化 | 1.1 新型电力系统建模仿真与运行分析 |
| T10440 | Advanced Thermoelectric Materials and Devices | 先进热电材料与器件 | 9.2 半导体材料与器件 |
| T10454 | Optimal Power Flow Distribution | 最优潮流计算 | 1.1 新型电力系统建模仿真与运行分析 |
| T10468 | Photovoltaic System Optimization Techniques | 光伏系统优化技术 | 7.2 太阳能发电 |
| T10471 | Climate Change Policy and Economics | 气候变化政策与经济学 | 3.1 能源转型战略与政策规划 |
| T10511 | High voltage insulation and dielectric phenomena | 高压绝缘与介电现象 | 6.1 特高压与柔性交直流输电 |
| T10568 | Thermodynamic and Exergetic Analyses of Power and Cooling Systems | 动力与制冷系统热力学及㶲分析 | 8.1 电-热-气综合能源 |
| T10573 | Power Quality and Harmonics | 电能质量与谐波 | 6.3 电网保护、故障与电能质量 |
| T10590 | Chalcogenide Semiconductor Thin Films | 硫族化合物半导体薄膜 | 7.2 太阳能发电 |
| T10592 | Fusion materials and technologies | 聚变材料与技术 | 7.5 核电与聚变 |
| T10603 | Smart Grid Energy Management | 智能电网能量管理 | 1.1 新型电力系统建模仿真与运行分析 |
| T10624 | Silicon and Solar Cell Technologies | 硅基与太阳能电池技术 | 7.2 太阳能发电 |
| T10663 | Advanced Battery Technologies Research | 先进电池技术研究 | 1.2 新型储能技术与装备 |
| T10680 | Wind Energy Research and Development | 风能研究与开发 | 7.1 风力发电 |
| T10740 | Wind Turbine Control Systems | 风力发电机组控制系统 | 7.1 风力发电 |
| T10768 | Electric Vehicles and Infrastructure | 电动汽车与充电基础设施 | 8.4 交通电气化 |
| T10808 | Electric and Hybrid Vehicle Technologies | 纯电动与混合动力汽车技术 | 8.4 交通电气化 |
| T10811 | Hydrogen Storage and Materials | 储氢技术与材料 | 1.2 新型储能技术与装备 |
| T10905 | Solar Thermal and Photovoltaic Systems | 太阳能热利用与光伏系统 | 7.2 太阳能发电 |
| T10917 | Smart Grid Security and Resilience | 智能电网安全与韧性 | 6.4 电网感知、通信与信息物理系统 |
| T10938 | Phase Change Materials Research | 相变材料研究 | 1.2 新型储能技术与装备 |
| T10967 | Carbon Dioxide Capture Technologies | 二氧化碳捕集技术 | 5.1 碳捕集利用与封存 |
| T10972 | Power Systems Fault Detection | 电力系统故障检测 | 6.3 电网保护、故障与电能质量 |
| T11007 | Hybrid Renewable Energy Systems | 混合可再生能源系统 | 1.3 大规模新能源外送与消纳 |
| T11052 | Energy Load and Power Forecasting | 负荷与功率预测 | 1.1 新型电力系统建模仿真与运行分析 |
| T11091 | Extraction and Separation Processes | 萃取与分离过程 | 9.5 其他基础与共性技术 |
| T11102 | HVDC Systems and Fault Protection | 高压直流输电系统与故障保护 | 6.1 特高压与柔性交直流输电 |
| T11185 | Integrated Energy Systems Optimization | 综合能源系统优化 | 1.3 大规模新能源外送与消纳 |
| T11202 | Cavitation Phenomena in Pumps | 泵空化现象 | 7.3 水力与海洋能 |
| T11225 | Geothermal Energy Systems and Applications | 地热能系统与应用 | 7.4 生物质与地热 |
| T11249 | Wireless Power Transfer Systems | 无线电能传输系统 | 8.4 交通电气化 |
| T11250 | Wave and Wind Energy Systems | 波浪能与风能系统 | 7.1 风力发电 |
| T11276 | Solar Radiation and Photovoltaics | 太阳辐射与光伏 | 7.2 太阳能发电 |
| T11302 | CO2 Sequestration and Geologic Interactions | 二氧化碳封存与地质相互作用 | 5.1 碳捕集利用与封存 |
| T11343 | Power Transformer Diagnostics and Insulation | 电力变压器诊断与绝缘 | 6.6 输变电设备与绝缘 |
| T11444 | Electromagnetic Compatibility and Noise Suppression | 电磁兼容与噪声抑制 | 6.2 电力电子化电力系统与稳定控制 |
| T11690 | Advanced battery technologies research | 先进电池技术研究 | 1.2 新型储能技术与装备 |
| T11774 | Adsorption and Cooling Systems | 吸附与制冷系统 | 8.1 电-热-气综合能源 |
| T11784 | CO2 Reduction Techniques and Catalysts | 二氧化碳还原技术与催化剂 | 5.1 碳捕集利用与封存 |
| T11802 | Chemical Looping and Thermochemical Processes | 化学链与热化学过程 | 7.4 生物质与地热 |
| T11877 | Iron oxide chemistry and applications | 氧化铁化学与应用 | 9.3 催化与电化学基础 |
| T11941 | Power System Reliability and Maintenance | 电力系统可靠性与维护 | 1.1 新型电力系统建模仿真与运行分析 |
| T11954 | Energy Efficiency and Management | 能效与能源管理 | 1.1 新型电力系统建模仿真与运行分析 |
| T12008 | Solar-Powered Water Purification Methods | 太阳能水净化方法 | 7.2 太阳能发电 |
| T12046 | MXene and MAX Phase Materials | MXene与MAX相材料 | 9.1 电池与储能材料 |
| T12118 | Forest Biomass Utilization and Management | 林业生物质利用与管理 | 7.4 生物质与地热 |
| T12129 | Global Energy Security and Policy | 全球能源安全与政策 | 3.1 能源转型战略与政策规划 |
| T12146 | Power Line Communications and Noise | 电力线通信与噪声 | 6.4 电网感知、通信与信息物理系统 |
| T12271 | Renewable energy and sustainable power systems | 可再生能源与可持续电力系统 | 1.3 大规模新能源外送与消纳 |
| T12277 | Frequency Control in Power Systems | 电力系统频率控制 | 6.2 电力电子化电力系统与稳定控制 |
| T12300 | Advanced Electrical Measurement Techniques | 先进电气测量技术 | 6.4 电网感知、通信与信息物理系统 |
| T12309 | solar cell performance optimization | 太阳能电池性能优化 | 7.2 太阳能发电 |
| T12451 | Smart Grid and Power Systems | 智能电网与电力系统 | 6.5 配电网与微电网 |
| T12503 | Social Acceptance of Renewable Energy | 可再生能源社会接受度 | 3.1 能源转型战略与政策规划 |
| T12639 | Global Energy and Sustainability Research | 全球能源与可持续性研究 | 3.1 能源转型战略与政策规划 |
| T12706 | Subcritical and Supercritical Water Processes | 亚临界与超临界水处理过程 | 8.1 电-热-气综合能源 |
| T12719 | Aerospace Engineering and Energy Systems | 航空航天工程与能源系统 | 8.4 交通电气化 |
| T12737 | Electrical Fault Detection and Protection | 电气故障检测与保护 | 6.3 电网保护、故障与电能质量 |
| T12804 | Thermal Analysis in Power Transmission | 输变电热分析 | 6.6 输变电设备与绝缘 |
| T12810 | Real-time simulation and control systems | 实时仿真与控制系统 | 1.1 新型电力系统建模仿真与运行分析 |
| T12838 | Photovoltaic Systems and Sustainability | 光伏系统与可持续性 | 7.2 太阳能发电 |
| T12898 | Induction Heating and Inverter Technology | 感应加热与逆变技术 | 6.2 电力电子化电力系统与稳定控制 |
| T13093 | Electric Power Systems and Control | 电力系统与控制 | 6.2 电力电子化电力系统与稳定控制 |
| T13183 | Islanding Detection in Power Systems | 电力系统孤岛检测 | 6.3 电网保护、故障与电能质量 |
| T13298 | Solar Energy Systems and Technologies | 太阳能系统与技术 | 7.2 太阳能发电 |
| T13331 | Energy and Environmental Sustainability | 能源与环境可持续性 | 3.1 能源转型战略与政策规划 |
| T13429 | Electricity Theft Detection Techniques | 窃电检测技术 | 6.3 电网保护、故障与电能质量 |
| T13715 | Power Line Inspection Robots | 输电线路巡检机器人 | 6.6 输变电设备与绝缘 |
| T13856 | Advanced Power Generation Technologies | 先进发电技术 | 7.5 核电与聚变 |
| T13975 | Energy, Economy, and Technology Trends | 能源、经济与技术趋势 | 3.1 能源转型战略与政策规划 |
| T14276 | Power Systems and Technologies | 电力系统与技术 | 9.5 其他基础与共性技术 |
| T14444 | Power Systems and Renewable Energy | 电力系统与可再生能源 | 7.7 新能源并网与构网型控制 |
| T14481 | Renewable Energy and Sustainability | 可再生能源与可持续性 | 7.7 新能源并网与构网型控制 |
| T14502 | High-Voltage Power Transmission Systems | 高压输电系统 | 6.1 特高压与柔性交直流输电 |

## 四、子方向覆盖观察

92 个采集主题分布在 24 个子方向（另 9 个子方向没有 topic 来源）：

| 子方向 | 来源 topic 数 | Topic ID |
|---|---:|---|
| 1.1 新型电力系统建模仿真与运行分析 | 8 | T10305、T10424、T10454、T10603、T11052、T11941、T11954、T12810 |
| 1.2 新型储能技术与装备 | 7 | T10018、T10179、T10281、T10663、T10811、T10938、T11690 |
| 1.3 大规模新能源外送与消纳 | 3 | T11007、T11185、T12271 |
| 3.1 能源转型战略与政策规划 | 6 | T10471、T12129、T12503、T12639、T13331、T13975 |
| 5.1 碳捕集利用与封存 | 3 | T10967、T11302、T11784 |
| 6.1 特高压与柔性交直流输电 | 3 | T10511、T11102、T14502 |
| 6.2 电力电子化电力系统与稳定控制 | 7 | T10175、T10228、T10361、T11444、T12277、T12898、T13093 |
| 6.3 电网保护、故障与电能质量 | 5 | T10573、T10972、T12737、T13183、T13429 |
| 6.4 电网感知、通信与信息物理系统 | 3 | T10917、T12146、T12300 |
| 6.5 配电网与微电网 | 2 | T10223、T12451 |
| 6.6 输变电设备与绝缘 | 3 | T11343、T12804、T13715 |
| 7.1 风力发电 | 3 | T10680、T10740、T11250 |
| 7.2 太阳能发电 | 12 | T10024、T10045、T10247、T10468、T10590、T10624、T10905、T11276、T12008、T12309、T12838、T13298 |
| 7.3 水力与海洋能 | 1 | T11202 |
| 7.4 生物质与地热 | 5 | T10088、T10284、T11225、T11802、T12118 |
| 7.5 核电与聚变 | 3 | T10346、T10592、T13856 |
| 7.6 氢能与燃料电池 | 3 | T10030、T10311、T10409 |
| 7.7 新能源并网与构网型控制 | 2 | T14444、T14481 |
| 8.1 电-热-气综合能源 | 3 | T10568、T11774、T12706 |
| 8.4 交通电气化 | 4 | T10768、T10808、T11249、T12719 |
| 9.1 电池与储能材料 | 1 | T12046 |
| 9.2 半导体材料与器件 | 1 | T10440 |
| 9.3 催化与电化学基础 | 2 | T10078、T11877 |
| 9.5 其他基础与共性技术 | 2 | T11091、T14276 |

- 来源最集中的方向：7.2 太阳能发电（12 个 topic）、1.1 新型电力系统建模仿真与运行分析（8 个）、1.2 新型储能技术与装备（7 个）、6.2 电力电子化电力系统与稳定控制（7 个）；最窄的是 7.3 水力与海洋能、9.1 电池与储能材料、9.2 半导体材料与器件（各 1 个）。
- 9 个子方向（2.1 地区实践与示范工程、3.2 能源-环境-经济集成建模、4.1 电力市场机制与商业模式、4.2 碳市场与绿证绿电交易、5.2 气候与电力气象、5.3 碳排放核算与减排评价、8.2 电-氢-碳耦合、8.3 建筑与终端用能、9.4 表征与测试方法）在当前 [_meta.json](../_meta.json) 中没有任何 topic 来源，其词条全部来自人工归位与补充（见[《修复变更日志》](修复变更日志.md)）。这不影响"每个 topic 只有一个去向"的完整性，但这 9 个方向无法由 OpenAlex topic 自动回溯，后续维护需单独留意。
