"""Contract and subprocess tests without torch, weights or a GPU.

Run: python3 -m unittest discover -s integrations/effectcraft -p 'test_*.py' -v
"""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from bridge import Bridge, Handler, Jobs, MAX_LINE, publish_connection, describe_progress, explain_failure


class FakeWorker:
    loaded=False
    loads=0
    mode='success'
    active=0
    maximum=0
    def run(self,spec,cancel):
        self.active+=1
        self.maximum=max(self.maximum,self.active)
        try:
            folder=Path(spec['folder'])
            (folder/'inference.log').write_text('worker started', encoding='utf-8')
            if self.mode=='slow': cancel.wait(4)
            if cancel.is_set(): raise InterruptedError('cancelled')
            if self.mode=='error':
                (folder/'inference.log').write_text('CUDA test failure', encoding='utf-8')
                raise RuntimeError('CUDA test failure')
            output=folder/'cutout.mov'
            if self.mode!='missing': output.write_bytes(b'fake movie')
            return dict(ok=True,output=str(output))
        finally: self.active-=1
    def close(self): pass
    def release(self): self.loaded=False


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="corridorkey-test-")
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'clip with ünicode $(echo nope).mp4'
        self.source.write_bytes(b"test input")
        self.fake = FakeWorker()
        self.jobs = Jobs(self.root, self.root / "outputs", worker=self.fake)
        self.bridge = Bridge(self.jobs, "test-token")
        self.worker("success")

    def tearDown(self):
        self.bridge.close()
        self.jobs.close()
        self.temp.cleanup()

    def worker(self, mode):
        self.fake.mode = mode

    def request(self, method, params=None, token="test-token"):
        return self.bridge.dispatch({"method": method, "params": params or {}, "token": token})

    def wait(self, job_id):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = self.jobs.status(job_id)
            if status["state"] in {"failed", "completed", "cancelled"} and self.jobs.active is None:
                return status
            time.sleep(0.01)
        self.fail("Job did not terminate")

    def test_success_unicode_and_literal_shell_characters(self):
        job = self.request("submit", {"input": str(self.source), "despill": 0.7})
        status = self.wait(job["id"])
        self.assertEqual(status["state"], "completed")
        self.assertTrue(Path(status["output"]).is_file())
        self.assertIn("worker started", status["detail"])
        self.assertEqual(status["input"], str(self.source))

    def test_failed_inference_and_missing_result(self):
        for mode in ("error", "missing"):
            self.worker(mode)
            status = self.wait(self.request("submit", {"input": str(self.source)})["id"])
            self.assertEqual(status["state"], "failed")
            self.assertIsNone(status["output"])
            self.assertTrue(status["error"])
            if mode == "error":
                self.assertIn("CUDA test failure", status["detail"])

    def test_serial_queue_cancel_and_next_job(self):
        self.worker("slow")
        first = self.request("submit", {"input": str(self.source)})
        deadline=time.monotonic()+3
        while self.jobs.active is None and time.monotonic()<deadline: time.sleep(.01)
        second = self.request("submit", {"input": str(self.source)})
        self.assertEqual(second["state"],"queued")
        self.request("cancel", {"id":second["id"]})
        self.assertEqual(self.jobs.status(second["id"])["state"],"cancelled")
        self.request("cancel", {"id":first["id"]})
        self.assertEqual(self.wait(first["id"])["state"],"cancelled")
        self.worker("success")
        next_job=self.request("submit", {"input":str(self.source)})
        self.assertEqual(self.wait(next_job["id"])["state"],"completed")
        self.assertEqual(self.fake.maximum,1)

    def test_batch_is_atomic_and_recovery_preserves_results(self):
        with self.assertRaises(ValueError): self.request("submit_batch", {"items":[{"input":str(self.source)},{"input":"bad.mp4"}]})
        self.assertEqual(len(self.jobs.jobs),0)
        jobs=self.request("submit_batch", {"items":[{"input":str(self.source)},{"input":str(self.source)}]})
        for job in jobs: self.wait(job["id"])
        self.jobs.close()
        self.jobs=Jobs(self.root,self.root/"outputs",worker=self.fake)
        self.bridge.jobs=self.jobs
        self.assertEqual(len(self.request("queue")),2)
        self.assertTrue(all(j["state"]=="completed" for j in self.request("queue")))
        self.assertEqual(self.fake.maximum,1)

    def test_manifest_write_failure_does_not_leave_an_invisible_queue(self):
        with patch.object(self.jobs,"_persist",side_effect=OSError("No space left on device")):
            with self.assertRaises(OSError): self.request("submit_batch",{"items":[{"input":str(self.source)}]})
        self.assertEqual(self.jobs.jobs,{})
        self.assertEqual(list(self.jobs.output_root.iterdir()),[])
        self.assertIsNone(self.jobs.active)

    def test_retry_preserves_original_and_can_change_settings(self):
        self.worker("error")
        old=self.request("submit",{"input":str(self.source),"despill":.25})
        self.wait(old['id']);self.worker("success")
        fresh=self.request("retry",{"id":old['id'],"changes":{"despill":1}})
        self.assertNotEqual(fresh['id'],old['id'])
        self.assertEqual(self.wait(fresh['id'])['state'],'completed')
        self.assertEqual(self.request("job.options",{"id":fresh['id']})['despill'],1)
        self.assertEqual(self.request("job.options",{"id":old['id']})['despill'],.25)
        self.assertEqual(self.jobs.status(old['id'])['state'],'failed')

    def test_missing_cache_cannot_refine_or_change_inference_parameters(self):
        old=self.request("submit",{"input":str(self.source)});self.wait(old['id'])
        with self.assertRaisesRegex(ValueError,"Korrekturdaten"):
            self.request("refine",{"id":old['id'],"changes":{"matte_expand":1}})
        with self.assertRaises(ValueError):
            self.request("refine",{"id":old['id'],"changes":{"range_start":5}})
        self.assertEqual(len(self.jobs.jobs),1)

    def test_shutdown_stops_running_child(self):
        self.worker("slow")
        job = self.request("submit", {"input": str(self.source)})
        self.jobs.close()
        self.assertEqual(self.wait(job["id"])["state"], "cancelled")

    def test_invalid_requests_never_start_inference(self):
        for request in (None, [], {}, {"token": []}, {"token": "wrong"},
                        {"token": "test-token", "params": []}):
            with self.assertRaises(ValueError):
                self.bridge.dispatch(request)
        for options in ({"input": "relative.mp4"}, {"input": str(self.root)},
                        {"input": str(self.source), "despill": float("nan")},
                        {"input": str(self.source), "low_vram": "false"},
                        {"input": str(self.source), "python": "arbitrary-command"}):
            with self.assertRaises(ValueError):
                self.request("submit", options)
        self.assertIsNone(self.jobs.active)

    def test_hint_and_memory_flags(self):
        hint = self.root / "hint.png"
        hint.write_bytes(b"png")
        job = self.request("submit", {"input": str(self.source), "hint": str(hint), "low_vram": True})
        self.wait(job["id"])
        options = self.jobs.jobs[job["id"]]["options"]
        self.assertTrue(options["low_vram"])
        self.assertEqual(options["hint"], str(hint))

    def test_protocol_rejects_http_oversize_and_bad_json(self):
        import io
        from types import SimpleNamespace
        for raw in (b"GET / HTTP/1.1\r\n", b"[]\n", b"x" * (MAX_LINE + 1), b"{}"):
            handler = object.__new__(Handler)
            handler.rfile, handler.wfile = io.BytesIO(raw), io.BytesIO()
            handler.connection = SimpleNamespace(settimeout=lambda value: None)
            handler.server = SimpleNamespace(bridge=self.bridge)
            handler.handle()
            self.assertFalse(json.loads(handler.wfile.getvalue())["ok"])
        raw = json.dumps({"method": "hello", "token": "test-token"}).encode() + b"\n"
        handler.rfile, handler.wfile = io.BytesIO(raw), io.BytesIO()
        handler.handle()
        self.assertEqual(json.loads(handler.wfile.getvalue())["result"]["api"], 1)

    def test_spawn_failure_is_reported(self):
        with patch.object(self.fake, "run", side_effect=OSError("Python not found")):
            job = self.request("submit", {"input": str(self.source)})
            self.assertIn("Python not found", self.wait(job["id"])["error"])

    def test_connection_file_is_private_and_replaced_on_restart(self):
        path = self.root / "config/connection.json"
        publish_connection(path, 9878, "first-token")
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))["token"], "first-token")
        import os
        if os.name != "nt":
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        publish_connection(path, 9879, "second-token")
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))["port"], 9879)
        self.assertEqual(len(list(path.parent.iterdir())), 1)

    def test_human_progress_and_actionable_failure(self):
        phase = describe_progress("Loading CorridorKey v2 runtime weights", "running")
        self.assertIn("KI-Modelle", phase["label"])
        phase = describe_progress("window 1/8\nwindow 2/8", "running")
        self.assertEqual((phase["done"], phase["total"]), (2, 8))
        self.assertIsNone(describe_progress("window 2/8", "completed")["done"])
        self.assertIn("Speichersparend", explain_failure("CUDA out of memory", None))
        self.assertIn("Speicherplatz", explain_failure("No space left on device", None))

    def test_installer_embeds_location_but_no_token(self):
        from install import install
        panel = install(self.root / "effectcraft")
        content = panel.read_text(encoding='utf-8')
        self.assertIn("CORRIDORKEY_CONNECTION_FILE", content)
        self.assertNotIn("test-token", content)
        self.assertFalse(panel.with_suffix(".jsx.bak").exists())
        install(self.root / "effectcraft")
        self.assertFalse(panel.with_suffix(".jsx.bak").exists())

    def test_heartbeat_only_targets_our_named_control(self):
        from bridge import pulse_panels
        writes = []
        replies = iter([
            {"ok": True, "result": [{"window": 1, "title": "Other Tool"}, {"window": 2, "title": "CorridorKey"}]},
            {"ok": True, "result": {"root": {"children": [{"name": "heartbeat"}]}}},
            {"ok": True, "result": {}},
        ])
        class Stream:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def write(self, raw): writes.append(json.loads(raw))
            def flush(self): pass
            def readline(self, size): return json.dumps(next(replies)).encode()
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def settimeout(self, value): pass
            def makefile(self, mode): return Stream()
        class Stop:
            done = False
            def is_set(self): return self.done
            def wait(self, seconds): self.done = True
        with patch("bridge.socket.create_connection", return_value=Connection()):
            pulse_panels(9877, self.bridge, Stop())
        self.assertTrue(self.bridge.auto_updates)
        self.assertEqual(writes[-1]["params"], {"command": "scriptui.click", "params": {"window": 2, "widget": "heartbeat"}})
        self.assertEqual(len(writes), 3)

    def test_launcher_reuses_an_open_panel_without_starting_another_app(self):
        import launch
        from types import SimpleNamespace
        with patch.object(launch, "ROOT", self.root), \
             patch.object(launch.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
             patch.object(launch.subprocess, "Popen") as spawn, \
             patch.object(launch, "control", return_value=[{"title": "CorridorKey"}]) as control:
            self.assertEqual(launch.main(), 0)
        spawn.assert_not_called()
        self.assertFalse(any(call.args[1].get("command") == "window.scriptPanel" for call in control.call_args_list))


if __name__ == "__main__":
    unittest.main()
