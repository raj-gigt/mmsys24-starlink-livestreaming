"""Generate an SVG timeline from a browser trial's saved JSON files."""
import argparse
import json
from datetime import datetime
from html import escape
from pathlib import Path


def plot_run(run_dir):
    run_dir = Path(run_dir)
    summary = json.loads((run_dir / 'summary.json').read_text())
    samples = json.loads((run_dir / 'samples.json').read_text())
    duration = max(1, summary['requested_seconds'])
    stages = summary.get('controlled_stages', [])
    ladder = {r['qualityIndex']: r['bitrate'] / 1e6 for r in summary.get('ladder', [])}
    elapsed = lambda sample: sample['elapsed_s']
    last = samples[-1] if samples else {}
    decisions = last.get('decisions', [])
    offset = None
    # The runner starts timing immediately after the load click.
    if summary.get('load_wall_clock_utc'):
        offset = datetime.fromisoformat(summary['load_wall_clock_utc']).timestamp()
    elif decisions:
        offset = decisions[0]['at_ms'] / 1000

    selected = [(r['at_ms'] / 1000 - offset, r['bitrate_bps'] / 1e6) for r in decisions]
    if selected:
        selected.append((duration, selected[-1][1]))
    throughput = [(r['at_ms'] / 1000 - offset, r['observation']['history'][-1]['mbps'])
                  for r in decisions if r['observation']['history']]
    if not throughput:
        for r in last.get('requests', []):
            if r.get('type') != 'MediaSegment' or r.get('code') != 200 or not all(r.get(k) for k in ('start','finish','bytes')) or offset is None:
                continue
            start, end = (datetime.fromisoformat(r[k].replace('Z', '+00:00')).timestamp() for k in ('start','finish'))
            if end > start:
                throughput.append((end-offset, r['bytes'] * 8 / (end-start) / 1e6))

    capacity = [(r['at_s'], r['rate_mbit']) for r in stages]
    if capacity:
        capacity.append((duration, capacity[-1][1]))
    panels = [
        ('Network rate (Mbps)', [('Configured capacity', capacity, '#334e68', True),
                                  ('Completed download throughput', throughput, '#007e9a', False)], None),
        ('Video bitrate (Mbps)', [('Selected bitrate', selected, '#6544ad', True)] if selected else
         [('Sampled player quality', [(elapsed(s), ladder.get(s.get('quality'))) for s in samples], '#6544ad', True)], None),
        ('Playable buffer (s)', [('Sampled buffer', [(elapsed(s), s.get('buffer')) for s in samples], '#007e9a', False)], None),
        ('Live latency (s)', [('Sampled latency', [(elapsed(s), s.get('latency')) for s in samples], '#6544ad', False)],
         summary.get('target_latency_s')),
    ]

    left, right = 84, 904
    def x(t):
        return left + (right - left) * min(duration, max(0, t)) / duration

    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="722" viewBox="0 0 960 722">',
           '<rect width="960" height="722" fill="#fafbfc"/>']

    def label(px, py, value, size=13, anchor='start', color='#24354b'):
        svg.append(f'<text x="{px}" y="{py}" text-anchor="{anchor}" fill="{color}" '
                   f'font-family="system-ui,sans-serif" font-size="{size}">{escape(str(value))}</text>')

    def line(x1, y1, x2, y2, color, dash=''):
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                   f'stroke="{color}" stroke-dasharray="{dash}"/>')

    label(48, 42, f"{summary['algorithm']} · browser trial", 24)
    label(48, 68, summary['run_id'])
    if capacity:
        min_rate = min(v for _, v in capacity)
        for (start, rate), (end, _) in zip(capacity, capacity[1:]):
            if end <= start:
                continue
            label((x(start) + x(end)) / 2, 100, f'{rate:g} Mbps capacity', 12, 'middle')
            if rate == min_rate and rate < max(v for _, v in capacity):
                svg.append(f'<rect x="{x(start)}" y="111" width="{x(end)-x(start)}" height="529" fill="#fff0d7"/>')
    else:
        label(48, 100, 'Trace replay · configured capacity stages not recorded')

    for i, (title, series, target) in enumerate(panels):
        top = 131 + i * 128
        values = [v for _, points, _, _ in series for _, v in points if v is not None]
        limit = max([1, target or 0, *values]) * 1.08
        def y(v):
            return top + 107 - 80 * max(0, v) / limit
        label(left, top, title, 15)
        for tick in range(5):
            v = tick * limit / 4
            line(left, y(v), right, y(v), '#dbe3ed')
            label(left-9, y(v)+4, f'{v:.2g}', 11, 'end')
        for t, _ in capacity[1:-1]:
            line(x(t), top+26, x(t), top+107, '#9b742e', '4 4')
        if target is not None:
            line(left, y(target), right, y(target), '#9b742e', '5 4')
            label(right, y(target)-4, f'{target:g} s target', 11, 'end')
        for j, (name, points, color, step) in enumerate(series):
            label(right-j*200, top, name if points else f'{name} unavailable', 11, 'end', color)
            commands = []
            for t, v in sorted(points, key=lambda p: p[0]):
                if v is None:
                    continue
                xx, yy = x(t), y(v)
                commands.append(f'M{xx:.2f} {yy:.2f}' if not commands else
                                f'H{xx:.2f} V{yy:.2f}' if step else f'L{xx:.2f} {yy:.2f}')
            if commands:
                svg.append(f'<path d="{" ".join(commands)}" fill="none" stroke="{color}" stroke-width="2.5"/>')
    for i in range(11):
        t = i * duration / 10
        label(x(t), 659, f'{t:g}', 11, 'middle')
    label((left+right)/2, 684, 'Trial time (seconds)', 13, 'middle')
    label(48, 708, 'Source: summary.json and samples.json · decision timestamps aligned approximately', 11)
    output = run_dir / 'run-timeline.svg'
    output.write_text(''.join(svg) + '</svg>', encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    print(plot_run(parser.parse_args().run_dir))
