"""Tests for aigis.badge module."""

from aigis.badge import BADGE_SVG, get_badge_html, get_badge_svg


class TestBadgeSvg:
    def test_badge_svg_is_string(self):
        assert isinstance(BADGE_SVG, str)

    def test_badge_svg_is_valid_svg(self):
        assert "<svg" in BADGE_SVG
        assert "</svg>" in BADGE_SVG

    def test_badge_svg_contains_text(self):
        assert "Protected by Aigis" in BADGE_SVG

    def test_badge_svg_has_xmlns(self):
        assert 'xmlns="http://www.w3.org/2000/svg"' in BADGE_SVG


class TestGetBadgeSvg:
    def test_returns_svg_constant(self):
        assert get_badge_svg() == BADGE_SVG

    def test_returns_string(self):
        assert isinstance(get_badge_svg(), str)


class TestGetBadgeHtml:
    def test_default_link(self):
        html = get_badge_html()
        assert "<a href=" in html
        assert "aigis-mauve.vercel.app" in html
        assert "</a>" in html

    def test_contains_svg(self):
        html = get_badge_html()
        assert "<svg" in html
        assert "</svg>" in html

    def test_custom_link(self):
        html = get_badge_html(link="https://example.com")
        assert 'href="https://example.com"' in html

    def test_security_attributes(self):
        html = get_badge_html()
        assert 'target="_blank"' in html
        assert 'rel="noopener"' in html

    def test_accessibility_title(self):
        html = get_badge_html()
        assert 'title="Protected by Aigis"' in html
