"""CLIronChef — CLI / AI-agent control of the Typhur Dome 2 air fryer + Sync ONE probe.

Top-level imports for convenient library use:

    >>> from cliron_chef import TyphurAPI, RecipeRunner, AF04_MODES
    >>> api = TyphurAPI.from_cached_credentials()
    >>> runner = RecipeRunner(api, recipe_path="recipes/salmon_basic.json")
    >>> runner.run()

CLI usage:

    $ cliron-chef cook salmon_basic

See docs/ for the full guide.
"""

__version__ = "0.1.0"

from cliron_chef.api import TyphurAPI
from cliron_chef.modes import AF04_MODES, get_mode
from cliron_chef.runner import RecipeRunner

__all__ = [
    "__version__",
    "TyphurAPI",
    "AF04_MODES",
    "get_mode",
    "RecipeRunner",
]
