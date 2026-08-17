/** @type {import('tailwindcss').Config} */

// The five brand colours are locked and unchanged since Stage 0. What the
// redesign pass adds is the set of text/border/surface tokens that were
// previously being faked with navy at an opacity (text-navy/60, border-navy/10,
// bg-navy/5). Those opacity tricks are why the hierarchy read flat: heading
// colour and paragraph colour were the same hue, so they carried the same
// weight of importance. See docs/design/REDESIGN-SPEC.md.
//
// THE RULE THAT BREAKS MOST OFTEN: navy is for headings and the score-display
// number ONLY. Body text is `ink`. Meta/captions are `ink-secondary`.
//
// TYPE SCALE — the named fontSize keys below carry size, line-height, tracking
// and weight together, so `text-page-title` is the whole style and there is no
// way to apply half of it:
//
//   text-score-display    48/1.0   serif semibold  navy   (the 87 itself)
//   text-page-title       28/1.2   serif semibold  navy
//   text-section-heading  18/1.3   serif semibold  navy
//   text-body             15/1.5   Inter regular   ink
//   text-body-secondary   14/1.5   Inter regular   ink-secondary
//   text-meta-label       12/1.4   Inter medium    ink-secondary, uppercase
//   text-table-header     12/1.4   Inter medium    ink-secondary, uppercase
//   text-table-cell       14/1.5   Inter regular   ink, tabular-nums
//
// Colour and uppercase are NOT baked into the fontSize keys — Tailwind's
// fontSize tuple cannot express them — so those stay as companion classes.
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    // `spacing` is REPLACED, not extended. Only 4/8/16/24/32/48 exist, so an
    // off-scale class like p-3 (12px) silently produces nothing and the drift
    // shows up on screen instead of hiding in a diff.
    spacing: {
      0: '0px',
      px: '1px',
      1: '4px',
      2: '8px',
      4: '16px',
      6: '24px',
      8: '32px',
      12: '48px',
    },
    // One radius, the same way there is one shadow depth. Cards, controls,
    // tags and the role switcher all round by 4px so nothing looks borrowed
    // from a different design system.
    //
    // `full` is deliberately ABSENT, not merely unused: rounded-full pills are
    // the badge-soup tell the redesign is correcting, and deleting the token
    // means `rounded-full` silently produces nothing instead of quietly
    // working the next time someone reaches for it.
    borderRadius: {
      none: '0px',
      DEFAULT: '4px',
    },
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      white: '#FFFFFF',

      // Brand — locked since Stage 0, unchanged.
      bg: '#FAF8F4',
      navy: '#132A47',
      green: '#2E7D5B',
      gold: '#C8952B',
      coral: '#D4573D',

      // Text. Near-black rather than navy, so a paragraph stops competing
      // with the heading above it.
      ink: '#14171A',
      'ink-secondary': '#5B6169',
      'ink-muted': '#94989E',

      // Borders, warm-toned to sit on the #FAF8F4 ground rather than reading
      // as a cool grey imported from somewhere else.
      border: '#DDD9D0',
      'border-strong': '#C7C2B6',

      // Surfaces. surface-sunk names what was previously bg-navy/5 — the
      // skipped-row ground and code-like blocks.
      surface: '#FFFFFF',
      'surface-sunk': '#F3F0EA',
    },
    extend: {
      // Named type styles. Extended rather than replaced so the pass can move
      // page by page without the whole app losing its type at once; the named
      // keys are what new work should use.
      fontSize: {
        'score-display': ['48px', { lineHeight: '1', fontWeight: '600' }],
        'page-title': ['28px', { lineHeight: '1.2', fontWeight: '600' }],
        'section-heading': ['18px', { lineHeight: '1.3', fontWeight: '600' }],
        body: ['15px', { lineHeight: '1.5' }],
        'body-secondary': ['14px', { lineHeight: '1.5' }],
        'meta-label': ['12px', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        'table-header': ['12px', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        'table-cell': ['14px', { lineHeight: '1.5' }],
      },
      fontFamily: {
        // Fraunces carries the display voice; Inter carries everything read
        // at body size, including every number in a table.
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      // Layout dimensions, not spacing. Kept off the spacing scale on purpose
      // so nobody reaches for w-sidebar as a padding value.
      width: {
        sidebar: '240px',
      },
      height: {
        topbar: '64px',
      },
      // Defines the content region on a page that has no content yet, so the
      // shell reads as a page waiting to be filled rather than a card adrift.
      minHeight: {
        region: '320px',
      },
      // One shadow depth for the whole app. See CLAUDE.md UI conventions.
      boxShadow: {
        card: '0 1px 2px rgba(19, 42, 71, 0.06)',
      },
    },
  },
  plugins: [],
}
