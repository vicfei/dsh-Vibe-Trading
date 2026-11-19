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

## 安装

```bash
npm i -g dsh-vibe-trading          # 或：dsh plugin add dsh-vibe-trading
dsh-vibe-trading run --question "Moutai vs the index: whose price-volume structure is weaker?" \
  --symbols sh600519,sh000001 --name moutai-vs-index
dsh-vibe-trading scan --symbols sh600519,sz000001,sh000001 --board momentum
```

需要 PATH 上有 `python3`（纯 stdlib，无 pip 安装）；npm 包同时注册宿主 typed
tools（`vibe_research` / `vibe_scan`）与技能。源码方式：clone 后直接
`python3 scripts/vibe_research.py`。

```bash
python3 scripts/vibe_research.py --question "茅台 vs 上证：量价结构谁更弱？" --symbols sh600519,sh000001 --lang zh   # 中文
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

v0.3.0——V1 硬化、V2 版本化工件、V3 工作台全部交付；35 项 hermetic 测试 +
CI 绿；typed tools 已在真实宿主形状验证。见 [ROADMAP](ROADMAP.md)——V4 因子
工坊+家族互通，V5 RESEARCH-TRAIL spec + WeKnora 问史库。盒内新增：MACD/RSI/
相关性指标、确定性榜单（动量/波动/量能/相关性）、多问题会话、版本化 append-only
研究工件与修订 diff。

## 致谢与免责

致敬 HKUDS/Vibe-Trading——独立原生重实现，MIT。**非投资建议**。
回测为免费率的结构探针。
