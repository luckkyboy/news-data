# Seven-Day Theme Palette Design

## Goal
Extend the current structured template to support seven weekday-driven color themes without duplicating layout templates.

## Themes
- Monday: cool
- Tuesday: forest
- Wednesday: navy
- Thursday: terracotta
- Friday: rose
- Saturday: warm
- Sunday: citrus

## Constraints
- Keep one HTML/CSS layout system.
- Only theme visual tokens; do not fork spacing, typography, or layout logic.
- Preserve current adaptive-height rendering behavior.

## Rendering
- Template context computes `theme_name` from `document.date`.
- `base.html` keeps default tokens and adds `body[data-theme="..."]` overrides.

## Validation
- Unit tests cover weekday-to-theme mapping and presence of theme tokens.
- Generate preview images with the same JSON data across all themes for side-by-side review.
