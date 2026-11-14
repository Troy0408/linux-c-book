#!/usr/bin/env python3
"""Validate local images and derive lossless PNGs from GIFs.

Writes only images/derived/<original-relative-path>.gif.png; the source remains
untouched. Multi-frame GIFs are reported and not silently flattened.
"""
from pathlib import Path
import argparse
import sys
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='report without writing PNGs')
    args = parser.parse_args()
    root = ROOT / 'images'
    files = sorted(p for p in root.rglob('*') if p.is_file() and 'derived' not in p.relative_to(root).parts)
    failed = animated = derived = 0
    for p in files:
        rel = p.relative_to(root)
        try:
            with Image.open(p) as image:
                image.load()
                fmt, size = image.format, image.size
                frames = getattr(image, 'n_frames', 1)
                dpi = image.info.get('dpi')
                notes = []
                if max(size) > 5000 or size[0] * size[1] > 25_000_000:
                    notes.append('large')
                if p.suffix.lower() == '.png' and fmt != 'PNG':
                    notes.append('extension/format mismatch')
                    failed += 1
                if fmt == 'GIF':
                    if frames != 1:
                        animated += 1
                        notes.append('animated: not converted')
                    else:
                        dest = root / 'derived' / (str(rel) + '.png')
                        notes.append('derived=' + str(dest.relative_to(root)))
                        if not args.check:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            # RGBA retains palette transparency; no resampling.
                            image.convert('RGBA').save(dest, format='PNG')
                            with Image.open(dest) as result:
                                result.load()
                                if result.size != size:
                                    raise ValueError('converted dimensions differ')
                            derived += 1
                print(f'{rel}: {fmt} {size[0]}x{size[1]} dpi={dpi} frames={frames}' + (' [' + ', '.join(notes) + ']' if notes else ''))
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            failed += 1
            print(f'{rel}: ERROR {exc}', file=sys.stderr)
    print(f'Total={len(files)} converted={derived} animated={animated} errors={failed}')
    return 1 if failed or animated else 0


if __name__ == '__main__':
    sys.exit(main())
