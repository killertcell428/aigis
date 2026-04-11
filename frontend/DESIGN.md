# Design System: Aigis

## Concept: "Linear Precision x Sentry Warmth"
Linear's ultra-precise dark-mode engineering meets Sentry's warm purple personality.
A security dashboard that feels like a high-end control room — not a generic SaaS template.

## 1. Visual Theme

- **Dark-mode native** with warm purple-black canvas
- **Inter Variable** with OpenType `"cv01", "ss03"` — geometric, precise
- Ultra-thin semi-transparent borders (Linear) + inset shadow buttons (Sentry)
- Single accent: guardian violet for CTAs, muted emerald for "safe" status
- Frosted glass panels for overlays (Sentry)

## 2. Color Palette

### Backgrounds
- `--bg-deep`: `#0d0b14` — deepest canvas (page bg)
- `--bg-panel`: `#13111c` — sidebar, panels
- `--bg-surface`: `#1a1726` — cards, elevated surfaces
- `--bg-elevated`: `#231f30` — hover states, dropdowns

### Text
- `--text-primary`: `#f0f0f3` — headings, primary content
- `--text-secondary`: `#a8a3b8` — body, descriptions
- `--text-muted`: `#6b6580` — placeholders, timestamps
- `--text-dim`: `#4a4460` — disabled, de-emphasized

### Brand Accent
- `--accent`: `#7c6af6` — primary CTA, active nav, links
- `--accent-hover`: `#9585ff` — hover on accent elements
- `--accent-muted`: `#5a4db8` — subtle accent backgrounds
- `--accent-glow`: `rgba(124, 106, 246, 0.15)` — glow behind accent elements

### Status (Security-specific)
- `--status-safe`: `#27a644` — allowed, safe, low risk
- `--status-safe-bg`: `rgba(39, 166, 68, 0.12)`
- `--status-warn`: `#e5a820` — medium risk, pending review
- `--status-warn-bg`: `rgba(229, 168, 32, 0.12)`
- `--status-danger`: `#ef4444` — blocked, critical risk
- `--status-danger-bg`: `rgba(239, 68, 68, 0.12)`
- `--status-info`: `#6b9fff` — informational
- `--status-info-bg`: `rgba(107, 159, 255, 0.10)`

### Borders
- `--border-subtle`: `rgba(255, 255, 255, 0.06)` — default card/section borders
- `--border-standard`: `rgba(255, 255, 255, 0.10)` — inputs, prominent separators
- `--border-accent`: `rgba(124, 106, 246, 0.3)` — active/focused elements

## 3. Typography

Font: `Inter Variable` with `font-feature-settings: "cv01", "ss03"`
Mono: `"Berkeley Mono", ui-monospace, "SF Mono", Menlo, monospace`

| Role | Size | Weight | Letter-spacing | Line-height |
|------|------|--------|----------------|-------------|
| Display | 36px | 580 | -1.2px | 1.1 |
| H1 | 24px | 580 | -0.6px | 1.25 |
| H2 | 18px | 560 | -0.3px | 1.3 |
| H3 | 15px | 540 | -0.15px | 1.4 |
| Body | 14px | 400 | normal | 1.5 |
| Body emphasis | 14px | 520 | normal | 1.5 |
| Caption | 12px | 440 | normal | 1.4 |
| Micro | 10px | 500 | 0.3px | 1.3 |

## 4. Components

### Buttons
- **Primary**: `bg: var(--accent)`, text white, radius 8px, `box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), 0 1px 3px rgba(0,0,0,0.3)` (Sentry tactile)
- **Ghost**: `bg: rgba(255,255,255,0.03)`, border `var(--border-subtle)`, radius 8px
- **Danger**: `bg: rgba(239,68,68,0.15)`, text `#ef4444`, radius 8px

### Cards
- `bg: var(--bg-surface)`, border `1px solid var(--border-subtle)`, radius 12px
- Hover: border transitions to `var(--border-standard)`

### Stat Cards
- Same as card, plus left-accent border (4px) in status color
- No colored background fill — accent is border-only

### Badges (Risk levels)
- Pill shape (radius 9999px), padding 2px 10px
- Background: status-*-bg, text: status-* color

### Inputs
- `bg: rgba(255,255,255,0.03)`, border `var(--border-standard)`, radius 8px
- Focus: border `var(--border-accent)`, glow `0 0 0 3px var(--accent-glow)`

### Navigation (Sidebar)
- `bg: var(--bg-panel)`, border-right `1px solid var(--border-subtle)`
- Active item: `bg: var(--accent-glow)`, left-border 2px accent, text lighter
- Hover: `bg: rgba(255,255,255,0.04)`
- Icons: Lucide icons (not emoji)

## 5. Depth & Elevation

| Level | Shadow |
|-------|--------|
| Flat | none |
| Surface | `0 1px 2px rgba(0,0,0,0.2)` |
| Card | `0 2px 8px rgba(0,0,0,0.25), 0 0 0 1px var(--border-subtle)` |
| Elevated | `0 8px 24px rgba(0,0,0,0.35)` |
| Inset (buttons) | `inset 0 1px 0 rgba(255,255,255,0.12), 0 1px 3px rgba(0,0,0,0.3)` |

## 6. Charts (Recharts)
- Bar fill: `var(--accent)` (#7c6af6)
- Grid stroke: `rgba(255,255,255,0.06)`
- Axis text: `var(--text-muted)` (#6b6580)
- Tooltip: `bg: var(--bg-elevated)`, border subtle, text primary
- Pie colors: safe/warn/danger status colors

## 7. Do's and Don'ts

### Do
- Use Inter Variable with `"cv01", "ss03"` on ALL text
- Use weight 520-580 range (between regular and semibold) for emphasis
- Keep backgrounds warm purple-black, never pure black or cool gray
- Use semi-transparent white borders, not solid colors
- Use inset shadows on primary buttons (Sentry tactile feel)
- Use Lucide icons — no emoji in the UI
- Use status colors only for actual status indication

### Don't
- Don't use slate/sky/blue from Tailwind defaults — this is a purple system
- Don't use pure white (#fff) backgrounds — darkest surface is #1a1726
- Don't use emoji icons — Lucide provides the professional look
- Don't use weight 700 — max is 580
- Don't introduce warm colors (orange/yellow) except for status-warn
