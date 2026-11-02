"""Owned Windows process jobs, copied from project tooling with provenance."""
import ctypes
from ctypes import wintypes
import subprocess
import sys
import time

def resume_owned_primary_thread(process):
    """Recover Popen's discarded primary-thread handle while its child is suspended."""
    class ThreadEntry(ctypes.Structure):
        _fields_ = [(name, wintypes.DWORD) for name in
                    ("size", "usage", "tid", "pid", "base_priority", "delta_priority", "flags")]

    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    api.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    api.Thread32First.argtypes = api.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
    api.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenThread.restype = wintypes.HANDLE
    api.GetProcessIdOfThread.argtypes = [wintypes.HANDLE]
    api.GetProcessIdOfThread.restype = wintypes.DWORD
    api.ResumeThread.argtypes = [wintypes.HANDLE]
    api.ResumeThread.restype = wintypes.DWORD
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = api.CreateToolhelp32Snapshot(0x4, 0)  # TH32CS_SNAPTHREAD
    if snapshot == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = ThreadEntry()
        entry.size = ctypes.sizeof(entry)
        threads = []
        found = api.Thread32First(snapshot, ctypes.byref(entry))
        while found:
            if entry.pid == process.pid:
                threads.append(entry.tid)
            found = api.Thread32Next(snapshot, ctypes.byref(entry))
        if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        api.CloseHandle(snapshot)
    if len(threads) != 1 or process.poll() is not None:
        raise ValueError("Suspended owned child does not have exactly one initial thread")
    thread = api.OpenThread(0x0002 | 0x0800, False, threads[0])  # SUSPEND_RESUME | QUERY_LIMITED_INFORMATION
    if not thread:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if api.GetProcessIdOfThread(thread) != process.pid:
            raise ValueError("Initial thread no longer belongs to the owned child")
        previous = api.ResumeThread(thread)
        if previous != 1:
            raise ValueError("Owned primary thread has unexpected suspend count: " + str(previous))
    finally:
        api.CloseHandle(thread)

def spawn_owned(command, job=None, **kwargs):
    """Never run Windows application code until this exact child belongs to its job."""
    process = None
    try:
        if job is not None and any(item._cleanup_failed for item in WindowsOwnedJob._active_jobs):
            raise ValueError("An owned job still has unresolved cleanup; retry its close before launching")
        flags = kwargs.pop("creationflags", 0)
        process = subprocess.Popen(command, creationflags=flags | (0x4 if job is not None else 0), **kwargs)
        if job is not None:
            job._starting_process = process
            job.assign(process)
            resume_owned_primary_thread(process)
            job._starting_process = None
        return process
    except BaseException:
        try:
            if job is not None:
                job.close()  # Also reaps an unassigned suspended child and drains assigned descendants.
        finally:
            if process is not None:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()
        raise

class WindowsOwnedJob:
    """Killing/closing this job affects only the assigned preview and descendants."""

    _active_jobs = set()  # Retain recoverable ownership if a caller's cleanup raises.

    def __init__(self):
        if sys.platform != "win32":
            raise ValueError("Persistent native preview currently requires Windows")
        api = ctypes.windll.kernel32
        class BasicLimits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                ("flags", wintypes.DWORD), ("min_working", ctypes.c_size_t), ("max_working", ctypes.c_size_t),
                ("active_limit", wintypes.DWORD), ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]
        class IOCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("basic", BasicLimits), ("io", IOCounters), ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        api.CreateJobObjectW.restype = wintypes.HANDLE
        api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        api.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
        api.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        api.WaitForSingleObject.restype = wintypes.DWORD
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api, self.handle = api, api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError()
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            api.CloseHandle(self.handle)
            self.handle = None
            raise ctypes.WinError()
        self._starting_process = None
        self._cleanup_failed = False
        self._active_jobs.add(self)

    def assign(self, process) -> None:
        if not self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))):
            raise ctypes.WinError()

    def pids(self) -> list[int]:
        pids = []
        if self.handle:
            buffer = ctypes.create_string_buffer(8192)
            if not self.api.QueryInformationJobObject(self.handle, 3, buffer, len(buffer), None):
                raise ctypes.WinError()
            count = ctypes.c_uint32.from_buffer(buffer, 4).value
            pids = list((ctypes.c_size_t * count).from_buffer(buffer, 8))
        starting = self._starting_process
        if starting is not None and starting.poll() is None and starting.pid not in pids:
            pids.append(starting.pid)
        return pids

    def close(self) -> None:
        try:
            self._close()
        except BaseException as error:
            self._cleanup_failed = True
            error.owned_job = self
            raise

    def _remember_members(self, pids, failures) -> None:
        pending = self.__dict__.setdefault("_pending_handles", {})
        for pid in pids:
            process, record = next(((handle, item) for handle, item in pending.items() if item["pid"] == pid), (None, None))
            if record is not None and record["owned"] is not None:
                continue  # An open process handle pins identity; never reopen a saved PID on retry.
            try:
                if record is None:
                    process = self.api.OpenProcess(0x00101000, False, pid)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
                    if not process:
                        if self.api.GetLastError() == 87:  # Already exited.
                            continue
                        raise ctypes.WinError()
                    record = {"pid": pid, "owned": None, "exited": False}
                    pending[process] = record
                member = wintypes.BOOL()
                if not self.api.IsProcessInJob(process, self.handle, ctypes.byref(member)):
                    raise ctypes.WinError()
                if not member.value and record.get("verification_failed"):
                    raise ValueError("Original process ownership could not be recovered; cleanup is incomplete")
                record["owned"] = bool(member.value)
            except Exception as error:
                if record is not None:
                    record["verification_failed"] = True
                failures.append(error)

    def _close(self) -> None:
        failures = []
        pending = self.__dict__.setdefault("_pending_handles", {})
        try:
            self._remember_members(self.pids(), failures)
        except Exception as error:
            failures.append(error)
        try:
            if self.handle and not self.api.TerminateJobObject(self.handle, 1):
                raise ctypes.WinError()
        except Exception as error:
            failures.append(error)
        try:
            starting = self._starting_process
            if starting is not None:
                if starting.poll() is None:
                    starting.kill()
                starting.wait(timeout=10)
                self._starting_process = None
        except Exception as error:
            failures.append(error)
        try:
            deadline = time.monotonic() + 10
            while True:
                pids = self.pids()
                self._remember_members(pids, failures)
                if not pids:
                    break
                if time.monotonic() >= deadline:
                    raise ValueError("Owned process job did not empty; cleanup is incomplete")
                time.sleep(.02)
        except Exception as error:
            failures.append(error)
        # Membership can empty before exit signals. Failed waits and failed
        # handle closes stay on this job across every subsequent close attempt.
        for process, record in list(pending.items()):
            try:
                if record["owned"] is None:
                    raise ValueError("Process ownership remains unverified; cleanup is incomplete")
                if record["owned"] and not record["exited"]:
                    remaining = max(0, int((deadline - time.monotonic()) * 1000))
                    if self.api.WaitForSingleObject(process, remaining) != 0:
                        raise ValueError("Owned process exit did not signal; cleanup is incomplete")
                    record["exited"] = True
                if not self.api.CloseHandle(process):
                    raise ctypes.WinError()
                del pending[process]
            except Exception as error:
                failures.append(error)
        if not failures and (pending or self._starting_process is not None):
            failures.append(ValueError("Owned cleanup obligations remain; cleanup is incomplete"))
        if not failures:
            try:
                if self.handle and not self.api.CloseHandle(self.handle):
                    raise ctypes.WinError()
                self.handle = None
            except Exception as error:
                failures.append(error)
        if failures:
            error = failures[0]
            for extra in failures[1:]:
                error.add_note("Additional owned cleanup failure: " + str(extra))
            raise error
        self._cleanup_failed = False
        self._active_jobs.discard(self)
