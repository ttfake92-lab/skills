# yyl-video-thumbnail

给视频做高点击封面（缩略图）的 skill。**pop-out 技法**：抠图人物全亮叠在自己那张被压暗的原图上、大标题压中间；一套内容用 HTML/CSS 重排成 **16:9 / 4:3 / 3:4** 三个比例。

主战场：B站 / YouTube / 抖音·视频号。走 YouTube 高设计感美学，区别于 `yuyile-social-card-skill`（小红书/杂志风）。

## setup（一次性）

```bash
pip install "rembg[cpu]" onnxruntime
python3 -m playwright install chromium
```

## 用法

```bash
# 1) 抠图：真人照片 → 整幅透明 PNG（不裁外框，用于 pop-out 对齐）
python3 src/cutout.py input/person.jpg input/person-cut.png

# 2) 渲染：brief.json → 3 张高清封面
python3 src/render.py examples/codex/brief.json output/
```

输出：`output/<name>-{16x9,4x3,3x4}.png`（device_scale_factor=2 高清）。

`brief.json` 里 `photo`=原图、`person_image`=抠图，**必须同一张**。字段见 `examples/codex/brief.json` 和 `SKILL.md`。

## 怎么改调性

- 配色/字体：改 `assets/template-popout.html` / `assets/template-ui.html` 顶部 `:root` 令牌。
- 两套模板（海报风 popout / 命令面板风 ui）：brief 里 `template` 字段切换。
- 美学规则、pop-out 三层、标题/人物/验收清单：见 `references/brand-system.md`。
- 可选钩子组件：见 `references/components.md`。

技术栈：Python + Playwright(Chromium) 截图渲染 + rembg 抠图。字体：Archivo Black(拉丁) + PingFang SC(中文，可换 Heavy)。
