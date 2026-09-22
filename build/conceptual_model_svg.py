"""Vector SVGs of the conceptual model, from the figures exported from Canva.

    python build/conceptual_model_svg.py

Reads ``Urban Liveability Mexicali - <Language>.pdf`` (one page each, all
vector) and writes ``Urban Liveability Mexicali - <Language>.svg`` beside it,
which the region's configuration names as the dashboard's conceptual model
(``reporting.languages.<Language>.conceptual_model``).

Text is converted to outlines: the figures use Canva's own typeface, which a
browser will not have, and outlines render exactly as designed without
shipping a font.  The fixed page size is replaced by a viewBox so the figure
scales to its container.  It also prints the fill and stroke of each domain
node, which the ULI's domain colours are taken from.
"""

import os
import re

import fitz  # PyMuPDF

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGUAGES = ('English', 'Spanish')
# a domain node's label, as it reads in each figure, by framework domain
DOMAIN_LABELS = {
    'English': {
        'safety': 'Safety',
        'mobility_transport': 'Mobility',
        'built_environment': 'Built',
        'ambient_environment': 'Ambient',
        'housing': 'Housing',
        'economic_development': 'Economic',
        'social_infrastructure': 'Social',
        'sociodemographics': 'Sociodemo-',
    },
}


def svg_of(page):
    """The page as a scalable SVG, with text as outlines."""
    svg = page.get_svg_image(text_as_path=True)
    width, height = page.rect.width, page.rect.height
    # sized by its container rather than fixed at the page's size in points:
    # with only a viewBox, an <img> takes its width from the page and its
    # height from the figure's proportions
    svg = re.sub(
        r'<svg([^>]*?)\swidth="[^"]*"\s+height="[^"]*"',
        r'<svg\1',
        svg,
        count=1,
    )
    if 'viewBox' not in svg[:500]:
        svg = svg.replace(
            '<svg',
            f'<svg viewBox="0 0 {width:g} {height:g}"',
            1,
        )
    return svg


def hex_of(colour):
    return '#' + ''.join(f'{round(c * 255):02X}' for c in colour)


def domain_colours(page, labels):
    """Fill and stroke of the node circle holding each domain's label.

    The node is the smallest filled drawing whose box contains the label, and
    its ring the stroked drawing of about the same box.
    """
    words = page.get_text('words')
    drawings = page.get_drawings()
    found = {}
    for domain, first_word in labels.items():
        boxes = [fitz.Rect(w[:4]) for w in words if w[4] == first_word]
        for box in boxes:
            around = [
                d
                for d in drawings
                if d['rect'].contains(box)
                and d['rect'].width < 250
                and d['rect'].width > box.width
            ]
            # a domain node is pastel; subdomain nodes, which share words
            # with it ('Personal Safety'), are white, and glyphs are dark
            filled = [
                d
                for d in around
                if d.get('fill') and 0.5 < min(d['fill']) < 0.99
            ]
            stroked = [d for d in around if d.get('color')]
            if not filled:
                continue
            node = min(filled, key=lambda d: d['rect'].width)
            ring = min(
                stroked or [node],
                key=lambda d: abs(d['rect'].width - node['rect'].width),
            )
            found[domain] = {
                'fill': hex_of(node['fill']),
                'stroke': hex_of(ring.get('color') or node['fill']),
            }
            break
    return found


def main():
    for language in LANGUAGES:
        source = os.path.join(HERE, f'Urban Liveability Mexicali - {language}.pdf')
        target = os.path.splitext(source)[0] + '.svg'
        page = fitz.open(source)[0]
        svg = svg_of(page)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(svg)
        print(f'{os.path.basename(target)}: {len(svg) / 1024:,.0f} KB')
        if language in DOMAIN_LABELS:
            for domain, colours in domain_colours(
                page,
                DOMAIN_LABELS[language],
            ).items():
                print(f'  {domain:24s} fill {colours["fill"]}  stroke {colours["stroke"]}')


if __name__ == '__main__':
    main()
