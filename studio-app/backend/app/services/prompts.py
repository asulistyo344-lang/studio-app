NICHE_STYLES: dict[str, list[str]] = {
    "interior": [
        "Modern",
        "Minimalist",
        "Scandinavian",
        "Bohemian",
        "Industrial",
        "Japandi",
        "Mediterranean",
    ],
    "exterior": [
        "Contemporary",
        "Classic",
        "Tropical",
        "Minimalist",
        "Mediterranean",
        "Industrial Modern",
    ],
    "product_model": [
        "Casual Street",
        "Professional",
        "Outdoor",
        "Luxury Editorial",
        "Fitness",
        "Beach Summer",
    ],
}

BASE_TEMPLATES: dict[str, str] = {
    "interior": (
        "Interior design visualization. {style} style redesign. "
        "Photorealistic architectural photography. "
        "Professional interior design magazine quality. "
        "Natural lighting, high resolution, 8k."
    ),
    "exterior": (
        "Architectural exterior visualization. {style} style facade redesign. "
        "Photorealistic architectural photography. "
        "Professional architectural render quality. "
        "Golden hour lighting, landscaping included, high resolution."
    ),
    "product_model": (
        "Professional fashion/lifestyle product photography. "
        "{style} aesthetic. "
        "The product must be clearly visible and accurately represented. "
        "Commercial photography quality, magazine editorial standard."
    ),
}

STYLE_ADDITIONS: dict[str, dict[str, str]] = {
    "interior": {
        "Modern": "Clean lines, neutral palette, minimal furniture, open space",
        "Minimalist": "Extreme simplicity, monochrome, only essential elements",
        "Scandinavian": "Light wood, white walls, cozy textures, hygge atmosphere",
        "Bohemian": "Eclectic mix, warm colors, plants, layered textiles, rattan",
        "Industrial": "Exposed brick, metal, Edison bulbs, raw materials",
        "Japandi": "Japanese-Scandinavian fusion, wabi-sabi, muted earth tones",
        "Mediterranean": "Arches, terracotta, blue accents, whitewashed walls",
    },
    "exterior": {
        "Contemporary": "Glass, steel, geometric forms, flat or low-pitched roof",
        "Classic": "Symmetrical, columns, traditional materials, timeless",
        "Tropical": "Natural materials, large overhangs, open air design, lush greenery",
        "Minimalist": "Clean facade, minimal ornamentation, monochrome palette",
        "Mediterranean": "Stucco walls, terracotta roof, arched windows, warm tones",
        "Industrial Modern": "Exposed steel, brick, large factory windows, urban",
    },
    "product_model": {
        "Casual Street": "Urban street style, casual outfit, city background, natural light",
        "Professional": "Office/business setting, professional attire, clean background",
        "Outdoor": "Natural outdoor setting, adventure/lifestyle context, golden hour",
        "Luxury Editorial": "High fashion, dramatic lighting, luxury hotel or venue setting",
        "Fitness": "Athletic context, gym or outdoor fitness, activewear aesthetic",
        "Beach Summer": "Beach/tropical setting, summer fashion, warm light, sand and water",
    },
}

VARIANT_SUFFIXES: list[str] = [
    "angle: wide establishing shot, full room/product view",
    "angle: medium shot, detail focus, lifestyle context",
    "angle: close detail shot, texture and material emphasis",
]


def build_prompt(niche: str, style: str, user_prompt: str | None, variant_index: int) -> str:
    base = BASE_TEMPLATES[niche].format(style=style)
    addition = STYLE_ADDITIONS[niche][style]
    suffix = VARIANT_SUFFIXES[variant_index % len(VARIANT_SUFFIXES)]

    parts = [base, addition]
    if user_prompt:
        parts.append(user_prompt)
    parts.append(suffix)

    return " ".join(parts)
