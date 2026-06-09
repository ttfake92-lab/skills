---
name: yyl-remotion-video
description: Build 16:9 spoken-video compositions as standalone Remotion projects with React, TypeScript, frame-based animation, estimated durations, and direct mp4 rendering. Use when the user wants video files, Remotion, mp4 export, frame-accurate motion, post-production voiceover, or theme-driven video templates; do not use for click-driven web presentations.
---

# YYL Remotion Video

Turn an article, script, notes, or clear outline into a **Remotion video project**.
This skill is video-first: no click-driven web player, no web `presentation/`, no TTS
synthesis inside this workflow.

## Core Output

```
my-video/
├── article.md
├── script.md
├── outline.md
├── notes.md
└── remotion/
    ├── src/Root.tsx
    ├── src/Composition.tsx
    ├── src/chapters/<NN>-<id>/
    │   ├── <Chapter>.tsx
    │   ├── narrations.ts
    │   └── timing.ts
    ├── public/assets/
    ├── preview-stills/
    └── out/
```

Bundled skill resources:

```
themes/       # color / typography systems
templates/    # copyable Remotion TSX starting points
references/   # craft, theme, and template guidance
```

## Execution Strength

Decide before writing files:

| Strength | Use When | Behavior |
|---|---|---|
| Quick | <= 450 Chinese chars, <= 60s, theme test, draft demo | 1 chapter, few beats, direct implementation |
| Standard | 1-4 min, normal publishable explainer | script + outline, first chapter anchor, then continue |
| Strict | > 4 min, brand/commercial/high-risk content | fuller planning, more still checks, slower chapter review |

Report in one line:

```
I will use <Quick/Standard/Strict> because <length / risk / target>.
```

## Workflow

1. **Input Gate**
   - Proceed only if the user gives source text, a script, notes, or a clear outline.
   - If they only give a topic, ask for material. Do not invent a full video.

2. **Content Files**
   - Save source material to `article.md` when provided.
   - Save final spoken text to `script.md`.
   - Save development plan to `outline.md`.
   - `outline.md` plans chapters, beats, screen content, information pool, assets.
   - `outline.md` does **not** prescribe exact animation implementation.

3. **Theme Choice**
   - Use only themes bundled in this skill: `themes/command-film`,
     `themes/studio-white`, `themes/research-desk`.
   - Do not reuse or import themes from `web-video-presentation`.

4. **Template Choice**
   - If the user asks for a known layout or animation mechanism, read
     [references/TEMPLATES.md](references/TEMPLATES.md).
   - Use `templates/luxury-perspective-gallery` for luxury dark portfolio,
     3D perspective horizontal carousel, or premium agency gallery requests.

5. **Remotion Project**
   - Reuse existing `remotion/` if present.
   - Create only if missing:
     ```bash
     npx create-video@latest --yes --blank --no-tailwind remotion
     ```
   - If a selected template requires Tailwind, create the project with Tailwind
     support or add Tailwind before copying template files.
   - Install dependencies only if `remotion/node_modules` is missing or Remotion
     commands fail because dependencies are absent.

6. **Timing**
   - Do not synthesize audio.
   - Estimate durations from narration and visual complexity.
   - Default `fps = 30`, `width = 1920`, `height = 1080`.
   - Store text in `narrations.ts`; store estimated `durationFrames` in `timing.ts`.

7. **Implementation**
   - Read [references/REMOTION-CRAFT.md](references/REMOTION-CRAFT.md) before each
     chapter.
   - Animate with `useCurrentFrame()`, `interpolate()`, `Easing`, and `Sequence`.
   - Do not use CSS transition / CSS animation / GSAP for primary animation.
   - Tailwind may style static layout, but Tailwind animation utilities are not allowed.

8. **Verification**
   - Run:
     ```bash
     cd remotion
     npm run lint
     ```
   - Render at least one still per chapter, or 2-4 stills for a short full video:
     ```bash
     npx remotion still <composition-id> --frame=<frame> --scale=0.5 --output=preview-stills/<name>.png
     ```
   - Render mp4 when the stills look correct:
     ```bash
     npx remotion render <composition-id> out/<name>.mp4
     ```

9. **Notes**
   - Update `notes.md` with fps, resolution, total frames, estimated duration,
     checked stills, rendered mp4 path, and that audio/subtitles are post-production.

## Theme Selection

| Theme | Best For | Feel |
|---|---|---|
| `command-film` | agents, terminal, automation, developer tools | dark cinematic command room |
| `studio-white` | SaaS demos, launches, courses, product tutorials | clean white product studio |
| `research-desk` | essays, reports, papers, business analysis | calm analytical desk |

For full theme notes, read [references/THEMES.md](references/THEMES.md).

## Template Selection

| Template | Best For | Feel |
|---|---|---|
| `luxury-perspective-gallery` | premium portfolio, product showcase, 3D horizontal carousel | dark cyber-minimal agency slider |
| `charity-doodle-poster` | nonprofit posters, hand-drawn animal heroes, line-boil editorial web effects | retro ink-brush stop-motion poster |

For full template notes, read [references/TEMPLATES.md](references/TEMPLATES.md).

## Remotion Rules

- Use `Composition` in `Root.tsx`.
- Use `Sequence` to place beats on the timeline.
- Use `useCurrentFrame()` + `interpolate()` for motion.
- Place static assets in `remotion/public/assets/`; reference with `staticFile()`.
- Still checks are required before final render.
- The final mp4 is silent unless the user later supplies audio in post-production.
