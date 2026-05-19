"""Allow `python -m cliron_chef` to behave like `cliron-chef`."""

from cliron_chef.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
