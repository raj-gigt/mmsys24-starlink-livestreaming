"""Verify actual schedule evaluator, including outages, boundaries and bad input."""
import importlib.util
from pathlib import Path

p = Path(__file__).resolve().parents[1]/'shaper/tc-final.py'
spec = importlib.util.spec_from_file_location('final_shaper', p)
shaper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shaper)
profile = {'start_at_unix_s': 1000, 'stages': [
    {'at_s': 0, 'rate_mbit': 8, 'delay_ms': 40, 'loss_percent': 0},
    {'at_s': 10, 'rate_mbit': 0, 'delay_ms': 100},
    {'at_s': 13, 'rate_mbit': 2, 'delay_ms': 60, 'loss_percent': 0}]}
assert shaper.profile_values(profile, 999, (20, 1, 1)) == (8, 40, 0)
assert shaper.profile_values(profile, 1009.99, (20, 1, 1)) == (8, 40, 0)
assert shaper.profile_values(profile, 1010, (20, 1, 1)) == (.05, 100, 100)
assert shaper.profile_values(profile, 1013, (20, 1, 1)) == (2, 60, 0)
assert shaper.profile_values({'rate_mbit': 3}, 10, (20, 40, 0)) == (3, 40, 0)
try:
    shaper.profile_values({'rate_mbit': -1}, 10, (20, 40, 0))
    raise AssertionError('Invalid rate accepted')
except AssertionError as exc:
    assert str(exc) != 'Invalid rate accepted'
print('PASS: actual profile evaluator boundary, outage, recovery, legacy and invalid-input fixtures')
