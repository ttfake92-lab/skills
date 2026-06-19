---
name: AI-video-prompt
description: "Turn a script, story beat, or shot idea into NeoWOW-style AI video prompts with image-reference binding, timeline action, sound, and hard constraints. Use when the user asks for AI video prompts, NeoWOW/Seedance prompts, image-reference video generation, script-to-video prompts, 多图参考, 首尾帧, 全能参考, 视频提示词, or wants a script converted into complete copy-paste video prompts."
---

# AI Video Prompt

Generate complete video prompts in the observed NeoWOW workflow style: **image references first, dense single-block prompt, time-coded action, sound design, and explicit constraints**.

## Quick Start

When the user provides a script, story, voiceover, or rough idea:

1. Split it into 8-15 second generation units by scene, location, time jump, action beat, or emotional turn.
2. For each unit, choose a reference mode: `多图参考` for several image anchors, `首尾帧` for start/end continuity, `全能参考` for mixed character/scene/prop anchors, or `动作模仿` only when a reference video drives motion.
3. Output a complete prompt pack for each unit:

```md
片段一：[one-line beat]
生成模式：[多图参考 / 首尾帧 / 全能参考]
模型参数：Seedance 2.0 | 720p | 16:9 | [10s/12s/15s]
参考图片：
图片1：[role, e.g. character look / location DNA / prop]
图片2：[role]

提示词：
[copy-paste-ready NeoWOW prompt]
```

If no reference images are provided, still generate placeholders (`图片1`, `图片2`) and state exactly what each image should be before the prompt.

## Prompt Formula

Write one dense prompt block, not a loose storyboard. Use Chinese labels with `【】` only when they improve control.

Order the content like this:

1. **Opening control sentence**: duration, shot form, core style, camera/film look, aspect ratio.
2. **Image binding**: define each image's job before action starts.
3. **Scene / spatial structure**: geography, subject placement, depth layers, crowd/traffic/props.
4. **Time-coded action**: use `【0-2秒】`, `【2-4秒】`, etc. for 10-15s clips; use exact second marks for reveals, occlusions, hard cuts, or transformations.
5. **Camera motion**: distance, height, lens behavior, tracking direction, handheld/stabilizer, when the frame must not move.
6. **Sound design**: environment bed first, then event sounds by time; specify distance and clarity.
7. **Style / light / color**: concrete film stock, camera, lens, color palette, light direction, grain, contrast.
8. **Hard constraints**: mark must-follow rules with `必须严格遵守`, especially scale, spatial logic, continuity, performance, and forbidden failure modes.

## Image Reference Rules

- Use NeoWOW-style references: `图片1`, `图片2`, `图片3`, and `@图片1` when binding must be explicit.
- Assign one job per image: character identity, outfit/look, first frame, end frame, location DNA, prop, creature/mecha/object, or style plate.
- Bind identity with concrete locked attributes: face, hair, clothing, body scale, object silhouette, colors, texture, and relation to the scene.
- Bind scene images as visual DNA: lighting, composition, wall/road layout, color temperature, atmosphere.
- Do not say only "参考图片". Say what is locked and what can change.
- If a prompt uses multiple images, mention them inside the action where they matter: "参考图片1的造型", "首帧锁定图片2", "票图片3从画面顶部飘入".

## Constraint Rules

Use constraints as production controls, not decoration:

- **Scale**: full body / half body / close-up, exact subject size in frame.
- **Spatial logic**: where characters, roads, vehicles, props, and background layers are allowed to be.
- **Motion logic**: action order, speed changes, occlusion timing, hard cut timing, incomplete actions.
- **Performance**: real, restrained, not theatrical unless requested.
- **Sound**: no music unless requested; specify distant street capture, muffled dialogue, or clear event sounds.
- **Continuity**: character, outfit, prop state, first/end frame, and next-shot handoff.
- **Negative controls**: avoid empty streets, staged extras, CG/game look, over-close framing, broken anatomy, impossible object movement, clear dialogue when dialogue must be muffled.

## Output Style

- Make every prompt copy-paste-ready.
- Prefer one strong paragraph with `【】` sections over many Markdown bullets inside the prompt.
- Use exact physical action: body weight, hand position, gaze, breath, cloth friction, object path.
- Make sound as specific as visuals.
- End each segment with model settings and any image upload notes.

See [verification-sample.md](references/verification-sample.md) for a script-to-prompt example.
