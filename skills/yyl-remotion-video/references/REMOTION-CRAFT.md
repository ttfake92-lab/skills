# Remotion Chapter Craft

Use this before implementing each Remotion chapter.

## Mental Model

Remotion is frame-driven. Every visual state must be derivable from:

- current frame from `useCurrentFrame()`
- composition config from `useVideoConfig()`
- explicit timing from `timing.ts`

Do not rely on browser runtime animation.

## Required Files Per Chapter

```
src/chapters/<NN>-<id>/
├── <Chapter>.tsx
├── narrations.ts
└── timing.ts
```

`narrations.ts`:

```ts
export const narrations = ["...", "..."];
```

`timing.ts`:

```ts
export const timings = [
  { step: 0, durationFrames: 120 },
  { step: 1, durationFrames: 150 },
];
```

`timings.length` must equal `narrations.length`.

## Duration Estimation

Default: `fps = 30`.

- Normal Chinese narration: roughly `6-8 frames` per Chinese character.
- Short pause: add `12-24 frames`.
- Important visual hold: add `24-60 frames`.
- Complex chart / UI demonstration: split into multiple beats instead of one long beat.

The goal is not perfect voice sync. The user will add voiceover in post.

## Animation Rules

Use:

- `useCurrentFrame()`
- `useVideoConfig()`
- `interpolate()`
- `Easing`
- `<Sequence from={...} durationInFrames={...}>`

Avoid:

- CSS transition
- CSS animation
- GSAP
- `setTimeout`
- `setInterval`
- `Date.now()`
- `Math.random()` unless seeded

## Layout Rules

- Design for 1920x1080.
- Use large type: title usually 80px+.
- Keep safe margins around the frame.
- Every beat should focus on 1-3 visual ideas.
- Use visual demonstrations: icons, diagrams, UI panels, charts, terminal panels,
  data flows, comparison cards, or motion typography.
- Do not make pure text-only chapters.

## Theme Rules

Use the selected theme palette and typography from this skill only.
Do not import web-video-presentation themes.

When useful, copy the selected theme's values into `src/index.css` as CSS variables.
Primary motion still comes from Remotion frame interpolation.

## Self-Check

Before reporting a chapter done:

- [ ] `narrations.ts` and `timing.ts` lengths match.
- [ ] Main animation is frame-driven, not CSS/GSAP-driven.
- [ ] At least one visual demonstration exists.
- [ ] Text is large and readable at 1920x1080.
- [ ] No fake data, fake logos, or irrelevant decorative icons.
- [ ] `npm run lint` passes.
- [ ] At least one still frame was rendered for inspection.

