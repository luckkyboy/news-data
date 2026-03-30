# Pages Theme-Matched Split Preview Design

## Goal

Replace the current Pages preview UI with a two-pane preview workspace that keeps the rendered image as the primary artifact, shows JSON in a secondary scrollable inspector, and visually matches the same seven weekday themes used by the render template.

## Layout

The page is split into two primary regions:
- Left: image preview stage
- Right: JSON inspector

Desktop keeps a persistent two-column layout with the image column wider than the JSON column. Mobile collapses to a single-column flow with the image stage first and the JSON inspector below it.

The image stage must always prioritize full image visibility within the current viewport. The JSON inspector may scroll internally.

## Visual Direction

The page should no longer use the dark gallery-console aesthetic. It should derive its background, panel, border, accent, and text colors from the same weekday theme palette used in `app/infrastructure/render/templates/base.html`.

The page should feel like a companion surface for the rendered card rather than a separate product. That means:
- theme-tinted page background
- light, warm panels derived from the selected theme
- shared accent color for buttons, active date chip, and section details
- reduced contrast between page chrome and preview image container

## Theme Rules

Theme selection follows the existing weekday mapping:
- Monday: `cool`
- Tuesday: `forest`
- Wednesday: `navy`
- Thursday: `terracotta`
- Friday: `rose`
- Saturday: `warm`
- Sunday: `citrus`

Pages should compute the active theme from the selected document date and apply it via `body[data-theme="..."]`.

## Components

### Preview Stage
- Contains the existing preview controls: previous day, next day, open image, open JSON.
- Displays the selected date and a small `NEWS DATA` label.
- Uses a single large framed surface whose main job is to keep the image fully visible.

### JSON Inspector
- Displays basic metadata summary near the top.
- Displays raw JSON in a scrollable `pre` block below.
- Remains secondary in hierarchy, with less visual weight than the preview stage.

### Date Rail
- Replaced with a compact date strip embedded in the JSON column header.
- Keeps date switching available without becoming a separate third panel.

## Responsive Behavior

Desktop:
- Two columns.
- Image column gets most width.
- JSON column has a fixed readable width and scrolls internally.

Mobile:
- Single column.
- Image preview first and still sized to remain fully visible.
- JSON inspector below, scrollable.
- Date list becomes a horizontal wrap or scroll strip.

## Testing

Update the Pages contract test to assert:
- split preview shell exists
- preview image and JSON panel exist
- the page uses `body[data-theme]`
- CSS includes `object-fit: contain`
- responsive breakpoint for mobile layout exists
