# YYL Remotion Video

An agent skill for Claude Code, Codex, and similar local coding-agent environments. It turns articles, scripts, notes, or clear outlines into **16:9 Remotion video projects** with frame-accurate animation and direct mp4 rendering.

This skill is Remotion-only. It does not create click-driven web presentations and does not synthesize voiceover. The agent estimates video duration from narration length and visual complexity; voiceover, subtitles, and audio mixing are left for post-production.

It includes one copyable Remotion template:

- **luxury-perspective-gallery**: a dark, high-end 3D horizontal portfolio carousel for product showcases, premium agency reels, and cyber-minimal interface animations.

## Install

```bash
npx skills@latest add ttfake92-lab/skills
```

Then select `yyl-remotion-video` in the interactive list.

To install only this skill into the current project:

```bash
SKILL_BASE_URL=https://github.com/ttfake92-lab/skills/tree/main npx skill skills/yyl-remotion-video
```

Or ask an AI agent with shell access:

```text
Install yyl-remotion-video for me. Run npx skills@latest add ttfake92-lab/skills, select yyl-remotion-video, then verify that SKILL.md, references/, and themes/ exist.
```

Update:

```text
Update yyl-remotion-video for me. Run npx skills@latest add ttfake92-lab/skills again and select yyl-remotion-video.
```

## Trigger Examples

```text
Use yyl-remotion-video to turn this script into a Remotion video with the command-film theme. Render still frames first, then export mp4.
```

```text
Create a product demo video from this outline using the studio-white theme. No voiceover synthesis; I will add audio later.
```

## Included Themes

| Theme | Best for | Feel |
|---|---|---|
| `command-film` | agents, terminal, automation, developer tools | dark cinematic command room |
| `studio-white` | SaaS demos, launches, courses, product tutorials | clean white product studio |
| `research-desk` | essays, reports, papers, business analysis | calm analytical desk |

## Workflow

1. Check that the user supplied source text, a script, notes, or a clear outline.
2. Choose Quick / Standard / Strict execution strength based on length and risk.
3. Save content into `article.md`, `script.md`, `outline.md`, and `notes.md`.
4. Reuse an existing `remotion/` project, or create one only when missing.
5. Select one bundled theme. Do not import themes from other skills.
6. Read `references/TEMPLATES.md` when the user asks for a known visual mechanism such as `luxury-perspective-gallery`.
7. Build frame-driven animation with `useCurrentFrame()`, `interpolate()`, `Easing`, and `Sequence`.
8. Run `npm run lint`, render still checks, then render mp4.

## Fits / Does Not Fit

Fits:

- mp4-first short videos, explainers, launch clips, and UI/terminal motion pieces.
- Frame-accurate text, code, UI, data-flow, and diagram animations.
- Silent video workflows where audio is added in post.

Does not fit:

- Click-to-advance browser presentations.
- In-skill voiceover synthesis.
- Full content invention from only a vague topic.

## License

MIT. See the repository license.
