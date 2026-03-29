# 2026-03-29 Adaptive Image Height Design

## Goal

Make rendered news images use a fixed width of `1200px` and a content-driven height.

When news content is short:
- the overall image height should become shorter
- the gap between the last news item and the quote section should remain fixed

When news content is long:
- the overall image height should become taller
- the same fixed layout gaps should still hold

## Current Problem

The current template uses a fixed card height and fixed grid rows.
That forces empty vertical space to accumulate when the news list is short.
As a result, the distance between the last news item and the quote section grows unexpectedly.

## Chosen Approach

Use natural document flow instead of a fixed-height card.

Keep:
- fixed card width: `1200px`
- existing visual style
- existing quote and footer sections

Change:
- remove fixed card height
- remove fixed grid row heights
- let the content section expand only as much as the news list needs
- keep quote and footer as normal blocks below the content
- continue screenshotting the `#news-card` element with Playwright

## Layout Rules

The following distances should remain fixed regardless of content length:
- header bottom to first news item top: `8px`
- last news item bottom to quote top: `8px`
- quote container bottom to footer container top: `8px`
- footer second-line text bottom to page bottom: `10px`

The card height should be the sum of:
- header height
- content height
- quote block height
- footer height

## Implementation Changes

### Template

In `app/infrastructure/render/templates/base.html`:
- remove fixed `height: 1800px` from `#news-card`
- replace fixed `grid-template-rows` layout with content-driven layout
- ensure `#news-card` uses natural height
- keep `width: 1200px`
- preserve current approved spacing values

### Renderer

In `app/infrastructure/render/playwright_image_renderer.py`:
- stop assuming a fixed final card height
- keep element screenshotting via `locator('#news-card').screenshot(...)`
- keep a large enough page viewport for initial rendering

No image post-processing behavior should change.

### Tests

Add or update tests to verify:
- rendered HTML still contains required sections
- short and long content both render successfully
- rendered PNG dimensions vary in height for different content lengths

## Validation

Render at least:
- `2026-03-27.json`
- `2026-03-29.json`

Expected result:
- `2026-03-29` image height should be greater than `2026-03-27` if its content is longer
- the last news item to quote gap should remain visually fixed
- footer bottom spacing should remain stable

## Scope Notes

This change is limited to image rendering layout behavior.
It does not change:
- data fetching
- article parsing
- JSON schema
- image width
- overall visual theme
