import json
import os
import subprocess
import sys
from pathlib import Path


def test_login_endpoint_is_rate_limited():
    """TC-30x: repeated failed logins from the same client must eventually be throttled (429).

    Runs in a subprocess so flipping RATELIMIT_ENABLED doesn't touch the shared
    db/jwt/limiter singletons the rest of the suite depends on.
    """
    probe = Path(__file__).parent / '_rate_limit_probe.py'
    backend_dir = Path(__file__).parent.parent
    env = {**os.environ, 'PYTHONPATH': str(backend_dir)}
    result = subprocess.run(
        [sys.executable, str(probe)],
        cwd=backend_dir, env=env,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    statuses = json.loads(result.stdout.strip().splitlines()[-1])
    assert 429 in statuses
