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
        print(f"\n⚠ There were {num_errors} errors")
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

    re_title = re.compile(r"## Chapter \d+ — [\w\s\,\:\-\'\?;\.]+$")

    def check_title(self, f):
        """
        Check that the chapter title is properly formatted
        """
        title_line = f.readline()
        if not self.re_title.match(title_line):
            if title_line.startswith(("## Postscript", "## Note of a Scribe")):
                return 0
            print(f"  ⚠ The title '{title_line}' does not follow the guidelines")
            return 1
        return 0
    
    def check_double_dashes(self, f):
        lines = f.readlines()
        for i, line in enumerate(lines, start=1):
            if "--" in line and "---" not in line:
                print(f"  ⚠ There is a double-dash on line {i}")
                return 1
        return 0
    
    def check_for_what_it_means(self, f):
        lines = f.readlines()
        for i, line in enumerate(lines):
            if self.is_subheader("### What it means", line, lines, i):
                return 0
        print(f"  ⚠ The 'What it means' section header is not formatted correctly")
        return 1

    def check_for_reflection(self, f):
        lines = f.readlines()
        for i, line in enumerate(lines):
            if self.is_subheader("### Reflection", line, lines, i):
                return 0
        print(f"  ⚠ The 'Reflection' section header is not formatted correctly")
        return 1

    def is_subheader(self, header, line, lines, i):
        if line.strip() == header:
            if (
                lines[i-1].strip() == ""
                and lines[i-2].strip() == "---"
                and lines[i-3].strip() == ""
                and lines[i-4].strip() != ""
                and lines[i+1].strip() == ""
                and lines[i+2].strip() != ""
            ):
                return True
        return False


class Fixer:
    def fix(self, filepath):
        contents = None
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            contents = f.read()
            contents = self.fix_trailing_whitespace(contents)
            contents = self.fix_title_separator(contents)

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

    def fix_trailing_whitespace(self, contents):
        lines = [x.rstrip() for x in contents.splitlines()]
        return "\n".join(lines) + "\n"

    def fix_title_separator(self, contents):
        lines = contents.splitlines()
        lines[0] = (
            lines[0]
            .replace(" – ", " — ")
            .replace("’", "'")
            .replace(" - ", " — ")
        )
        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    cli(prog_name="do")
