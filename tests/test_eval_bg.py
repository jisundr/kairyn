"""evals/bg.py: an eval run that outlives the agent that started it, and a wait that reports DONE, RUNNING or DIED."""
import os
import signal
import sys
import time

from bg import start, wait

SUMMARY = "== eval summary =="


def fake(root, script):
    """A stand-in for run.py: a python one-liner run in the repo root."""
    return [sys.executable, "-c", script]


def test_wait_reports_done_with_the_new_run_id(tmp_path):
    (tmp_path / "evals" / "results" / "20260101T000000Z").mkdir(parents=True)   # an older run
    script = ("import os,time; os.makedirs('evals/results/20260102T000000Z'); time.sleep(0.3); "
              f"print('{SUMMARY}', flush=True)")
    start(tmp_path, fake(tmp_path, script))
    out = wait(tmp_path, timeout=10, poll=0.1)
    assert out == "DONE 20260102T000000Z", out


def test_wait_reports_running_at_its_timeout(tmp_path):
    start(tmp_path, fake(tmp_path, "import time; time.sleep(5)"))
    out = wait(tmp_path, timeout=0.5, poll=0.1)
    assert out.startswith("RUNNING"), out


def test_wait_reports_died_with_the_log_tail(tmp_path):
    start(tmp_path, fake(tmp_path, "print('boom: no promptfoo', flush=True); raise SystemExit(3)"))
    out = wait(tmp_path, timeout=10, poll=0.1)
    assert out.startswith("DIED") and "boom: no promptfoo" in out, out


def test_wait_reports_done_without_a_folder_when_all_evals_skipped(tmp_path):
    start(tmp_path, fake(tmp_path, f"print('{SUMMARY}'); print('exit: skipped (dependencies unchanged)')"))
    assert wait(tmp_path, timeout=10, poll=0.1) == "DONE skipped"


def test_the_run_is_its_own_session(tmp_path):
    """Detached: killing the starter's process group (the agent's Bash) does not kill the run."""
    pid = start(tmp_path, fake(tmp_path, "import time; time.sleep(3)"))
    try:
        assert os.getsid(pid) == pid
        assert os.getpgid(pid) != os.getpgid(os.getpid())
    finally:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.1)
