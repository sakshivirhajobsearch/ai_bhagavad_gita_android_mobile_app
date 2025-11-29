# data/shlokas.py

from data.SECTION_1 import SECTION_1
from data.SECTION_2 import SECTION_2
from data.SECTION_3 import SECTION_3
from data.SECTION_4 import SECTION_4
from data.SECTION_5 import SECTION_5

"""
प्रत्येक SECTION_X इस संरचना में है:
SECTION_X = [
    {
        "title": "भाग 1 : समस्याएँ 1–4",
        "shlokas": [
            {
                "problem": "विस्मृति / अर्थ भूल जाना",
                "reference": "अध्याय 15 / श्लोक 15",
                "text": "...",
                "meaning": "...",
                "example": "..."
            },
            ...
        ]
    }
]
"""

# Combine all SECTION_* into one list
ALL_SHLOKAS = [
    SECTION_1[0],
    SECTION_2[0],
    SECTION_3[0],
    SECTION_4[0],
    SECTION_5[0]
]

# Backward compatibility
PROBLEM_SECTIONS = ALL_SHLOKAS

print("🔢 Current Sections Loaded:", len(ALL_SHLOKAS))
