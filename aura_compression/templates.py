"""
AURA Template Library

Built-in templates for common AI response patterns.
"""

from typing import Dict

class TemplateLibrary:
    """Template library for binary semantic compression"""

    # Production template library
    DEFAULT_TEMPLATES: Dict[int, str] = {
        # Limitations
        0: "I don't have access to {0}. {1}",
        1: "I cannot {0}.",
        2: "I'm unable to {0}.",
        5: "The {0} is {1}.",

        # Questions
        6: "Can you {0}?",

        # Facts
        10: "The {0} of {1} is {2}.",
        11: "{0} is {1}.",
        12: "{0} are {1}.",

        # Code examples
        30: "Here's {0} {1} example:\n\n```{2}\n{3}\n```",
        31: "Here's how to {0}:\n\n```{1}\n{2}\n```",
        32: "```{0}\n{1}\n```",

        # Instructions
        40: "To {0}, use {1}: `{2}`",
        41: "To {0}, {1}.",
        42: "You can {0} by {1}.",

        # Comparisons
        60: "The main {0} between {1} are: {2}",
        61: "{0} and {1} are different: {0} {2}, {1} {3}.",

        # Explanations
        70: "The {0} of {1} is {2} because {3}.",
        71: "{0} works by {1}.",

        # Enumerations
        80: "Common {0} include: {1}.",
        81: "The main {0} are: {1}.",

        # Recommendations
        90: "To {0}, I recommend: {1}",
        91: "I recommend {0}.",

        # Clarifications
        100: "Yes, I can help with that. What specific {0} would you like to know more about?",
        101: "Could you clarify {0}?",

        # Features
        120: "The {0} in {1} allows you to {2}: `{3}`",
    }

    def __init__(self, custom_templates: Dict[int, str] = None):
        """
        Initialize template library

        Args:
            custom_templates: Additional templates to add (dict of {id: template_string})
        """
        self.templates = self.DEFAULT_TEMPLATES.copy()
        if custom_templates:
            self.templates.update(custom_templates)

    def get(self, template_id: int) -> str:
        """Get template by ID"""
        return self.templates.get(template_id)

    def add(self, template_id: int, template: str):
        """Add custom template"""
        self.templates[template_id] = template

    def remove(self, template_id: int):
        """Remove template"""
        if template_id in self.templates:
            del self.templates[template_id]

    def list_templates(self) -> Dict[int, str]:
        """Get all templates"""
        return self.templates.copy()

    def format_template(self, template_id: int, slots: list) -> str:
        """Format template with slots"""
        if template_id not in self.templates:
            raise ValueError(f"Unknown template ID: {template_id}")

        template = self.templates[template_id]
        return template.format(*slots)
