# Remotion Themes

These themes belong to `yyl-remotion-video` only.
Do not import or reference themes from `web-video-presentation`.

Each theme contains:

```
themes/<id>/
├── theme.json
└── tokens.css
```

Use `theme.json` for selection and narrative fit. Use `tokens.css` as the source
for palette, typography, spacing, borders, and surface treatment. In a Remotion
project, copy only the selected theme's relevant variables into `src/index.css`
or a local theme file.

## Included Themes

| id | nameZh | Use When |
|---|---|---|
| `command-film` | 命令行电影 | Agents, Claude/Codex, terminal, automation, developer tools |
| `studio-white` | 白棚发布 | Product launches, SaaS demos, courses, polished tutorials |
| `research-desk` | 研究桌面 | Essays, reports, papers, business analysis, research explainers |

## Selection Heuristics

- Choose `command-film` when the content is about tools doing work on a computer.
- Choose `studio-white` when the content needs product confidence and clean polish.
- Choose `research-desk` when the content is analytical, long-form, or evidence-heavy.

## Remotion Adaptation

The CSS variables are safe to copy, but do not copy CSS keyframes or web-player
assumptions. Remotion animation should stay in TSX through frame interpolation.
