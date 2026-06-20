# 钩子组件 Components（可选）

> pop-out 技法下，封面默认**不放**组件——暗化原图本身已是环境/语境，人物 + 黄块标题已经够强。只有当主题特别需要一个技术暗示（如纯讲某个 CLI）时才加，且只加 1 个。

钩子组件 = 一张封面里**唯一**那个"这条视频讲什么"的视觉暗示。一张封面最多放 1 个。里面的小字是装饰，不放需要细读的真信息。

在 `brief.json` 里用 `component` 字段配置；渲染逻辑在 `src/render.py` 的 `component_html()`，样式在模板 `.hook`。

## terminal —— 终端框

适合 Codex / Claude Code / Agent / 自动化主题。

```json
"component": {
  "type": "terminal",
  "title": "thumbnail-skill",
  "lines": [
    "$ codex run thumbnail",
    "> cutting out subject...",
    "> rendering 16:9 / 4:3 / 3:4",
    "✓ done in 4.2s"
  ]
}
```

- `title`：标题栏文字（窗口名）。
- `lines`：3–5 行，短。`$` 开头=命令感，`✓` / `done`=成功态。

## github —— 仓库卡

适合开源项目、stars、工具类。

```json
"component": {
  "type": "github",
  "repo": "yuyile/thumbnail-skill",
  "desc": "AI Cover Generator",
  "stars": "4.8k"
}
```

## none —— 不放组件

留空或不写 `component`。当人物 + 标题已经够强时，**不放组件反而更高级**。

---

## 设计约束

- 组件用 `--card-bg` 半透明 + 描边 + 模糊背板，融进画面，不是硬贴的白卡。
- 字体用等宽 `--font-mono`，强化"技术感"。
- 尺寸克制：宽度约画面 30–46%（见模板各比例 `.hook` 规则）。
- 颜色只用青/黄点缀，**不要**让组件出现大面积亮色抢标题。

## 想加新组件？

1. 在 `src/render.py` 的 `component_html()` 加一个 `type` 分支，产出一段 `<div class="hook ...">`。
2. 复用模板里已有的 `.hook .bar/.body/.dot` 类，必要时在模板 `<style>` 里加该类型的专属样式。
3. 在本文件登记用法。

候选（按需再做，别一次堆全）：状态条 `status`、代码 diff `diff`、推特卡 `tweet`、prompt 卡 `prompt`。
