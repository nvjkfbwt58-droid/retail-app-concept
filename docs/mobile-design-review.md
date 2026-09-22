# Mobile experience review — revision 04

## Findings
The previous mobile screen gave almost all of the first viewport to a loyalty card. Repeated pale rounded containers, tiny uppercase labels and decorative bottle circles created a monotonous hierarchy. Layered CSS and overlapping entrance/press/parallax animation created inconsistent motion. The original mobile layout also retained simulated device chrome and allowed catalog overflow; those fixes are preserved.

## Implemented direction
A store context header, one editorial photographic hero, a compact warm-gold membership pass with a directly usable barcode, three lightweight shortcuts, a personal coupon and tailored recommendations. Product imagery is separated from typography instead of wrapping every item in another white card. Price, style and specifications have a clear reading order. A dark contained navigation bar sits fully inside the viewport. Detail sheets, benefits and profile use the same palette and typography.

## Motion contract
Single 300ms opacity/10px screen entry, 110ms press with 220ms release, sliding active-tab indicator, 280ms sheet opening and downward dismissal. Press is cancelled when the user scrolls. No cloned pages, pointer image parallax, staggered catalog animation, or idle animation loop. Hidden tabs and reduced-motion cancel active effects.

## References
- Apple Human Interface Guidelines, Motion: https://developer.apple.com/design/human-interface-guidelines/motion
- Google, Making Motion Meaningful: https://design.google/library/making-motion-meaningful
- Google, Expressive Material Design research: https://design.google/library/expressive-material-design-google-research

These are design principles, not evidence of a claim to be the best app on the market. Actual iPhone hardware performance needs device testing; responsive browser checks do not establish frame rates.

## Verification
- Responsive WebKit preview at 390×844 and 320×568.
- Catalog and benefits scrollWidth equals clientWidth; navigation stays within viewport.
- Hero title and action do not overlap at 320px.
- Product sheet open/close, loyalty barcode dialog, coupon presence and catalog search checked.
- No browser console errors in these scenarios; JavaScript syntax checks passed.
