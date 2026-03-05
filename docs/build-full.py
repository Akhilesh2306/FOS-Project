#!/usr/bin/env python3
"""
Reads FOS-storybook.html + all slides → writes FOS-storybook-full.html (NEW file).
Does NOT modify any existing files.

All slides are embedded as JS strings, no fetch calls.
Result is a single self-contained HTML that works via file://.

Usage:
    python3 build-full.py
    # → produces FOS-storybook-full.html (~5MB, fully standalone)
"""

import re
from pathlib import Path

INPUT = Path('FOS-storybook.html')
OUTPUT = Path('FOS-storybook-full.html')

assert INPUT.exists(), f'{INPUT} not found'

# ── Read sources (all read-only) ─────────────────────────────
deck_html = INPUT.read_text()

slides = {
    'slides/slide0-problem.html': Path('slides/slide0-problem.html').read_text(),
    'slides/slide1-journeys.html': Path('slides/slide1-journeys.html').read_text(),
    'slides/slide2-solution.html': Path('slides/slide2-solution.html').read_text(),
    'slides/slide3-architecture.html': Path('slides/slide3-architecture.html').read_text(),
    'slides/slide4-data-pipeline.html': Path('slides/slide4-data-pipeline.html').read_text(),
    'slides/slide5-data-model.html': Path('slides/slide5-data-model.html').read_text(),
    'slides/slide6-semantic.html': Path('slides/slide6-semantic.html').read_text(),
    'slides/slide7-agents.html': Path('slides/slide7-agents.html').read_text(),
    'slides/slide9-deepdives.html': Path('slides/slide9-deepdives.html').read_text(),
    'slides/slide10-gaps.html': Path('slides/slide10-gaps.html').read_text(),
}

# ── 1. Embed slide HTML in JS + slide loading function ───────
def escape_for_js(html):
    """Escape characters that break JS template literals."""
    html = html.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    # CRITICAL: </script> inside a JS string still closes the browser's script block.
    # Split it so the HTML parser doesn't see a closing tag.
    html = html.replace('</script>', '<\\/script>')
    return html

js_entries = ',\n'.join(
    f'  "{path}": `{escape_for_js(html)}`'
    for path, html in slides.items()
)

slide_loading_js = f"""

// ── Embedded slide content (no fetch) ──
const slideContent = {{
{js_entries}
}};

// Replace the async fetch-based loadDeck with synchronous loading
function loadDeckFull() {{
  const deck = document.getElementById('deck');
  const slideFilesLocal = slideFiles; // Use existing slideFiles array

  try {{
    const slideContents = slideFilesLocal.map(file => slideContent[file] || '');
    deck.innerHTML = slideContents.join('\\n');

    // Move overlays out of the deck to body.
    // CSS transform on .deck breaks position:fixed inside it.
    var overlays = deck.querySelectorAll('.overlay');
    overlays.forEach(function(o) {{
      document.body.appendChild(o);
    }});
  }} catch (error) {{
    console.error('Error loading deck:', error);
    deck.innerHTML = '<div style="padding:40px;color:#991B1B;background:#FEE2E2;border-radius:8px;"><strong>Failed to load storybook</strong></div>';
  }}
}}
"""

# Replace the loadDeck call with loadDeckFull
deck_html = deck_html.replace('loadDeck();', 'loadDeckFull();')

# Insert the slide loading JS before the existing loadDeck function
deck_html = deck_html.replace('async function loadDeck()', slide_loading_js + '\nasync function loadDeck()')

# ── Write NEW file (FOS-storybook.html is untouched) ─────────
OUTPUT.write_text(deck_html)
size_kb = len(deck_html) // 1024
print(f'Built → {OUTPUT} ({size_kb} KB)')
print(f'{INPUT} unchanged.')
