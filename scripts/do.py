"""
do.py: Automation script

Commands:
    check-contents
"""
import os
import re
import sys
import time

import click

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@cli.command(short_help="Check chapter contents for mistakes")
def check_contents():
    """
    Check for various formatting rules and key content sections
    """
    num_errors = 0
    checker = Checker()
    for filepath in all_chapters():
        num_errors += checker.check(filepath)
    
    if num_errors:
        print("\n⚠ There were {num_errors} errors")
    else:
        print("\nYay - There are no errors")
    sys.exit(num_errors)


@cli.command(short_help="Fix the known issues")
def fixup():
    fixer = Fixer()
    for filepath in all_chapters():
        fixer.fix(filepath)

def all_chapters():
    for root, _, files in os.walk("chapters"):
        for file in files:
            if not file.endswith(".md"):
                continue
            filepath = os.path.join(root, file)
            yield filepath
    

class Checker:
    def check(self, filepath):
        num_errors = 0
        print(f"Checking {filepath}")
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            for attr_name in dir(self):
                if not attr_name.startswith("check_"):
                    continue
                check_func = getattr(self, attr_name)
                f.seek(0)
                num_errors += check_func(f)
        return num_errors

    re_title = re.compile(r"## Chapter \d — [\w\s]+$")

    def check_title(self, f):
        """
        Check that the chapter title is properly formatted
        """
        title_line = f.readline()
        if not self.re_title.match(title_line):
            print(f"  ⚠ The title '{title_line}' does not follow the guidelines")
            return 1
        return 0


class Fixer:
    def fix(self, filepath):
        contents = None
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            contents = f.read()
            contents = self.fix_title_colons(contents)

        # Sometimes opening the file for writing fails
        attempts = 0
        while attempts < 3:
            try:
                with open(filepath, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(contents)
                break
            except PermissionError:
                time.sleep(0.1)
                attempts += 1

    def fix_title_separators(self, contents):
        lines = contents.splitlines()
        lines[0] = lines[0].replace(" - ", " — ")
        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    cli(prog_name="do")
