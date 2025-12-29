# 新增Benchmark列表

本文档总结了相对于初始26个benchmark（不包括LMArena categories）的新增benchmark。

## 新增Benchmark汇总

从原始的26个benchmark增加到目前的31个benchmark，共新增**4个全新的benchmark**，同时**1个benchmark被拆分为2个**，实际新增**6个benchmark条目**。

---

## 1. Artificial Analysis统一表格方法新增Benchmark（4个）

以下4个benchmark是全新添加的，它们的数据来自Artificial Analysis统一表格：https://artificialanalysis.ai/leaderboards/models

| 序号 | Benchmark名称 | Benchmark ID | 分类 | 数据来源 | 说明 |
|------|--------------|--------------|------|---------|------|
| 1 | Terminal-Bench Hard (Agentic Coding & Terminal Use) | `terminal_bench_hard` | Coding (Agentic) | Artificial Analysis统一表格 | 新的benchmark，与Terminal-Bench v2.0不同 |
| 2 | τ²-Bench Telecom (Agentic Tool Use) | `tau2_bench_telecom` | Coding (Agentic) | Artificial Analysis统一表格 | 新的benchmark |
| 3 | AA-LCR (Long Context Reasoning) | `aa_lcr` | Hard Prompts | Artificial Analysis统一表格 | 新的benchmark |
| 4 | GPQA Diamond (Scientific Reasoning) | `gpqa_diamond` | Expert | Artificial Analysis统一表格 | 新的benchmark，与GPQA不同 |

---

## 2. FrontierMath拆分新增（2个）

FrontierMath原为1个benchmark，现拆分为2个独立的benchmark条目：

| 序号 | Benchmark名称 | Benchmark ID | 分类 | 数据来源 | 说明 |
|------|--------------|--------------|------|---------|------|
| 5 | FrontierMath Tier 1-3 | `frontiermath_tier1_3` | Math | Epoch.ai平台（手动下载） | 原FrontierMath的前3个Tier，现作为独立benchmark |
| 6 | FrontierMath Tier 4 | `frontiermath_tier4` | Math | Epoch.ai平台（手动下载） | 原FrontierMath的第4个Tier，现作为独立benchmark |

---

## 3. 数据来源变更的Benchmark（非新增，仅URL变更）

以下benchmark不是新增的，而是将数据来源从原URL迁移到Artificial Analysis统一表格，URL发生了变化：

| Benchmark名称 | 原URL | 新URL | 说明 |
|--------------|-------|-------|------|
| Humanity's Last Exam (HLE) | https://scale.com/leaderboard/humanitys_last_exam | https://artificialanalysis.ai/leaderboards/models | URL变更，数据来源改为统一表格 |
| MMLU-Pro | https://huggingface.co/spaces/TIGER-Lab/MMLU-Pro | https://artificialanalysis.ai/leaderboards/models | URL变更，数据来源改为统一表格 |
| LiveCodeBench | https://livecodebench.github.io/leaderboard.html | https://artificialanalysis.ai/leaderboards/models | URL变更，数据来源改为统一表格 |
| SciCode | https://artificialanalysis.ai/evaluations/scicode | https://artificialanalysis.ai/leaderboards/models | URL变更，数据来源改为统一表格 |
| IFBench | https://artificialanalysis.ai/evaluations/ifbench | https://artificialanalysis.ai/leaderboards/models | URL变更，数据来源改为统一表格 |
| AIME (2025) | https://llm-stats.com/benchmarks/aime-2025 | https://artificialanalysis.ai/leaderboards/models | URL变更，数据来源改为统一表格 |

**注意**：这些benchmark在统计中不计入新增，因为它们已经在原始26个benchmark中存在，只是数据获取方式发生了变化。

---

## 统计总结

| 类别 | 数量 | 说明 |
|------|------|------|
| 完全新增的benchmark | 4个 | Terminal-Bench Hard, τ²-Bench Telecom, AA-LCR, GPQA Diamond |
| 拆分新增的benchmark条目 | 2个 | FrontierMath Tier 1-3, FrontierMath Tier 4 |
| **新增benchmark条目总数** | **6个** | |
| URL变更的benchmark | 6个 | 不计入新增，仅数据来源变更 |

**最终统计**：
- 原始benchmark数量：26个
- 新增benchmark条目：6个（4个完全新增 + 2个拆分新增）
- 当前benchmark总数：31个（26 + 6 - 1 = 31，其中FrontierMath拆分导致原1个变成2个，净增1个）

---

## 新增Benchmark详细信息

### 1. Terminal-Bench Hard

- **完整名称**: Terminal-Bench Hard (Agentic Coding & Terminal Use)
- **Benchmark ID**: `terminal_bench_hard`
- **URL**: https://artificialanalysis.ai/leaderboards/models
- **分类**: Coding (Agentic)
- **爬取方法**: Artificial Analysis统一表格
- **数据文件**: `github/data/raw/benchmarks/terminal_bench_hard.csv`
- **说明**: 新的benchmark，与Terminal-Bench v2.0（使用pandas.read_html方法）不同

### 2. τ²-Bench Telecom

- **完整名称**: τ²-Bench Telecom (Agentic Tool Use)
- **Benchmark ID**: `tau2_bench_telecom`
- **URL**: https://artificialanalysis.ai/leaderboards/models
- **分类**: Coding (Agentic)
- **爬取方法**: Artificial Analysis统一表格
- **数据文件**: `github/data/raw/benchmarks/tau2_bench_telecom.csv`
- **说明**: 新的benchmark，专注于工具使用能力的评估

### 3. AA-LCR

- **完整名称**: AA-LCR (Long Context Reasoning)
- **Benchmark ID**: `aa_lcr`
- **URL**: https://artificialanalysis.ai/leaderboards/models
- **分类**: Hard Prompts
- **爬取方法**: Artificial Analysis统一表格
- **数据文件**: `github/data/raw/benchmarks/aa_lcr.csv`
- **说明**: 新的benchmark，专注于长文本上下文推理能力

### 4. GPQA Diamond

- **完整名称**: GPQA Diamond (Scientific Reasoning)
- **Benchmark ID**: `gpqa_diamond`
- **URL**: https://artificialanalysis.ai/leaderboards/models
- **分类**: Expert
- **爬取方法**: Artificial Analysis统一表格
- **数据文件**: `github/data/raw/benchmarks/gpqa_diamond.csv`
- **说明**: 新的benchmark，与GPQA（使用Selenium方法从llm-stats.com爬取）不同，专注于科学推理能力

### 5. FrontierMath Tier 1-3

- **完整名称**: FrontierMath Tier 1-3
- **Benchmark ID**: `frontiermath_tier1_3`
- **URL**: https://epoch.ai/frontiermath
- **分类**: Math
- **爬取方法**: 手动下载
- **数据文件**: `github/data/raw/benchmarks/manual/frontiermath_tier1_3.csv`
- **说明**: 原FrontierMath的前3个Tier，现作为独立的benchmark

### 6. FrontierMath Tier 4

- **完整名称**: FrontierMath Tier 4
- **Benchmark ID**: `frontiermath_tier4`
- **URL**: https://epoch.ai/frontiermath
- **分类**: Math
- **爬取方法**: 手动下载
- **数据文件**: `github/data/raw/benchmarks/manual/frontiermath_tier4.csv`
- **说明**: 原FrontierMath的第4个Tier，现作为独立的benchmark

---

## 更新日期

最后更新: 2025-12-28

