"""
"""
import jinja2
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent.parent


class PromptHandler:
    """
    """

    def __init__(self,
                 prompt_target: Path | str,
                 prompt_template: str,
                 style: str = "jinja2"):
        """
        """
        self.prompt_target = prompt_target
        self.prompt_template = prompt_template
        self.style = style
        self.load_prompt()

    def load_prompt(self, encoding="utf8"):
        """
        Load text prompt from prompt_target
        """
        if self.style == "direct":
            return
        with open(self.prompt_target, "r", encoding=encoding) as fp:
            self.prompt_template = fp.read()
            # generaly, reading file should be in batches, but for
            # prompts are relatively short, we may load all of it directly.

    def render_prompt_jinja2(self, **kwargs):
        """
        Render jinja2 type prompts.
        """
        return jinja2.Template(self.prompt_template).render(**kwargs)

    def render_prompt(self, **kwargs):
        """
        Default render method is jinja2
        """
        match self.style:
            case "jinja2":
                return self.render_prompt_jinja2(**kwargs)
            case _:
                return self.prompt_template
