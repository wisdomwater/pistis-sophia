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


@cli.command(short_help="Compile into output files")
@click.option("-p", "--pdf", is_flag=True, help="Generate PDF")
@click.option("-e", "--epub", is_flag=True, help="Generate ePub")
def compile(pdf, epub):
    """
    Compile into output file formats
    """
    all_files = not pdf and not epub
    compiler = Compiler(pdf, epub, all_files)
    compiler.compile()


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
    for subdir in sorted(os.listdir("chapters")):
        if not os.path.isdir(os.path.join("chapters", subdir)):
            continue
        for file in sorted(os.listdir(os.path.join("chapters", subdir))):
            if not file.endswith(".md"):
                continue
            filepath = os.path.join("chapters", subdir, file)
            yield filepath


class Compiler:
    book_md = "output/markdown/book.md"
    book_pdf = "output/pdf/book.pdf"
    book_epub = "output/epub/book.epub"
    epub_css = "scripts/epub.css"
    pagebreak_lua = "scripts/pagebreak.lua"

    def __init__(self, pdf, epub, all_files):
        self.pdf = pdf
        self.epub = epub
        self.all_files = all_files
    
    def compile(self):
        self.create_md()

        if self.all_files or self.epub:
            self.create_epub()

        if self.all_files or self.pdf:
            self.create_pdf()

    def create_md(self):
        filename = self.book_md
        print(f"Creating {filename}")
        files = [
            "chapters/foreword.md",
        ]
        files.extend(all_chapters())
        
        content = ""
        for file in files:
            with open(file, encoding="utf-8", errors="ignore") as f:
                content += f.read()
                content += "\n::: pagebreak\n:::\n\n"
        content = content.strip()

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)

    def create_epub(self):
        print(f"Creating {self.book_epub}")
        os.makedirs(os.path.dirname(self.book_epub), exist_ok=True)
        exit_code = os.system(
            f"pandoc -o {self.book_epub} {self.book_md} --css {self.epub_css} --lua-filter {self.pagebreak_lua}"
        )
        if exit_code != 0:
            print("Failed to generate epub")
            sys.exit(1)

    def create_pdf(self):
        print(f"Creating {self.book_pdf}")
        os.makedirs(os.path.dirname(self.book_pdf), exist_ok=True)
        exit_code = os.system(
            f"pandoc {self.book_md} -o {self.book_pdf} --pdf-engine=xelatex --metadata-file=meta.yaml --template=scripts/my-template.tex"
        )
        if exit_code != 0:
            print("Failed to generate pdf")


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

    re_title = re.compile(r"# Chapter \d+ — [\w\s\,\:\-\'\?;\.]+$")

    def check_title(self, f):
        """
        Check that the chapter title is properly formatted
        """
        title_line = f.readline()
        if not self.re_title.match(title_line):
            if title_line.startswith(("# Postscript", "# Note of a Scribe")):
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
            if self.is_subheader("## What it means", line, lines, i):
                return 0
        print(f"  ⚠ The 'What it means' section header is not formatted correctly")
        return 1

    def check_for_reflection(self, f):
        lines = f.readlines()
        for i, line in enumerate(lines):
            if self.is_subheader("## Reflection", line, lines, i):
                return 0
        print(f"  ⚠ The 'Reflection' section header is not formatted correctly")
        return 1
    
    def check_for_colonized_headers(self, f):
        lines = f.readlines()
        for i, line in enumerate(lines, start=1):
            if ":**" in line:
                print(f"  ⚠ There is a ':**' on line {i}")
                return 1
        return 0
    
    re_list = re.compile(r"^\d+\.\s")

    def check_for_bold(self, f):
        lines = f.readlines()
        for i, line in enumerate(lines, start=1):
            if "**" in line and not (line.startswith("**") or self.re_list.match(line)):
                print(f"  ⚠ There is a bold word on line {i}")
                return 1
        return 0
    
    def check_reflection_bullets(self, f):
        lines = f.readlines()
        for i, line in enumerate(lines):
            if self.is_subheader("## Reflection", line, lines, i):
                if (
                    lines[i+1].strip() == ""
                    and lines[i+2].startswith("* ")
                    and lines[i+3].startswith("* ")
                    and lines[i+4].startswith("* ")
                    and len(lines) == i + 5
                ):
                    return 0
        print(f"  ⚠ The reflective bullets are not formatted correctly as 3x '*'")
        return 1
    
    def check_third_person_questions(self, f):
        exceptions = [
            'I am the gnosis of the universe',
        ]
        lines = f.readlines()
        for i, line in enumerate(lines):
            if self.is_subheader("## Reflection", line, lines, i):
                questions = lines[i+2:i+4]
                for q in questions:
                    if any(x in q for x in ["I ", " me ", " me?", " me,", " my "]) and not any(x in q for x in exceptions):
                        print(f"  ⚠ Questions are written in the first person")
                        return 1
        return 0    

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
