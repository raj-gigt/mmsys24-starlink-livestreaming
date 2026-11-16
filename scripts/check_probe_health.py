"""Run in the stats-server container: preserve legacy RTT but reject stale health."""
import subprocess
from unittest.mock import patch
import app as server

client = server.app.test_client()
assert client.get('/ping').json == 0
assert client.get('/ping/details').json['valid'] is False
with patch.object(server.subprocess, 'check_output', return_value=b'64 bytes: icmp_seq=1 ttl=64 time=42.1 ms'):
    server.py_ping('nginx')
assert client.get('/ping').json == 42.1
assert client.get('/ping/details').json['valid'] is True
with patch.object(server.subprocess, 'check_output', side_effect=subprocess.CalledProcessError(1, 'ping', b'loss')):
    server.py_ping('nginx')
assert client.get('/ping').json == 42.1, 'Legacy scalar must remain unchanged on loss'
assert client.get('/ping/details').json['valid'] is False
server.probe_health['success_at_s'] -= 10
server.probe_health['ok'] = True
assert client.get('/ping/details').json['valid'] is False
print('PASS: actual Flask routes, missing probe, success, failed probe and stale timestamp; legacy scalar preserved')
