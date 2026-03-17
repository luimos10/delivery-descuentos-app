import atexit
import os
import schedule
import sys
import time
from pathlib import Path
import msvcrt
from main import run

LOCK_FILE = Path(__file__).with_name(".scheduler.lock")


def acquire_single_instance_lock():

    lock_handle = open(LOCK_FILE, "a+")
    try:
        lock_handle.seek(0)
        msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("[scheduler] another scheduler instance is already running.", flush=True)
        lock_handle.close()
        sys.exit(1)

    lock_handle.seek(0)
    lock_handle.truncate()
    lock_handle.write(str(os.getpid()))
    lock_handle.flush()

    def release_lock():
        try:
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        lock_handle.close()

    atexit.register(release_lock)
    return lock_handle


_LOCK_HANDLE = acquire_single_instance_lock()


def run_job():

    try:
        print("[scheduler] running job...", flush=True)
        sent_count = run()
        print(f"[scheduler] job finished (new_sent={sent_count})", flush=True)
    except Exception as e:
        print(f"[scheduler] job failed: {e}", flush=True)


run_job()
schedule.every(24).hours.do(run_job)

while True:

    schedule.run_pending()
    time.sleep(60)
