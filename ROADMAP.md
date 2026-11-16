# ROADMAP — dsh-vibe-trading

北极星：三仓家族的第三块拼图，与 [dsh-TradingAgents](https://github.com/vicfei/dsh-TradingAgents)
/ [dsh-ai-hedge-fund](https://github.com/vicfei/dsh-ai-hedge-fund) 同套打法，
**30 天目标 100–300★**，吃 HKUDS/Vibe-Trading 搜索流量。

## 定位纪律（本仓特有）

Vibe-Trading 本身是 MCP server——**插件必须赢在深度集成**：研究循环编排、
确定性计算层（数字出自代码）、交互卡片、可审计轨迹。任何一版退化为
"MCP 调用包装器"就失去了存在理由（README 定位表已明示这一点）。

## 星标策略（与前两仓一体）

1. 名字即流量：`vibe-trading` 全名保留；npm `dsh-vibe-trading` 已验可注册。
2. 关键词矩阵：vibe-trading, deepseek-harness, dsh, quant-research, factor,
   interactive-charts, technical-analysis, ic-memo。
3. 钩子：**"问题进、研究包出"的 6 秒真实数据演示**（SVG 卡可直接贴帖）。
4. 渠道：三仓同日组合拳，互链互推；本仓素材=交互卡截图对比裸 MCP 对话。
5. npm 占位 0.0.1 立即发（owner 手动流程）。

## 里程碑

### M0 · 引擎冒烟 ✅（2026-11-16）
LLM 规划→确定性层（K线/指标/SMA交叉回测/内联 SVG）→LLM 解读（[F#] 挂靠字段，
样本不足自曝）。真实数据 6s/场（茅台 vs 上证），轨迹 HTML+JSON 落盘。

### M0.5 · 发布包
- [ ] README 打磨 + SVG 卡截图首屏 + npm 0.0.1 占位（手动）
- [ ] 公开仓 topics + 三仓互链 + marketplace + 渠道清单（同日）

### M1 · 工作台化（第 2-3 周）
- [ ] 确定性筛选器（多标的横截面扫描：动量/波动/量能异常榜）
- [ ] 指标库扩展（MACD/RSI/相关性矩阵/北向资金）+ 多问题会话（vibe 连续追问）
- [ ] DSH Web canvas 卡集成（dsh-plugin-canvas 先例）+ cordis 插件化 → 0.1.0

### M2 · 因子工坊（第 4-6 周）
- [ ] 自定义因子 DSL（表达示→确定性计算）+ 因子快速回测
- [ ] 与家族互通：研究轨迹 → 一键送 dsh-TradingAgents 开庭 / 基金会估值

### M3 · 生态（第 2 月起）
- [ ] 轨迹格式标准化（IC-MEMO 姊妹件 RESEARCH-TRAIL spec）
- [ ] 历史问题库：可检索的"问过的行情问题"资产

## 纪律（不可让步）

- 数字只出自确定性层；[F#] 挂靠字段；样本不足必须自曝；
- 不做建议（解读结构，不喊方向）；SVG 卡零依赖（无 CDN）；
- 轨迹永不删改（append-only 思想）。
