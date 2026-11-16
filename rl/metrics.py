"""Common offline outcome ledger; independent of a controller's internal reward.

Samples describe the interval START state. Media advancement is integrated over
wall time, deliberate pause/seek is excluded, startup and stalls are separate.
"""
import math
import numpy as np


def evaluate_samples(samples, target=3.0, horizon=None):
    collapsed = []
    for sample in samples:
        if collapsed and sample['t_s'] < collapsed[-1]['t_s']:
            raise ValueError('Sample times must increase')
        if collapsed and sample['t_s'] == collapsed[-1]['t_s']:
            collapsed[-1] = sample  # zero-time event boundary: last state wins
        else:
            collapsed.append(sample)
    samples = collapsed
    if len(samples) < 2:
        raise ValueError('At least two timestamped samples required')
    totals = dict(quality_utility=0., stall_s=0., startup_s=0., variation=0.,
                  latency_area=0., played_media_s=0., unattributed_media_s=0., skipped_media_s=0., switches=0)
    started = False
    previous_bitrate = None
    latencies, latency_weights = [], []
    played_bitrate_sum = 0.
    stall_count = 0
    was_stalled = False
    for a, b in zip(samples, samples[1:]):
        dt = float(b['t_s']) - float(a['t_s'])
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('Sample times must increase')
        latency = a.get('latency_s')
        if latency is not None and math.isfinite(latency):
            totals['latency_area'] += max(0, latency-target)*dt
            latencies.append(latency)
            latency_weights.append(dt)
        if a.get('paused') or a.get('seeking'):
            was_stalled = False
            continue
        delta = max(0., float(b['media_s']) - float(a['media_s']))
        rate = max(.01, float(a.get('rate', 1.)))
        if b.get('seek_epoch', 0) != a.get('seek_epoch', 0) or delta > dt*rate + .25:
            # Initial live positioning can jump from zero to epoch media time.
            # This is startup, not billions of seconds of discarded content.
            if started:
                totals['skipped_media_s'] += delta
            else:
                totals['startup_s'] += dt
            was_stalled = False
            continue
        was_started = started
        played_wall = min(dt, delta/rate)
        if delta > 1e-5:
            started = True
            bitrate = a.get('played_bitrate_bps')
            if bitrate is None or bitrate <= 0:
                totals['unattributed_media_s'] += delta
            else:
                utility = math.log(bitrate/300000.)
                totals['quality_utility'] += utility*delta/2
                played_bitrate_sum += bitrate*delta
                if previous_bitrate is not None and bitrate != previous_bitrate:
                    totals['variation'] += abs(math.log(bitrate/previous_bitrate))
                    totals['switches'] += 1
                previous_bitrate = bitrate
            totals['played_media_s'] += delta
        idle = max(0., dt-played_wall)
        if not was_started:
            totals['startup_s'] += idle
        else:
            # Playback clocks are quantized. Minor clock drift while playing
            # is not a stall; prefer the collector's actual waiting state.
            stalled = bool(a.get('waiting', delta <= 1e-5)) and idle > .02
            totals['stall_s'] += idle if stalled else 0
            stall_count += int(stalled and not was_stalled)
            was_stalled = stalled
    duration = float(samples[-1]['t_s'])-float(samples[0]['t_s'])
    if horizon is not None and abs(duration-horizon) > .5:
        raise ValueError('Incomplete observation horizon')
    qoe = totals['quality_utility']-4*totals['stall_s']-totals['startup_s']-.3*totals['variation']-.1*totals['latency_area']
    if latencies:
        order = np.argsort(latencies)
        vals = np.array(latencies)[order]
        weights = np.array(latency_weights)[order]
        mean_latency = float(np.average(vals, weights=weights))
        p95 = float(vals[np.searchsorted(np.cumsum(weights), .95*sum(weights))])
    else:
        mean_latency = p95 = None
    return {**totals, 'duration_s': duration, 'stall_count': stall_count,
            'quality_attribution_fraction': 1-totals['unattributed_media_s']/max(totals['played_media_s'],1e-9),
            'played_bitrate_bps': played_bitrate_sum/max(totals['played_media_s']-totals['unattributed_media_s'], 1e-9),
            'mean_live_latency_s': mean_latency, 'p95_live_latency_s': p95,
            'qoe_total': qoe, 'qoe_per_wall_s': qoe/duration}
