#!/usr/bin/env python3
"""Offline structural verification of a G1 approved visual baseline.

This checks local evidence, never attempts to verify remote Figma links, approvals or
human perception. It must not be presented as behavioral AI/design certification.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

IMAGE_PATTERN = re.compile(r'!\[([^\]]+)\]\(([^)]+)\)')
PLACEHOLDER = re.compile(r'\{\{[^}]+\}\}')


def validate_baseline(file: Path, *, approved: bool = False):
    errors, warnings = [], []
    if not file.is_file():
        return [f'Missing baseline: {file}'], warnings
    raw = file.read_text(encoding='utf-8')
    # Ignore fenced and inline-code examples: Markdown displays those literally.
    visible_lines = []
    in_fence = False
    for line in raw.splitlines():
        if re.match(r'^\s*(`{3,}|~{3,})', line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        visible_lines.append(re.sub(r'`[^`]*`', '', line))
    images = list(IMAGE_PATTERN.finditer('\n'.join(visible_lines)))
    if not images:
        errors.append('No embedded Markdown images found; links or backticks are not image previews')
    for match in images:
        alt, target = match.groups()
        if not alt.strip():
            errors.append('Image without alt text')
        if '://' in target or target.startswith('data:'):
            warnings.append(f'Nonlocal image cannot be verified offline: {target}')
            continue
        rel = target.split('#', 1)[0].split('?', 1)[0]
        image_path = (file.parent / rel).resolve()
        if not image_path.is_relative_to(file.parent.resolve()):
            errors.append(f'Image escapes baseline directory: {target}')
        elif not image_path.is_file():
            errors.append(f'Broken preview image: {target}')
    if approved:
        if PLACEHOLDER.search(raw):
            errors.append('An approved baseline still contains template placeholders')
        if not re.search(r'\bG1\b', raw):
            errors.append('Missing explicit G1 reference')
        if not re.search(r'(?i)\bapproved\b|\baprovad[oa]\b', raw):
            errors.append('No explicit approved status')
        if not re.search(r'\bG2\b', raw):
            errors.append('G2 boundary must be stated (G1 is not G2)')
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path, help='Path to populated approved visual baseline Markdown')
    parser.add_argument('--approved', action='store_true', help='Require approved-G1 fields and no template placeholders')
    args = parser.parse_args()
    errors, warnings = validate_baseline(args.baseline, approved=args.approved)
    for warning in warnings:
        print(f'WARN: {warning}')
    for error in errors:
        print(f'ERROR: {error}')
    print(f'G1 baseline validation: {"PASS" if not errors else "FAIL"} ({len(errors)} errors, {len(warnings)} warnings)')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
