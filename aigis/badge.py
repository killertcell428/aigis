"""Aigis trust badge — embed in your product UI.

Provides SVG badge markup and a status endpoint helper for showing
real-time protection status in your application.
"""

BADGE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="28" viewBox="0 0 200 28">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#1e40af"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
  </defs>
  <rect width="200" height="28" rx="6" fill="url(#bg)"/>
  <path d="M16 6L10 9v4.5c0 4.2 2.9 8.1 6.8 9.1 3.9-1 6.8-4.9 6.8-9.1V9l-7.6-3z" fill="white" fill-opacity="0.2" stroke="white" stroke-width="1.2" stroke-linejoin="round"/>
  <path d="M13.5 13.5l1.5 1.5 3-3" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <text x="32" y="18" font-family="system-ui,-apple-system,sans-serif" font-size="11" font-weight="600" fill="white">Protected by Aigis</text>
</svg>"""


def get_badge_svg() -> str:
    """Return the Aigis trust badge as an SVG string."""
    return BADGE_SVG


def get_badge_html(link: str = "https://aigis-mauve.vercel.app") -> str:
    """Return the Aigis trust badge as an HTML anchor wrapping the SVG."""
    return f'<a href="{link}" target="_blank" rel="noopener" title="Protected by Aigis">{BADGE_SVG}</a>'
