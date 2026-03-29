# Adaptive Image Height Implementation Plan

1. Replace fixed-height card grid with natural-flow layout so card height is content-driven.
2. Keep key spacing invariant: last news item border to quote top border is 8px.
3. Preserve existing quote/footer visual rules while letting locator screenshot capture actual element height.
4. Add regression tests for generated HTML/CSS contract around adaptive layout.
