# Remotion Templates

Templates are bundled TSX starting points. Use them when the user asks for a
specific visual mechanism, not as general themes.

## Included Templates

| id | Use When | Files |
|---|---|---|
| `luxury-perspective-gallery` | Luxury dark portfolio, 3D horizontal carousel, premium agency work showcase, cyber-minimal gallery slider | `templates/luxury-perspective-gallery/LuxuryPerspectiveGallery.tsx`, `LuxuryPerspectiveGalleryPanDepth.tsx`, `Root.snippet.tsx` |

## `luxury-perspective-gallery`

Variants:

- `ring-carousel` / `LuxuryPerspectiveGallery`: centered carousel ring with overlapping cards.
- `pan-depth-stage` / `LuxuryPerspectiveGalleryPanDepth`: loopable stage based on the supplied browser reference video. Cards mostly face the camera; each featured card holds for about 2 seconds, then a smooth lateral pan moves the next card into focus. Depth comes from large offscreen cropping, scale, blur, and layered z-index rather than strong card rotation.

Visual target:

- Dark navy / charcoal space gradient with indigo glow and perspective grid floor.
- Minimal header: left index pill, centered Roman profile, right Subscribe button.
- `ring-carousel`: centered horizontal project-card carousel.
- `pan-depth-stage`: flat-facing cards distributed across a horizontal stage; huge cards slide partly off the left / right edges as the camera pans, with a 2-second hold per card and a seamless loop.
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
