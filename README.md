# Glossary Scribe — Node Molecule (V0.1)

> 以“节点分子（Node Molecule）”形态实现的最小可用术语表生成器：
> 读取一段非结构化文本 → 产出符合 `terms.yaml` 口径的结构化条目（本仓用 JSON 作金样本，CLI 输出 YAML）。

- 名称（统一术语）：**节点分子 / Node Molecule**
- Z 等级：**Z2**（L0/L1/L2 全绿：结构合法、金样本等价、性质与约束）
- 运行形态：**LangGraph/脚本**均可；本仓提供纯 Python 版本（零依赖/无数据库/无网络）。
- TCK：见 `tck/`（L0/L1/L2）
- 规范：见 `specs/node-molecule.spec.json`（同时提供 `specs/node-molecule.spec.yaml` 供阅读）

## 快速开始

```bash
# 运行 CLI（输入自由文本，从 stdin 读取；输出 YAML 到 stdout）
python -m glossary_scribe.cli << 'EOF'
persona_state，中文名叫“身份状态”，也叫“Persona”或“身份画像”。
工程上对应的主题是 ps.persona_state.v2.0。
EOF
```

示例输出（YAML）：
```yaml
- id: persona_state
  canonical_zh: "身份状态"
  canonical_en: "Persona State"
  aliases: ["Persona", "身份画像"]
  engineering_bindings:
    topics: ["ps.persona_state.v2.0"]
    schemas: ["schemas/ps/events/ps.persona_state.v2.0.schema.json"]
  rationale: "PS 本体与运行态统一表述；工程主题保留 v2.0。"
```

## 运行 TCK（L0/L1/L2）

```bash
python run_tests.py
# 或直接：
python -m glossary_scribe.tck_runner
```

## 目录结构

```
glossary-scribe-node/
  README.md
  run_tests.py
  specs/
    node-molecule.spec.json
    node-molecule.spec.yaml      # 人读版（程序不依赖）
    terms.schema.json            # L0 所需的结构/口径约束
  tck/
    l0/
      node_rules.json            # L0 检查所用规则
    l1/
      persona_state_input.txt
      persona_state_expected.json
    l2/
      properties.json            # 性质断言与预算线（此处为静态规则）
  glossary_scribe/
    __init__.py
    engine.py
    yaml_utils.py
    node_molecule.py
    tck_runner.py
    cli.py
```

## 设计说明

- **为什么是“节点分子”？** 本工具在图中作为可运行节点，并绑定输入/输出、回放/观测等运行位形；它引用（或内嵌）抽取逻辑，满足 L0/L1/L2。  
- **Z 等级为何为 Z2？** 我们实现了：
  - L0：输出结构与字段口径检查（必备字段、id 形态、topic 格式等）；
  - L1：金样本输入→输出等价（稳定重放）;
  - L2：性质与约束（幂等、去重、规范化、长度/前缀/重复约束）。
- **为什么金样本用 JSON？** 为了零依赖（无需 YAML 解析器），L1/ L2 的“等价判定”使用 JSON 金样本；CLI 输出 YAML 便于人类阅读。

## 许可证
MIT
