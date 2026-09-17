"""Static nutrition, health and usage information per fruit class.

Figures are approximate, per 100g edible portion, sourced from general
nutrition references. The app is a prototype and is not a certified
food-safety or nutrition tool (see project scoping doc, section 2.4).
"""

FRUIT_INFO = {
    "apple": {
        "display_name": "Apple",
        "nutrition": {
            "calories_kcal": 52,
            "carbs_g": 14,
            "sugar_g": 10,
            "fiber_g": 2.4,
            "vitamin_c_mg": 4.6,
            "potassium_mg": 107,
        },
        "health_benefits": [
            "Good source of dietary fibre, supporting digestion.",
            "Contains antioxidants (quercetin, catechin) linked to heart health.",
            "Low glycaemic load, suitable for most blood-sugar-conscious diets.",
        ],
        "usage_suggestions": [
            "Eat fresh as a snack, sliced with nut butter.",
            "Bake into pies, crumbles or sauces.",
            "Add to salads or slaw for crunch.",
        ],
    },
    "banana": {
        "display_name": "Banana",
        "nutrition": {
            "calories_kcal": 89,
            "carbs_g": 23,
            "sugar_g": 12,
            "fiber_g": 2.6,
            "vitamin_c_mg": 8.7,
            "potassium_mg": 358,
        },
        "health_benefits": [
            "High in potassium, supporting healthy blood pressure.",
            "Provides quick-release energy, useful before/after exercise.",
            "Contains vitamin B6, supporting metabolism.",
        ],
        "usage_suggestions": [
            "Eat fresh as a snack or add to smoothies.",
            "Slice over cereal or porridge.",
            "Bake into banana bread once very ripe.",
        ],
    },
}

RIPENESS_NOTES = {
    "apple": {
        "unripe": "This apple looks under-ripe (firm, strongly green). Best left a few more days.",
        "ripe": "This apple looks ripe and ready to eat.",
        "overripe": "This apple looks very ripe or bruised. Best used soon, e.g. in baking.",
    },
    "banana": {
        "unripe": "This banana looks under-ripe (green). It will be firm and less sweet.",
        "ripe": "This banana looks ripe and ready to eat (yellow).",
        "overripe": "This banana looks overripe (brown spots or heavily spotted). Great for banana bread or smoothies.",
    },
}


def get_fruit_info(label: str) -> dict:
    return FRUIT_INFO.get(label, {})


def get_ripeness_note(label: str, ripeness: str) -> str:
    return RIPENESS_NOTES.get(label, {}).get(ripeness, "")
