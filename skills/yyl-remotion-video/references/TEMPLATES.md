# Remotion Templates

Templates are bundled TSX starting points. Use them when the user asks for a
specific visual mechanism, not as general themes.

## Included Templates

| id | Use When | Files |
|---|---|---|
| `luxury-perspective-gallery` | Luxury dark portfolio, 3D horizontal carousel, premium agency work showcase, cyber-minimal gallery slider | `templates/luxury-perspective-gallery/LuxuryPerspectiveGallery.tsx`, `LuxuryPerspectiveGalleryPanDepth.tsx`, `Root.snippet.tsx` |
| `charity-doodle-poster` | Editorial nonprofit poster, rough ink animal illustration, line-boil stop-motion texture, hand-drawn web hero | `templates/charity-doodle-poster/CharityDoodlePoster.tsx`, `Root.snippet.tsx` |

## `luxury-perspective-gallery`

Variants:

- `ring-carousel` / `LuxuryPerspectiveGallery`: centered carousel ring with overlapping cards.
- `pan-depth-stage` / `LuxuryPerspectiveGalleryPanDepth`: loopable stage based on the supplied browser reference video. Cards mostly face the camera; each featured card holds for about 2 seconds, alternates between left and right focal positions, then slides forward and out to that side while the next card grows from the background into focus. Depth comes from scale, blur, and layered z-index rather than strong card rotation or side-entry motion.

Visual target:

- Dark navy / charcoal space gradient with indigo glow and perspective grid floor.
- Minimal centered `鱼亦乐` brand mark.
- `ring-carousel`: centered horizontal project-card carousel.
- `pan-depth-stage`: flat-facing cards distributed across a horizontal stage; hold frames alternate a large left / right focal card with the next card on the opposite side, the exiting focal card moves forward off the left / right edge, and the deepest card starts near the central vanishing point.
- Bottom `SAY HELLO` neon pill.
- Cards interpolate horizontal position, size, opacity, blur, and z-index from `useCurrentFrame()`.
- Card examples: SummerRain packaging, Landlord Dashboard, Wunderflats App.

Technical rules:

- This template uses Tailwind class names for static layout and surface styling.
- The Remotion project must import Tailwind in `src/index.css`:
  ```css
  @import "tailwindcss";
  ```
- Do not use Tailwind animation utilities.
- Main motion must remain frame-driven with `useCurrentFrame()`, `interpolate()`, `spring()`, and `Easing`.
- Keep 16:9 composition at `1920x1080`; use `fps=60` for this template unless the project requires 30fps.
- If the Remotion project was created without Tailwind, add Tailwind support before copying this template, or translate static class names into CSS while preserving the frame-driven animation logic.

Copy pattern:

1. Copy the chosen variant TSX into `remotion/src/`.
2. Register it in `src/Root.tsx` using the values from `Root.snippet.tsx`.
3. Run `npm run lint`.
4. Render still checks around frames `0`, `120`, `168`, `336`, `504`, and `671` for `pan-depth-stage`.

Suggested still check:

```bash
npx remotion still LuxuryPerspectiveGallery --frame=90 --scale=0.5 --output=preview-stills/luxury-gallery-090.png
```

## `charity-doodle-poster`

Visual target:

- Solid retro background colors, defaulting to pale zoo yellow `#E8F582`.
- Huge black headline as SVG text. Keep text and illustration in the same filtered SVG group so the title line-boil matches the animal drawing.
- Organic custom `O` forms in `ZOO`, drawn as rough overlapping ellipses rather than regular font glyphs.
- Minimal left editorial paragraph block and white circular plus button.
- Giant black ink-brush animal illustration entering from the center and bottom of the frame.

Motion / texture rules:

- Use the SVG `line-boil` filter in the template: `feTurbulence` + `feDisplacementMap` for organic shaking, then `feGaussianBlur` + `feComponentTransfer` for rough ink edges.
- Bind `feTurbulence.seed` to `Math.floor(frame / 3)` or a similarly stepped value. Do not update the seed every frame.
- Wrap headline, paragraph, and illustration in one filtered `<g>` so the whole poster shares the same stop-motion hand-drawn language.
- Do not use CSS animation or Tailwind animation utilities.

Built-in palette ids:

- `zoo-yellow`
- `sky-blue`
- `soft-peach`
- `lime-green`
- `rose-pink`

Suggested still checks:

```bash
npx remotion still CharityDoodlePoster --frame=0 --scale=0.5 --output=preview-stills/charity-doodle-000.png
npx remotion still CharityDoodlePoster --frame=42 --scale=0.5 --output=preview-stills/charity-doodle-042.png
npx remotion still CharityDoodlePoster --frame=96 --scale=0.5 --output=preview-stills/charity-doodle-096.png
```
