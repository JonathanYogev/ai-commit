import sys
import logging
import os
import subprocess
import argparse
from huggingface_hub import InferenceClient
from requests.exceptions import HTTPError, RequestException
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# ============ Setup ============
console = Console()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
MAX_DIFF_CHARS = 5000  # truncate long diffs


# ============ Git Helpers ============
def get_staged_diff() -> str | None:
    """Get staged git diff safely."""
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--staged"],
            text=True,
            stderr=subprocess.STDOUT,
            encoding='utf-8'
        ).strip()
        if not diff:
            return None
        if len(diff) > MAX_DIFF_CHARS:
            logger.warning(
                "Diff too long, truncating to %s chars", MAX_DIFF_CHARS)
            diff = diff[:MAX_DIFF_CHARS] + "\n... [truncated]"
        return diff
    except subprocess.CalledProcessError as e:
        logger.error("Error getting git diff: %s", getattr(e, 'output', e))
        return None
    except FileNotFoundError:
        logger.error(
            "Git command not found. Please ensure git is installed and in your PATH.")
        return None


# ============ Commit Message Generation ============
def generate_commit_message(diff: str, model: str, hf_token: str | None) -> str | None:
    """Generate commit message using the chosen HF model."""

    # Explicit client creation
    if hf_token:
        client = InferenceClient(token=hf_token)
    else:
        client = InferenceClient()  # works for models that don’t require auth

    prompt = f"""
Analyze the following git diff, coming from the command git diff --cached , and generate a concise commit message in the Conventional Commits format.
Start with a type (feat, fix, chore, docs, refactor, test, style, build, ci, perf), followed by a short, lowercase description.
Do NOT add explanations, markdown, or code blocks.

Git Diff:
{diff}

Commit Message:
"""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message["content"].strip()
    except (HTTPError, RequestException) as e:
        logger.error("API error: %s", e)
        return None
    except Exception:
        logger.exception("Unexpected error generating commit message")
        return None


# ============ Git Commit ============
def commit_with_message(msg: str) -> None:
    """Run git commit with the message."""
    try:
        subprocess.run(["git", "commit", "-F", "-"], input=msg,
                       text=True, check=True, encoding='utf-8')
        console.print(
            f"\n✅ Successfully committed with message: [bold green]{msg}[/bold green]")
    except subprocess.CalledProcessError as e:
        logger.error("Git commit failed: %s", getattr(e, 'stderr', e))
        console.print(
            f"\n[red]Git commit error:[/red]\n{getattr(e, 'stderr', e)}")


# ============ UI Helpers ============
def show_diff(diff: str):
    """Pretty print the git diff (truncated)."""
    syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
    console.print(
        Panel(syntax, title="[yellow]Staged Diff[/yellow]", border_style="yellow"))


def show_suggested_message(msg: str):
    """Show commit message suggestion in a panel."""
    console.print(
        Panel.fit(
            f"[bold green]{msg}[/bold green]",
            title="[cyan]Suggested Commit Message[/cyan]",
            border_style="blue"
        )
    )

# ============ User Prompt Functions ============
def prompt_manual_message() -> str:
    """Prompt the user to enter a commit message manually."""
    while True:
        msg = console.input(
            "[yellow]Enter your commit message:[/yellow] ").strip()
        if msg:
            return msg
        console.print("[red]Commit message cannot be empty. Exiting.[/red]")
        sys.exit(1)


def prompt_commit_message(initial_msg: str, diff: str, model: str, hf_token: str | None) -> str:
    """
    Prompt the user to accept, reject, regenerate, or edit the suggested commit message.
    """
    msg = initial_msg
    while True:
        choice = console.input(
            "[bold cyan]Use this message?[/bold cyan] "
            "[green][Y]es[/green] / [red][N]o[/red] / [yellow][E]dit[/yellow] / [magenta][R]egenerate[/magenta]: "
        ).strip().lower()

        if choice in ["y", "yes", ""]:
            return msg

        elif choice in ["n", "no"]:
            console.print("[red]Commit cancelled by user.[/red]")
            sys.exit(0)

        elif choice in ["e", "edit"]:
            msg = prompt_manual_message()

        elif choice in ["r", "regen", "regenerate"]:
            with console.status("[bold magenta]Regenerating commit message...[/bold magenta]", spinner="dots"):
                msg = generate_commit_message(diff, model, hf_token)
            if msg:
                show_suggested_message(msg)
            else:
                msg = prompt_manual_message()

        else:
            console.print(
                "[red]Invalid choice. Enter 'y', 'n', 'e', or 'r'.[/red]")


# ============ Main ============
def main():
    hf_token = os.getenv("HF_TOKEN")
    parser = argparse.ArgumentParser(
        description="Generate smart git commit messages with Hugging Face models.")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="Model to use (default: %(default)s)")
    args = parser.parse_args()
    try:
        diff = get_staged_diff()
        if not diff:
            console.print(
                "\n[red]No staged changes. Stage your files first (`git add`).[/red]")
            sys.exit(1)

        show_diff(diff)

        with console.status("[bold green]Generating commit message...[/bold green]", spinner="dots"):
            msg = generate_commit_message(diff, args.model, hf_token)

        if msg:
            show_suggested_message(msg)
            msg = prompt_commit_message(
                msg, diff, args.model, hf_token)
        else:
            console.print(
                "[red]Failed to generate a commit message. Please write one manually.[/red]")
            msg = prompt_manual_message()

            if not msg:
                console.print(
                    "[red]Commit message cannot be empty. Exiting.[/red]")
                sys.exit(1)

        commit_with_message(msg)
    except KeyboardInterrupt:
        console.print(
            "\n\n[bold yellow]Operation cancelled by user. Exiting.[/bold yellow]")
        sys.exit(0)
