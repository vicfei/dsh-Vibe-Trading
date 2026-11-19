# dsh-vibe-trading — DeepSeek Harness 原生的交互式投研工作台

**提一个行情问题 → 确定性管道规划、取数、计算、解读——数字全部出自代码，
结论逐条挂靠计算字段。终端纪要 + 零依赖 SVG 交互卡 + 可审计研究轨迹。**

[English](README.md) | [简体中文](README.zh-CN.md)

[![DeepSeek Harness](https://img.shields.io/badge/DSH-plugin-4E6DD4)](https://github.com/deepseek-ai) [![License: MIT](https://img.shields.io/badge/license-MIT-3da639)](LICENSE)

> 结构致敬 [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading)——重组为
> DeepSeek Harness 原生体验。无隶属；独立社区项目。家族：
> [dsh-TradingAgents](https://github.com/vicfei/dsh-TradingAgents)（多空议院）·
> [dsh-ai-hedge-fund](https://github.com/vicfei/dsh-ai-hedge-fund)（人格基金）。

## 为什么需要插件（Vibe-Trading 自带 MCP server——`mcp.json` 不够吗？）

| | 裸 Vibe-Trading MCP in DSH | **dsh-vibe-trading** |
|---|---|---|
| 交互 | 你逐步驱动工具调用 | **研究循环被编排**——规划→取数→计算→解读一条命令 |
| 数字 | 产自模型驱动的调用 | **确定性计算层**——LLM 只解读、引用字段 `[F#]`，不产数 |
| 产物 | 聊天文本 | **终端纪要 + 内联 SVG 交互卡 + 完整轨迹**（问题/规划/统计/回测/结论） |
| 可审计性 | — | 每条结论指向产出它的计算；缺口如实声明 |

## 快速开始（零额外 key）

```bash
git clone https://github.com/vicfei/dsh-Vibe-Trading && cd dsh-vibe-trading
python3 scripts/vibe_research.py --save \
  --question "Moutai vs the Shanghai index: which leg is weaker?" \
  --symbols sh600519,sh000001
python3 scripts/vibe_research.py --question "茅台 vs 上证：量价结构谁更弱？" --lang zh   # 中文
```

真实冒烟（2026-11-16，6 秒，2 次 LLM 调用，temperature=0）：识别指数为较弱腿
（ret20 −3.44% vs +9.73%），标记"缩量上行 vs 缩量下行"结构，并**诚实拒绝倚重
4 笔交易的回测样本**——结论全程挂靠计算字段。打开 `trails/*.html` 看交互卡。
输出英文优先；`--lang zh` 把用户可见标签（与解读语言）切为中文。

## 盒内有什么

- A 股 / 指数 / 美股 K 线（CN 可达的腾讯通道，免 key）
- 统计：ret20/60、SMA60 姿态、30 日波动、距 120 日峰回撤、量能 z 分数
- 迷你趋势回测（SMA20/60 交叉，仅持仓，无费率——结构探针，非建议）
- 零依赖内联 SVG 交互卡（离线安全，无 CDN）
- 可审计轨迹 JSON + 家族证据纪律（数字出自代码，LLM 只解读）

## 状态与路线图

v0 引擎已在真实数据上冒烟。见 [ROADMAP](ROADMAP.md)——V 系列依次交付：
引擎硬化（诚实不可用语义务化/来源元数据随行/样本外纪律）、版本化研究工件、
工作台（筛选器/指标库/多问题会话）、因子工坊与家族互通。

## 致谢与免责

致敬 HKUDS/Vibe-Trading——独立原生重实现，MIT。**非投资建议**。
回测为免费率的结构探针。
