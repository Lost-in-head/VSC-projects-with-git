"""
DescriptionBuilder — formats image analysis into an eBay listing description.

Extracted from app.format_description() for testability and reuse.
"""
import logging

logger = logging.getLogger(__name__)

# Trading-card specific fields rendered in the description.
_CARD_FIELDS = [
    ('player_name', 'Player'),
    ('set_name', 'Set'),
    ('year', 'Year'),
    ('card_number', 'Card Number'),
    ('grade', 'Grade'),
]


class DescriptionBuilder:
    """Builds plain-text eBay listing descriptions from image analysis."""

    def build(self, analysis: dict) -> str:
        """Format an analysis dict into a multiline description string."""
        parts = []

        if analysis.get('category'):
            parts.append(f"**Category**: {analysis['category']}")

        if analysis.get('condition'):
            parts.append(f"**Condition**: {analysis['condition']}")

        for key, label in _CARD_FIELDS:
            if analysis.get(key):
                parts.append(f"**{label}**: {analysis[key]}")

        grading_notes = analysis.get('grading_notes')
        if grading_notes:
            if isinstance(grading_notes, list):
                notes_text = '\n'.join(f"• {n}" for n in grading_notes)
            else:
                notes_text = str(grading_notes)
            parts.append(f"**Grading Notes**:\n{notes_text}")

        features = analysis.get('features')
        if features:
            if isinstance(features, list):
                features_text = '\n'.join(f"• {f}" for f in features)
            else:
                features_text = str(features)
            parts.append(f"**Features**:\n{features_text}")

        if analysis.get('brand'):
            parts.append(f"**Brand**: {analysis['brand']}")

        if analysis.get('model'):
            parts.append(f"**Model**: {analysis['model']}")

        return '\n\n'.join(parts)
