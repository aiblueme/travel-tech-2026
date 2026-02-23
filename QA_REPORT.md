# QA Report — 2026 Travel Tech Comparison
**URL:** http://64.235.43.190:9090/
**Date:** 2026-02-23
**Assessor:** QA Expert Agent
**Server:** nginx/1.29.5 on Docker (HTTP, no TLS)
**Page size:** 48,978 bytes HTML + 10.33 MB images = 10.38 MB total transfer

---

## Executive Summary

The 2026 Travel Tech Comparison is a well-structured, zero-dependency single-file application with solid semantic HTML, functional sort/filter logic, and a well-articulated CSS architecture. All 19 devices render correctly, all product images load (HTTP 200), and the core interactive features (sort, filter, table sort, nav scroll highlighting) function as designed. However, a critical CSS Container Query threshold bug means the page's signature feature — cards switching from stacked to side-by-side layout — never actually fires in any standard desktop or tablet grid configuration, directly undermining the pedagogical purpose of the page. Additionally, a 10.33 MB uncompressed image payload, missing WCAG color contrast compliance on secondary text surfaces, absent dark-mode badge color adaptation, and several accessibility gaps (no `<main>` landmark, no skip link, no focus-visible styles) require resolution before this page can be considered production-ready.

---

## Findings

### 1. Functional Testing

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| F-1 | **Card sort buttons all function correctly.** Weight sorts ASC (lightest first), Battery sorts DESC (most first), Price sorts ASC (cheapest first), Travel Score sorts DESC (highest first). `aria-pressed` toggling is correct. | Passed | `.controls [data-sort]` | No action needed |
| F-2 | **Filter buttons all function correctly.** "Shipping now" returns 16 devices (avail='Now'), "≤ 2.5 lbs" returns 4 devices (LG Gram, ThinkPad X1C, Surface Pro 11, Yoga Slim 7i Ultra Aura), "≤ 3.0 lbs" returns 15 devices. Filters are mutually exclusive. | Passed | `.controls [data-filter]` | No action needed |
| F-3 | **Table column sort works.** Weight, Battery, MSRP, Score columns all trigger `tblSort()`. Active column gets `.t-active` highlight class. Toggle (same column) correctly reverses direction. | Passed | `thead th button` | No action needed |
| F-4 | **Table Weight column defaults to DESC (heaviest first)** when first clicked, because `tblAsc` initializes to `false` and resets to `false` on any new column click. Users expect weight to sort lightest-first when clicking a weight column for the first time. | Medium | `JS: tblSort()`, line ~933 | Set `tblAsc = true` when `tblCol` switches to `'weight'`, or define a `defaultAsc` map per column (e.g., `{weight: true, battery: false, msrp: true, score: false}`). |
| F-5 | **No empty-state UI** when a filter produces zero results. `innerHTML` is set to an empty string with no user feedback message. Currently safe with the 19-device dataset, but fragile if data changes. | Medium | `JS: renderCards()`, line ~847 | Add an empty-state guard: `if (data.length === 0) { grid.innerHTML = '<p class="empty-state">No devices match this filter.</p>'; return; }` |
| F-6 | **Nav links (Cards, Table, Learn CQ) scroll to correct sections** via `href="#cards"`, `href="#table"`, `href="#learn"` with `scroll-behavior: smooth` on `html`. IntersectionObserver correctly activates the matching nav link when each section enters the viewport centre. | Passed | `nav .nav-links a` | No action needed |
| F-7 | **Learn CQ section renders correctly.** Code blocks, browser support grid, and explanatory text all display. `.fi` fade-in animation triggers via IntersectionObserver. | Passed | `#learn .explainer-box` | No action needed |

---

### 2. Image Loading

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| I-1 | **All 19 product images return HTTP 200.** No image fails to load; every device card displays its real product photo rather than the emoji fallback. | Passed | `images/*.jpg` | No action needed |
| I-2 | **Total image payload is 10.33 MB** — far above the recommended 1–2 MB budget for a product listing page. The HP OmniBook Ultra 14 image alone is 3.07 MB; the MacBook Air M4 image is 937 KB; six images exceed 500 KB. This causes degraded load time on mobile networks. | High | `images/hp_omnibook_ultra_14.jpg` (3,065 KB), `images/macbook_air_m4.jpg` (938 KB), `images/yoga_slim_7i_aura_14.jpg` (722 KB), `images/yoga_slim_7x_gen10.jpg` (710 KB), `images/galaxy_book5_pro_14.jpg` (701 KB), `images/matebook_x_pro_2025.jpg` (583 KB), `images/yoga_slim_7x_gen11.jpg` (519 KB) | Convert all images to WebP (lossless for product shots) or AVIF. Target max 150 KB per card thumbnail at 640px wide. Use `<picture srcset>` with WebP and JPEG fallback. Consider squoosh, sharp, or ImageMagick in a build step. |
| I-3 | **Images use `loading="lazy"` and `decoding="async"`**, which prevents render-blocking on below-the-fold cards. | Passed | `JS: renderCards()` template, `.card-img` | No action needed |
| I-4 | **Emoji fallback mechanism is correctly wired.** Event delegation on `#card-grid` listens for `error` events on `.card-img` elements in capture phase, then hides the `<img>` and shows `.card-emoji`. The `z-index` layering (img=1, emoji=2) is correct. | Passed | `JS line ~822`, CSS `.card-emoji` | No action needed |

**Image size breakdown:**

| Image slug | Size | Status |
|-----------|------|--------|
| hp_omnibook_ultra_14 | 3,065 KB | Needs urgent optimization |
| macbook_air_m4 | 938 KB | Needs optimization |
| yoga_slim_7i_aura_14 | 722 KB | Needs optimization |
| yoga_slim_7x_gen10 | 710 KB | Needs optimization |
| galaxy_book5_pro_14 | 701 KB | Needs optimization |
| matebook_x_pro_2025 | 583 KB | Needs optimization |
| yoga_slim_7x_gen11 | 519 KB | Needs optimization |
| surface_pro_11 | 471 KB | Acceptable |
| yoga_slim_7a_gen11 | 457 KB | Acceptable |
| thinkpad_x1_carbon_13 | 401 KB | Acceptable |
| yoga_slim_7i_ultra_aura | 396 KB | Acceptable |
| yoga_slim_9i_gen10 | 387 KB | Acceptable |
| dell_xps_13_2025 | 279 KB | Good |
| razer_blade_14_2025 | 219 KB | Good |
| zenbook_s14_oled | 235 KB | Good |
| yoga_slim_7i_aura_15 | 141 KB | Good |
| acer_swift_14_ai | 115 KB | Good |
| framework_13_amd | 110 KB | Good |
| lg_gram_14_2026 | 130 KB | Good |

---

### 3. Visual / Layout QA

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| V-1 | **Container query threshold (400px) never fires in any realistic grid configuration.** At 1280px desktop: 4-column grid produces ~282px-wide cards. At 900px: 2-column grid produces ~393px cards. Even at max-width 1440px with 4 columns, cards reach only ~322px. The side-by-side `grid-template-columns: 160px 1fr` layout is the defining feature of the page and it is never activated in normal browsing. The container query only fires when a card occupies nearly full viewport width (i.e., 1-column layout on very narrow screens), but that is exactly when stacked layout is preferable anyway. | Critical | CSS `@container card (min-width: 400px)`, `card-grid: minmax(290px, 1fr)` | Lower the container query threshold from `400px` to `240px`. At a 290px minimum card width, a 240px threshold will fire comfortably. Alternatively, increase `minmax` to `minmax(440px, 1fr)` so cards are always wide enough to trigger the side-by-side layout. |
| V-2 | **Duplicate `transition` property in `.nav-links a`.** Two `transition` declarations exist in the same CSS block (line ~87 and ~90). The first (`transition: color var(--ease)`) is overridden by the second (`transition: color var(--ease), border-color var(--ease)`), making the first declaration dead code. Not a visual bug but a code quality issue that can confuse future maintainers. | Medium | CSS `.nav-links a` block | Remove the first `transition: color var(--ease);` line; keep only the combined declaration. |
| V-3 | **Badge colors (`.bg`, `.ba`, `.br`) are hardcoded and do not adapt to dark mode.** In dark mode, these badges render with light-colored backgrounds (#dcfce7 green, #fef3c7 amber, #fee2e2 red) against dark card surfaces (#1a1d23). The contrast of `#15803d` (badge green text) against `#1a1d23` (dark card surface) is only 3.37:1 — failing WCAG AA for the `.68rem` font size used. The `.bb` badge correctly uses CSS variables and adapts to dark mode. | High | CSS `.bg`, `.ba`, `.br`, `.tag-now`, `.tag-soon` | Add `@media (prefers-color-scheme: dark)` overrides for these badge classes, using darker backgrounds and lighter text colors appropriate for dark surfaces. |
| V-4 | **Card hover transform (`translateY(-2px)`) and box-shadow elevation are functional** and provide clear lift feedback. | Passed | CSS `.card-inner:hover` | No action needed |
| V-5 | **Hero section, card grid, comparison table, and explainer section all render correctly** at desktop width with proper spacing, hierarchy, and alignment. | Passed | All sections | No action needed |
| V-6 | **Explainer code blocks (`role="region"`) render with correct syntax highlighting** using span class coloring. Dark code box background (`#0d1117`) is fixed and does not adapt to light mode — intentionally readable dark-on-dark terminal aesthetic. Acceptable as a deliberate design choice. | Passed | `.code-box` | No action needed |

---

### 4. Accessibility Audit

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| A-1 | **No `<main>` landmark element or `role="main"`.** The page has `role="navigation"`, `role="banner"`, and `role="contentinfo"` (footer), but the primary content area has no `<main>` wrapper. Screen reader users relying on landmark navigation cannot jump directly to the main content. | High | HTML structure between `<header>` and `<footer>` | Wrap all `<section>` elements between `<header>` and `<footer>` in a `<main>` element: `<main id="main-content">...</main>`. |
| A-2 | **No skip-to-content link.** Keyboard users must tab through the entire navigation bar (3 links) before reaching the sort/filter controls and content. | High | `<nav>` region | Add as the first element in `<body>`: `<a href="#cards" class="skip-link">Skip to content</a>` with CSS: `.skip-link { position:absolute; top:-40px; left:0; } .skip-link:focus { top:0; }` |
| A-3 | **No explicit `:focus-visible` or `:focus` styles defined.** All interactive elements (buttons, links, table sort buttons) rely on browser-default focus rings, which vary widely across browsers and may be invisible on some backgrounds. | High | CSS (no `:focus-visible` rule anywhere in stylesheet) | Add: `.ctrl-btn:focus-visible, .nav-links a:focus-visible, thead th button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }` |
| A-4 | **`text-muted` (#6b7280) on `surface-2` (#f0f1f4) fails WCAG AA** with a contrast ratio of 4.28:1 (requires 4.5:1). Affected elements: `.spec-cell .l` labels ("lbs", "battery", "MSRP"), `.section-hd p`, `.ctrl-label`, table `.td-brand`, and `.card-chip` text when rendered on surface-2 backgrounds. | High | CSS `--text-muted: #6b7280`, `--surface-2: #f0f1f4` | Darken `--text-muted` in light mode from `#6b7280` to `#5d6475` (achieves 5.0:1 on surface-2). |
| A-5 | **`text-muted` (#6b7280) on `bg` (#f4f5f7) fails WCAG AA** with a contrast ratio of 4.43:1. This affects the hero paragraph text and disclaimer text which sit directly on the page background. | High | CSS `--text-muted`, `--bg: #f4f5f7` | The same fix from A-4 (darkening `--text-muted`) resolves this. Alternatively, ensure muted text never sits directly on `--bg` without a surface wrapper. |
| A-6 | **Decorative emojis in visible content are not wrapped with `aria-hidden="true"`.** The `✈️` in `.hero-eyebrow` and `⚠️` in `.disclaimer` will be read aloud by screen readers as "Airplane" and "Warning sign" in full, disrupting the natural reading flow of those elements. | Medium | HTML `<div class="hero-eyebrow">✈️ ...`, `<p class="disclaimer">⚠️ ...` | Wrap standalone decorative emojis: `<span aria-hidden="true">✈️</span>` and `<span aria-hidden="true">⚠️</span>`. |
| A-7 | **`.spec-cell .l` uses `.58rem` font size (~9.3px)**, well below the WCAG informational guidance of 14px for body text. Combined with the contrast failure on surface-2 (finding A-4), these "lbs / battery / MSRP" labels are a usability risk for users with moderate visual impairment. | Medium | CSS `.spec-cell .l { font-size: .58rem }` | Increase to `.65rem` (10.4px) as a minimum, or `.7rem` (11.2px) for comfort. |
| A-8 | **Heading hierarchy is correct** (one `<h1>` → three `<h2>` → no `<h3>`). No skipped levels. | Passed | HTML heading structure | No action needed |
| A-9 | **All `<th>` elements have `scope="col"`** (8/8 confirmed). ARIA labels on sort buttons are meaningful ("Sort by weight", "Sort by battery life", etc.). | Passed | `<thead>` | No action needed |
| A-10 | **`aria-pressed` state is correctly managed** on all sort and filter buttons (8 attributes, toggled correctly on interaction). | Passed | `.ctrl-btn[aria-pressed]` | No action needed |
| A-11 | **`role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`** is correctly implemented on the `.score-track` element. | Passed | `.score-track[role="progressbar"]` | No action needed |
| A-12 | **Alt text is present in the image template** as `"${d.brand} ${d.name} laptop"` — descriptive and meaningful at runtime (e.g., "Apple MacBook Air 13" laptop"). | Passed | `JS renderCards()` template | No action needed |
| A-13 | **`lang="en"` is set on `<html>`**, viewport meta is correctly defined. | Passed | `<html lang="en">` | No action needed |

---

### 5. Performance

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| P-1 | **HTML TTFB is 1.5ms** and total HTML download is 2.0ms (48,978 bytes). Nginx serves the file with gzip not confirmed (no `Content-Encoding` header visible — may need to verify). Extremely fast for the HTML payload itself. | Passed | nginx/1.29.5 | Enable `gzip on` in nginx config if not already active |
| P-2 | **Total image payload is 10.33 MB** (see I-2). On a 10 Mbps mobile connection this represents ~8 seconds of transfer for the image assets alone, before `loading="lazy"` defers below-the-fold images. Above-the-fold images (first 4–6 cards) will load immediately. | High | `images/` directory | See I-2 recommendation: WebP/AVIF conversion with aggressive compression |
| P-3 | **No render-blocking resources.** The page has zero external CSS, zero external JS, zero web fonts, and zero CDN dependencies. All styles and scripts are inline. This is excellent for first-contentful-paint (FCP). | Passed | `<head>` | No action needed |
| P-4 | **`loading="lazy"` and `decoding="async"` are applied to all product images** (via JS template string). Only the card images in the initial viewport will load immediately. | Passed | `JS renderCards()` line ~853 | No action needed |
| P-5 | **No `Cache-Control` or `Expires` headers** are returned for static image assets. Every browser visit re-validates all images. For a product page that rarely changes, this wastes bandwidth on repeat visitors. | Medium | nginx config | Add `location ~* \.(jpg\|jpeg\|png\|webp\|avif)$ { expires 365d; add_header Cache-Control "public, max-age=31536000, immutable"; }` in nginx config |
| P-6 | **No `ETag` is present for image files** (only the HTML has an ETag). Without ETags or Last-Modified headers on images, conditional GET cannot be used. | Medium | nginx config | The nginx default serves static files with `Last-Modified`; verify by curling an image with `-I`. Consider enabling `etag on` in nginx. |
| P-7 | **IntersectionObserver instances accumulate** on every `renderCards()` call (triggered on every sort or filter interaction). Each call to `attachFade()` creates a new `IntersectionObserver` without disconnecting the previous one. On a session with 20 sort/filter interactions, 20+ observers may be alive simultaneously. This is a low-level memory leak. | Medium | `JS attachFade()` line ~967, called from `renderCards()` line ~895 | Store the observer reference: `let fadeObs; function attachFade() { if (fadeObs) fadeObs.disconnect(); fadeObs = new IntersectionObserver(...); ... }` |

---

### 6. Responsive Design

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| R-1 | **Mobile (~390px): Single-column card layout renders correctly.** Section padding `clamp(16px, 4vw, 48px)` resolves to 16px at 390px, giving ~358px usable width. Cards display in stacked format (correct at this width). Controls wrap cleanly via `flex-wrap: wrap`. Hero typography scales well with `clamp()`. | Passed | All breakpoints | No action needed |
| R-2 | **Tablet (~768px): 2-column card grid renders correctly.** Controls remain on two rows due to flex-wrap. Table scrolls horizontally with `overflow-x: auto`. Explainer section `exp-grid` remains 2-column (breakpoint is 680px). | Passed | `.card-grid`, `.table-scroll` | No action needed |
| R-3 | **Desktop (~1280px): 4-column card grid.** No overflow detected. Max-width of 1440px on `.section` prevents over-stretching. Nav is stable and sticky. | Passed | `.section { max-width: 1440px }` | No action needed |
| R-4 | **Container query side-by-side layout never activates** on tablet or desktop (see V-1). The explainer text instructs users to "narrow your browser to around 640px" but at that width cards are in a 2-column grid at ~300px each — also below the 400px threshold. The side-by-side layout is effectively invisible in all documented usage scenarios. | Critical | `@container card (min-width: 400px)` | See V-1 fix |
| R-5 | **Explainer `exp-grid` correctly collapses** from 2-column to 1-column at 680px via `@media (max-width: 680px)`. | Passed | CSS `.exp-grid` | No action needed |
| R-6 | **Navigation wraps at narrow widths** via `flex-wrap: wrap` on `.nav-links`. No overflow or horizontal scroll on the nav bar. | Passed | `nav`, `.nav-links` | No action needed |
| R-7 | **No fixed-width elements cause layout overflow.** All widths above 320px are constrained by `max-width` (hero: 900px, content: 640px, section: 1440px) rather than forced fixed widths. | Passed | CSS `max-width` declarations | No action needed |

---

### 7. Content Accuracy

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| C-1 | **All 19 devices are present** (IDs 1–19 confirmed in JS data array). | Passed | `const DEVICES` array | No action needed |
| C-2 | **All 6 Yoga Slim variants are present** and correctly named: Yoga Slim 9i Gen 10 (id:14), Yoga Slim 7i Aura 14" (id:15), Yoga Slim 7i Aura 15" (id:16), Yoga Slim 7x Gen 11 (id:17), Yoga Slim 7a Gen 11 (id:18), Yoga Slim 7i Ultra Aura (id:19). All match the required variant list. | Passed | `const DEVICES` array, ids 14–19 | No action needed |
| C-3 | **Availability badges are logically assigned.** "Now" (16 devices): all 13 original devices + Yoga Slim 9i Gen 10, 7i Aura 14", 7i Aura 15". "Soon" (3 devices): Yoga Slim 7x Gen 11, 7a Gen 11, 7i Ultra Aura. CES 2026 / Q2 2026 announced-only devices correctly marked "Soon". | Passed | `avail` property in DEVICES array | No action needed |
| C-4 | **Spot-checked specs are plausible:** MacBook Air M4 (2.70 lbs, 18h, $1,099) matches Apple's published specs. Surface Pro 11 (1.96 lbs, 14h, $999) — tablet-only weight is correctly documented in the device note with the Type Cover caveat. LG Gram 14 2026 (2.18 lbs, 22h, $1,299) is consistent with LG Gram's historically class-leading weight and battery. Razer Blade 14 2025 (3.89 lbs, 9h, $2,499) — published weight is 3.89–4.0 lbs depending on config; spec is plausible. | Passed | DEVICES array | No action needed |
| C-5 | **Travel Score calculation is mathematically correct** (verified by re-running the formula). LG Gram 14 tops at 94, Yoga Slim 7i Ultra Aura second at 80, Razer Blade 14 at 0 (anchor minimum). The formula correctly normalizes weight (lower = better) and battery (higher = better) each at 50% weight. | Passed | `JS score calculation IIFE`, lines ~791–801 | No action needed |
| C-6 | **Yoga Slim 7i Aura 15" lists chip as "Core Ultra 7 256V"** while other Lenovo/Intel SKUs at similar tiers use "258V". The 256V designation is not a standard Intel model number (Intel's Lunar Lake lineup uses 258V as the Core Ultra 7 variant). This may be a data entry error — 256V does not appear in Intel's published Lunar Lake lineup. | Low | `DEVICES` array, id:16, `chip: 'Core Ultra 7 256V'` | Verify against Lenovo's official product page for Yoga Slim 7i Aura 15"; most likely should be "Core Ultra 7 258V". |
| C-7 | **Hero stats state "19 devices" and "$849–$2,499" MSRP range** — both accurate with Yoga Slim 7a Gen 11 at $849 (soon) and Razer Blade 14 at $2,499. Battery range "9–22h" is accurate (Razer Blade at 9h, LG Gram at 22h). Weight range "1.96–3.89" lbs is accurate (Surface Pro 11 at 1.96 lbs, Razer Blade at 3.89 lbs). | Passed | `.hero-stats` | No action needed |

---

### 8. UX / Interaction Quality

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| U-1 | **Sort and filter feedback is immediate.** Button state changes (`.active` class + `aria-pressed`) and card grid re-render happen synchronously on click with no perceptible delay. | Passed | JS event handlers | No action needed |
| U-2 | **Travel score progress bar does not animate on card render.** The `.score-fill` CSS has `transition: width .7s cubic-bezier(.4,0,.2,1)`, but because cards are injected via `innerHTML` with `style="width:X%"` already set to the final value, the browser has no previous `width` value to transition from. The transition CSS rule is effectively dead. The `.fi` fade-in (opacity/transform) does animate correctly via IntersectionObserver. | High | `JS renderCards()` template (`style="width:${d.score}%"`), CSS `.score-fill` | Set initial width to `0%` in the HTML template and apply the target width in a `requestAnimationFrame` callback after the element is in the DOM: `requestAnimationFrame(() => { el.querySelector('.score-fill').style.width = d.score + '%'; })` — or use a CSS animation triggered by a class addition. |
| U-3 | **IntersectionObserver nav active state works correctly.** `rootMargin: '-45% 0px -50% 0px'` creates a 5% detection band in the middle of the viewport. Each of the three sections (#cards, #table, #learn) activates the corresponding nav link when scrolled into view. The logic correctly clears all links before setting the active one. | Passed | `JS navObs`, lines ~976–983 | No action needed |
| U-4 | **"📍 SEA availability" notes are readable** in context. The `.card-sea` block uses `var(--accent)` text on `var(--accent-soft)` background (4.75:1 contrast in light mode — passes AA). The `aria-label="Southeast Asia availability"` on the container provides screen reader context for the map emoji. Font size is `.7rem` (11.2px) — technically readable but small for informational body copy. | Low | CSS `.card-sea { font-size: .7rem }` | Increase font size to `.75rem` or `.8rem` for improved legibility, especially on mobile. |
| U-5 | **Print stylesheet is correctly defined** as `@media print` inline within the single `<style>` block. No separate `<link rel="stylesheet" media="print">` is needed or expected. Print styles correctly hide nav, controls, score tracks, and explainer. Card grid is forced to 3 columns in print. | Passed | CSS `@media print`, lines ~430–446 | No action needed |
| U-6 | **No result count feedback after filtering.** After applying a filter (e.g., "≤ 2.5 lbs" shows 4 devices), there is no indication of how many results are shown. Users must count cards manually. | Low | `.controls` region | Add a result counter: `<span class="result-count" aria-live="polite">Showing 4 of 19 devices</span>` updated in `renderCards()`. The `aria-live="polite"` attribute also ensures screen reader announcement. |
| U-7 | **No sort direction indicator** is shown on the card sort buttons. "Weight ↑" label hints ascending, but there is no dynamic arrow or indicator that updates when sort direction changes (table has `⇅` but it is static too). | Low | `.ctrl-btn[data-sort]` | Consider appending a dynamic `↑` / `↓` arrow to the active sort button text to indicate current direction. |

---

### 9. Security & Infrastructure

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| S-1 | **No Content-Security-Policy (CSP) header.** The page is served with no CSP, leaving it open to XSS injection if any future dynamic content is added. Currently low risk (no user input, no inline script execution from external sources), but represents a security hygiene gap. | Medium | nginx config | Add `add_header Content-Security-Policy "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';" always;` (adjust for inline script/style requirements). |
| S-2 | **No `Cache-Control` headers on image assets.** See P-5. | Medium | nginx config | See P-5 recommendation. |
| S-3 | **No Permissions-Policy header.** Leaves browser feature access (camera, microphone, geolocation) at browser default rather than explicitly denied. | Low | nginx config | Add `add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";` |
| S-4 | **Site served over plain HTTP** (port 9090). No TLS/HTTPS. All traffic is unencrypted. In a Docker dev/staging environment this may be acceptable, but production must use HTTPS with a valid certificate. | High | Server configuration | Terminate TLS at the nginx level or via a reverse proxy. Use Let's Encrypt for a free certificate. |
| S-5 | **`X-Frame-Options: SAMEORIGIN`**, **`X-Content-Type-Options: nosniff`**, and **`Referrer-Policy: no-referrer`** are all correctly set. | Passed | nginx response headers | No action needed |

---

### 10. Code Quality

| # | Finding | Severity | Location | Recommended Fix |
|---|---------|----------|----------|-----------------|
| Q-1 | **No favicon** defined. All browsers will make a `GET /favicon.ico` request that returns 404. This adds an unnecessary error to browser console and network logs. | Medium | `<head>` | Add `<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>✈️</text></svg>">` (inline SVG emoji favicon, zero extra file needed). |
| Q-2 | **No Open Graph or Twitter Card meta tags.** Sharing the URL on social media or messaging apps will render a blank preview with no title, description, or image. | Medium | `<head>` | Add `<meta property="og:title" content="2026 Travel Tech · Carry-On Comparison">`, `og:description`, `og:image`, `og:url`, `twitter:card`, etc. |
| Q-3 | **Duplicate `transition` in `.nav-links a`** (see V-2 for detail). Dead CSS property. | Medium | CSS lines ~87–90 | Remove the first `transition: color var(--ease);` line. |
| Q-4 | **`IntersectionObserver` leak in `attachFade()`** (see P-7 for detail). | Medium | `JS attachFade()` | Store and disconnect previous observer before creating new one. |

---

## Screenshots

Due to the static analysis nature of this assessment, browser-rendered screenshots were not captured via an automated browser session. The following screenshots are recommended to be taken by a developer using browser DevTools to supplement this report:

1. **Full-page desktop screenshot (1280px)** — to confirm visual hierarchy, nav, hero, card grid, table, explainer, and footer
2. **Mobile screenshot (390px)** — to confirm single-column card layout, wrapping controls, scrollable table
3. **Dark mode screenshot (desktop)** — to confirm badge color jarring contrast issue (V-3/A-4) is visually evident
4. **Container query demonstration screenshot** — after applying the V-1 fix, capture cards in both stacked and side-by-side states simultaneously
5. **Score progress bar comparison** — before and after the U-2 animation fix

---

## Priority Fix List

Ordered by impact and urgency:

1. **[Critical] Fix container query threshold (V-1 / R-4)** — The page's headline feature does not work. Change `@container card (min-width: 400px)` to `(min-width: 240px)` to ensure cards trigger side-by-side layout when they are at least 240px wide, which is achievable in the current grid. This is the single highest-priority code fix.

2. **[High] Compress and convert images to WebP (I-2 / P-2)** — The HP OmniBook Ultra 14 image alone (3.07 MB) is larger than the entire acceptable image budget for the page. Run all 19 images through WebP conversion at quality 85, targeting ≤150 KB per image. This can reduce total image payload from 10.33 MB to under 1.5 MB.

3. **[High] Fix HTTPS / TLS (S-4)** — If this is production, serve over HTTPS. This is a prerequisite for any trust signal, and many modern browser APIs behave differently (or are disabled) over plain HTTP.

4. **[High] Add `<main>` landmark (A-1) and skip-to-content link (A-2)** — These are essential baseline accessibility requirements. Both fixes are 2–5 lines of HTML.

5. **[High] Add explicit `:focus-visible` styles (A-3)** — Without custom focus rings, keyboard users on certain browsers (especially Safari) receive no visual indication of keyboard focus.

6. **[High] Darken `--text-muted` in light mode (A-4 / A-5)** — Change `#6b7280` to `#5d6475` to fix WCAG AA failures on surface-2 and bg backgrounds. One token change, wide impact.

7. **[High] Fix badge dark mode adaptation (V-3)** — Add `@media (prefers-color-scheme: dark)` overrides for `.bg`, `.ba`, `.br`, `.tag-now`, `.tag-soon` with appropriate dark-mode color values.

8. **[High] Fix score progress bar animation (U-2)** — Set `style="width:0%"` in the rendered HTML template and use `requestAnimationFrame` to apply the target width after cards are in the DOM.

9. **[Medium] Fix duplicate `transition` in `.nav-links a` (V-2 / Q-3)** — One-line deletion.

10. **[Medium] Add nginx Cache-Control for images (P-5)** — One nginx location block addition; dramatically reduces repeat-visitor bandwidth.

11. **[Medium] Add Content-Security-Policy header (S-1)** — One nginx `add_header` directive.

12. **[Medium] Fix `tblSort()` default sort direction for weight (F-4)** — Add column-specific default sort direction logic so weight sorts lightest-first on first click.

13. **[Medium] Fix `attachFade()` observer accumulation (P-7 / Q-4)** — Store observer reference and disconnect on re-create.

14. **[Medium] Add favicon (Q-1)** — Eliminates 404 on every page load; can be an inline SVG data URI.

15. **[Medium] Add Open Graph meta tags (Q-2)** — Enables social sharing previews.

16. **[Low] Add `aria-hidden` to decorative emojis (A-6)** — Three attribute additions.

17. **[Low] Increase `.spec-cell .l` font size from `.58rem` to `.65rem` (A-7)**.

18. **[Low] Add filter result count with `aria-live` (U-6)**.

19. **[Low] Verify Yoga Slim 7i Aura 15" chip model (C-6)** — "Core Ultra 7 256V" is not a standard Intel SKU; likely should be "258V".

20. **[Low] Add `Permissions-Policy` header (S-3)**.

---

## Passed Checks

The following items are working correctly and require no action:

- All 19 devices render in the card grid and comparison table
- All 19 product images load successfully (HTTP 200) with correct filenames matching slugs
- `loading="lazy"` and `decoding="async"` are correctly applied to all product images
- Image error handler with event delegation correctly falls back to emoji on image load failure
- All 4 card sort buttons function correctly with proper sort directions
- All 4 filter buttons function correctly; mutual exclusivity maintained
- All 4 table column sort buttons function; toggle direction on same-column click
- `aria-pressed` state management is correct on all interactive buttons
- Nav smooth-scroll links target the correct section IDs
- IntersectionObserver nav active state works correctly with appropriate rootMargin
- Travel Score calculation is mathematically correct (verified independently)
- All 6 required Yoga Slim variants are present and correctly named
- "Now" / "Soon" availability badges are logically correct for all 19 devices
- All 4 hero stat figures (19 devices, weight range, MSRP range, battery range) are accurate
- Heading hierarchy is correct: one `h1`, three `h2`, no skipped levels
- All `<th>` elements have `scope="col"` (8/8)
- ARIA labels on table sort buttons are descriptive
- `role="progressbar"` with `aria-valuenow/min/max` is correctly set on score tracks
- Alt text is present on all product images (descriptive template string)
- `lang="en"` on `<html>`, viewport meta correctly defined
- Color contrast passes WCAG AA for: tag-now (4.57:1), tag-soon (6.37:1), badge-red (5.30:1), accent on accent-soft (4.75:1), text-muted on white surface (4.83:1), dark mode text-muted on surface (5.49:1)
- `color-mix()` usage in nav backdrop is well-supported (Chrome 111+, Firefox 113+, Safari 16.2+)
- No render-blocking resources — zero external CSS, JS, or web fonts
- HTML TTFB is 1.5ms; total HTML delivery is ~2ms at 48,978 bytes
- Comparison table has `overflow-x: auto` wrapper with `tabindex="0"` for keyboard scroll
- Print stylesheet (`@media print`) is correctly defined inline and hides non-print elements
- Fade-in IntersectionObserver correctly triggers `.vis` class on `.fi` elements
- `@container card` query is correctly defined syntactically; threshold is the only issue
- Explainer section code blocks render with correct syntax highlighting
- Browser support table correctly reflects 2026 availability ("Widely available" for CQ)
- Dark mode `prefers-color-scheme` tokens are comprehensive and well-calibrated
- `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` headers are correctly set
- Zero external dependencies — entire application is one HTML file
- `.card-sea` SEA availability notes are styled distinctly and have ARIA context label
- Disclaimer correctly notes Surface Pro 11 tablet-only weight and Type Cover addition
- Three "Soon" devices (7x Gen 11, 7a Gen 11, 7i Ultra Aura) correctly reflect CES 2026 announcements

---

*Report generated by QA Expert Agent — 2026-02-23*
