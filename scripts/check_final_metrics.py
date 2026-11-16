"""Hand-calculated playback, startup, stall, seek and quality-change fixtures."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import math
from rl.metrics import evaluate_samples


def row(t, media, bitrate=600000, **kwargs):
    return dict(t_s=t, media_s=media, played_bitrate_bps=bitrate,
                latency_s=3., rate=1., **kwargs)


def main():
    uninterrupted = evaluate_samples([row(0, 0), row(1, 1), row(2, 2)])
    assert abs(uninterrupted['qoe_total']-math.log(2)) < 1e-9
    assert uninterrupted['stall_s'] == 0
    stalled = evaluate_samples([row(0, 0), row(1, 1), row(2, 1), row(3, 2)])
    assert stalled['stall_s'] == 1 and stalled['stall_count'] == 1
    assert abs(stalled['qoe_total']-(math.log(2)-4)) < 1e-9
    startup = evaluate_samples([row(0, 0), row(1, 0), row(2, 1)])
    assert startup['startup_s'] == 1 and startup['stall_s'] == 0
    partial = evaluate_samples([row(0, 0), row(1, .5), row(2, 1.5)])
    assert partial['startup_s'] == .5 and partial['stall_s'] == 0
    quantized = evaluate_samples([row(0, 0), row(1, 1), row(2, 1.99, waiting=False)])
    assert quantized['stall_s'] == 0
    switched = evaluate_samples([row(0, 0), row(1, 1, 1200000), row(2, 2, 1200000)])
    assert switched['switches'] == 1 and abs(switched['variation']-math.log(2)) < 1e-9
    seek = evaluate_samples([row(0, 0), row(1, 1), row(2, 21, seek_epoch=1), row(3, 22, seek_epoch=1)])
    assert seek['skipped_media_s'] == 20 and seek['played_media_s'] == 2
    initial_live = evaluate_samples([row(0, 0), row(1, 1700000000, seek_epoch=1), row(2, 1700000001, seek_epoch=1)])
    assert initial_live['skipped_media_s'] == 0 and initial_live['startup_s'] == 1
    paused = evaluate_samples([row(0, 0, paused=True), row(1, 0), row(2, 1)])
    assert paused['stall_s'] == paused['startup_s'] == 0
    try:
        evaluate_samples([row(1, 1), row(0, 0)])
        raise AssertionError('Non-monotone time accepted')
    except ValueError:
        pass
    print('PASS: hand-calculated played utility, stall/startup, switch, seek, pause and invalid-time fixtures')


if __name__ == '__main__':
    main()
