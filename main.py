"""Ad Copy Critic — CLI entry point."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

load_dotenv()

app = typer.Typer(
    name="ad-copy-critic",
    help="Evaluate ad copy with the precision of a senior creative strategist.",
    add_completion=False,
)
console = Console()


def _load_input_file(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _render_markdown(critique: dict) -> str:
    score = critique["overall_score"]
    verdict = critique["overall_verdict"].upper().replace("_", " ")
    lines = [
        f"# Ad Copy Critique\n",
        f"## Overall Score: {score}/100 — {verdict}\n",
        f"> {critique['executive_summary']}\n",
        "---\n",
        "## Dimension Scores\n",
    ]

    table_lines = ["| Dimension | Score | Verdict |", "|-----------|-------|---------|"]
    for dim in critique["dimensions"]:
        bar = "█" * dim["score"] + "░" * (10 - dim["score"])
        table_lines.append(f"| {dim['dimension']} | {dim['score']}/10 {bar} | {dim['verdict']} |")
    lines.extend(table_lines)
    lines.append("")

    if critique.get("critical_issues"):
        lines.append("## ⛔ Critical Issues\n")
        for issue in critique["critical_issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    if critique.get("minor_issues"):
        lines.append("## ⚠️ Minor Issues\n")
        for issue in critique["minor_issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    if critique.get("strengths"):
        lines.append("## ✅ Strengths\n")
        for s in critique["strengths"]:
            lines.append(f"- {s}")
        lines.append("")

    if critique.get("dimensions"):
        issues_with_fixes = [d for d in critique["dimensions"] if d.get("issue")]
        if issues_with_fixes:
            lines.append("## Dimension Details\n")
            for dim in issues_with_fixes:
                lines.append(f"**{dim['dimension']}** (score {dim['score']}/10)")
                lines.append(f"- Issue: {dim['issue']}")
                if dim.get("fix"):
                    lines.append(f"- Fix: {dim['fix']}")
                lines.append("")

    lines.append("## Improved Variants\n")
    for variant in critique["variants"]:
        lines.append(f"### {variant['label']}")
        lines.append(f"**Headline:** {variant['headline']}")
        if variant.get("body"):
            lines.append(f"**Body:** {variant['body']}")
        if variant.get("cta"):
            lines.append(f"**CTA:** {variant['cta']}")
        lines.append(f"*{variant['rationale']}*\n")

    lines.append("## A/B Test Recommendation\n")
    lines.append(critique["ab_test_recommendation"] + "\n")

    lines.append("## Platform Fit\n")
    lines.append(critique["platform_fit_note"] + "\n")

    return "\n".join(lines)


def _render_html(critique: dict, title: str = "Ad Copy Critique") -> str:
    score = critique["overall_score"]
    verdict = critique["overall_verdict"].upper().replace("_", " ")
    color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"

    dims_html = ""
    for dim in critique["dimensions"]:
        pct = dim["score"] * 10
        bar_color = "#22c55e" if dim["score"] >= 7 else "#f59e0b" if dim["score"] >= 5 else "#ef4444"
        issue_html = f"<p class='issue'>⚠️ {dim['issue']}</p>" if dim.get("issue") else ""
        fix_html = f"<p class='fix'>💡 Fix: {dim['fix']}</p>" if dim.get("fix") else ""
        dims_html += f"""
        <div class="dimension">
            <div class="dim-header">
                <span class="dim-name">{dim['dimension']}</span>
                <span class="dim-score">{dim['score']}/10</span>
            </div>
            <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
            <p class="verdict">{dim['verdict']}</p>
            {issue_html}{fix_html}
        </div>"""

    variants_html = ""
    for v in critique["variants"]:
        body_html = f"<p><strong>Body:</strong> {v['body']}</p>" if v.get("body") else ""
        cta_html = f"<p><strong>CTA:</strong> {v['cta']}</p>" if v.get("cta") else ""
        variants_html += f"""
        <div class="variant">
            <h3>{v['label']}</h3>
            <p><strong>Headline:</strong> {v['headline']}</p>
            {body_html}{cta_html}
            <p class="rationale"><em>{v['rationale']}</em></p>
        </div>"""

    critical_html = "".join(f"<li>{i}</li>" for i in critique.get("critical_issues", []))
    minor_html = "".join(f"<li>{i}</li>" for i in critique.get("minor_issues", []))
    strengths_html = "".join(f"<li>{s}</li>" for s in critique.get("strengths", []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; color: #1a1a2e; background: #f8f9fa; }}
  h1 {{ color: #1a1a2e; }} h2 {{ color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }}
  .score-card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 24px; text-align: center; }}
  .score-big {{ font-size: 72px; font-weight: 800; color: {color}; line-height: 1; }}
  .verdict-badge {{ display: inline-block; padding: 4px 16px; border-radius: 20px; background: {color}22; color: {color}; font-weight: 600; font-size: 14px; margin-top: 8px; }}
  .summary {{ font-size: 16px; color: #6b7280; margin-top: 12px; }}
  .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; }}
  .dimension {{ margin-bottom: 20px; }}
  .dim-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
  .dim-name {{ font-weight: 600; }} .dim-score {{ font-weight: 700; color: #374151; }}
  .bar-bg {{ background: #e5e7eb; border-radius: 4px; height: 8px; margin-bottom: 8px; }}
  .bar-fill {{ height: 8px; border-radius: 4px; transition: width 0.3s; }}
  .verdict {{ font-size: 14px; color: #6b7280; margin: 4px 0; }}
  .issue {{ color: #b45309; font-size: 14px; margin: 4px 0; }} .fix {{ color: #065f46; font-size: 14px; margin: 4px 0; }}
  ul {{ padding-left: 20px; }} li {{ margin-bottom: 6px; }}
  .variant {{ background: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 0 8px 8px 0; padding: 16px; margin-bottom: 12px; }}
  .variant h3 {{ margin-top: 0; color: #166534; }}
  .rationale {{ color: #6b7280; font-style: italic; }}
  .critical {{ color: #dc2626; }} .minor {{ color: #d97706; }}
  footer {{ text-align: center; color: #9ca3af; font-size: 13px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="score-card">
  <div class="score-big">{score}</div>
  <div class="verdict-badge">{verdict}</div>
  <p class="summary">{critique['executive_summary']}</p>
</div>

<div class="card">
  <h2>Dimension Scores</h2>
  {dims_html}
</div>

{'<div class="card"><h2>⛔ Critical Issues</h2><ul class="critical">' + critical_html + '</ul></div>' if critique.get('critical_issues') else ''}
{'<div class="card"><h2>⚠️ Minor Issues</h2><ul class="minor">' + minor_html + '</ul></div>' if critique.get('minor_issues') else ''}
{'<div class="card"><h2>✅ Strengths</h2><ul>' + strengths_html + '</ul></div>' if critique.get('strengths') else ''}

<div class="card">
  <h2>Improved Variants</h2>
  {variants_html}
</div>

<div class="card">
  <h2>A/B Test Recommendation</h2>
  <p>{critique['ab_test_recommendation']}</p>
</div>

<div class="card">
  <h2>Platform Fit</h2>
  <p>{critique['platform_fit_note']}</p>
</div>

<footer>Built by <a href="https://swapnanilsaha.com">Swapnanil Saha</a> — Ad Copy Critic · Powered by Claude</footer>
</body>
</html>"""


@app.command()
def critique(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to JSON input file"),
    headline: Optional[str] = typer.Option(None, "--headline", help="Ad headline"),
    body: Optional[str] = typer.Option(None, "--body", help="Ad body copy"),
    cta: Optional[str] = typer.Option(None, "--cta", help="Call to action text"),
    platform: Optional[str] = typer.Option(None, "--platform", help="Advertising platform"),
    audience: Optional[str] = typer.Option(None, "--audience", help="Target audience"),
    goal: Optional[str] = typer.Option(None, "--goal", help="Campaign goal"),
    category: Optional[str] = typer.Option(None, "--category", help="Product category"),
    usp: Optional[str] = typer.Option(None, "--usp", help="Unique selling proposition"),
    competitor: Optional[str] = typer.Option(None, "--competitor", help="Competitor copy for comparison"),
    format: str = typer.Option("markdown", "--format", help="Output format: markdown, json, html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    batch: Optional[Path] = typer.Option(None, "--batch", help="Directory of JSON files for batch mode"),
) -> None:
    """Critique ad copy and receive structured performance feedback."""
    from agent import AdCopyInput, critique_ad, critique_batch

    if batch:
        # Batch mode
        json_files = sorted(batch.glob("*.json"))
        if not json_files:
            console.print(f"[red]No JSON files found in {batch}[/red]")
            raise typer.Exit(1)

        ads = []
        for jf in json_files:
            try:
                data = _load_input_file(jf)
                ads.append(AdCopyInput(**data))
            except Exception as e:
                console.print(f"[yellow]Skipping {jf.name}: {e}[/yellow]")

        if not ads:
            console.print("[red]No valid ad inputs found.[/red]")
            raise typer.Exit(1)

        console.print(f"[blue]Critiquing {len(ads)} ads...[/blue]")
        batch_result = critique_batch(ads)

        result_data = batch_result.model_dump()

        if format == "json":
            out_text = json.dumps(result_data, indent=2)
        else:
            lines = [f"# Batch Critique Report\n", f"**{batch_result.fleet_summary}**\n"]
            for i, (crit, ad) in enumerate(zip(batch_result.critiques, ads), 1):
                lines.append(f"\n---\n\n## Ad {i}: {ad.headline[:50]}")
                lines.append(_render_markdown(crit.model_dump()))
            out_text = "\n".join(lines)

        _output_result(out_text, output)
        return

    # Single ad mode
    if file:
        data = _load_input_file(file)
        if competitor:
            data["competitor_copy"] = competitor
        try:
            ad_input = AdCopyInput(**data)
        except Exception as e:
            console.print(f"[red]Invalid input: {e}[/red]")
            raise typer.Exit(1)
    elif headline:
        if not all([platform, audience, goal, category]):
            console.print(
                "[red]Inline mode requires --headline, --platform, --audience, --goal, --category[/red]"
            )
            raise typer.Exit(1)
        try:
            ad_input = AdCopyInput(
                headline=headline,
                body=body,
                cta=cta,
                platform=platform,
                target_audience=audience,
                campaign_goal=goal,
                product_category=category,
                usp=usp,
                competitor_copy=competitor,
            )
        except Exception as e:
            console.print(f"[red]Invalid input: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[red]Provide either --file or --headline with context flags.[/red]")
        raise typer.Exit(1)

    console.print("[blue]Analysing ad copy...[/blue]")

    try:
        result = critique_ad(ad_input)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if format == "json":
        out_text = result.model_dump_json(indent=2)
    elif format == "html":
        out_text = _render_html(result.model_dump(), title=f"Ad Critique: {ad_input.headline[:40]}")
    else:
        out_text = _render_markdown(result.model_dump())

    _output_result(out_text, output)

    if format == "markdown" and not output:
        console.print(Markdown(out_text))
    elif not output:
        console.print(out_text)


def _output_result(text: str, output: Optional[Path]) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        if not sys.stdout.isatty():
            print(text)


if __name__ == "__main__":
    app()
