import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from bundles import Bundles, media_paths, contained
from jobs import Jobs
from player import Player
from storage import Storage
from tasks import Tasks
from test_bridge import FakeWorker


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
        self.jobs=Jobs(self.root,self.root/'outputs',worker=FakeWorker())
        self.tasks=Tasks();self.player=Player(self.jobs)
        self.storage=Storage(self.jobs,self.player,self.tasks)
        self.bundles=Bundles(self.jobs,self.tasks)
        self.input=self.root/'clip.mp4';self.input.write_bytes(b'source')
    def tearDown(self):
        self.player.close();self.tasks.close();self.jobs.close();self.tmp.cleanup()
    def done(self,task):
        end=time.monotonic()+3
        while time.monotonic()<end:
            result=self.tasks.status(task['id'])
            if result['state']!='running':return result
            time.sleep(.01)
        self.fail('Background task did not finish')
    def job(self):
        value=self.jobs.submit({'input':str(self.input),'context':{}})
        end=time.monotonic()+3
        while self.jobs.status(value['id'])['state'] not in ('completed','failed') and time.monotonic()<end:time.sleep(.01)
        return self.jobs.jobs[value['id']]
    def test_cleanup_only_disposable_data_and_skips_live_player_and_queued_refinement(self):
        job=self.job();folder=Path(job['folder']);proxy=folder/'playback';proxy.mkdir();(proxy/'frame.jpg').write_bytes(b'proxy')
        cache=folder/'cache';cache.mkdir();(cache/'raw_000000.exr').write_bytes(b'raw')
        job.update(cache_dir=str(cache),frame_count=1,native_fps=24,first_frame=0,end_frame=1,cropped=False,preview=False)
        view=self.player.open(job['id'])
        plan=self.storage.plan([job['id']],False,[]);self.assertEqual(plan['folders'],0)
        self.player.close_view(view['id'])
        plan=self.storage.plan([job['id']],False,[])
        result=self.done(self.storage.clean(plan['id']));self.assertEqual(result['state'],'completed')
        self.assertFalse(proxy.exists());self.assertTrue(Path(job['output']).is_file());self.assertTrue(cache.exists())
        # An actual project reference protects even optional correction-cache deletion.
        plan=self.storage.plan([job['id']],True,[str(cache/'raw_000000.exr')]);self.assertEqual(plan['folders'],0)
        with self.jobs.condition:
            refined=self.jobs.refine(job['id'],{'matte_expand':1})
            plan=self.storage.plan([job['id']],True,[]);self.assertEqual(plan['folders'],0)
            self.jobs.cancel(refined['id'])
        plan=self.storage.plan([job['id']],True,[])
        self.assertGreater(plan['bytes'],0)
        self.assertEqual(self.done(self.storage.clean(plan['id']))['state'],'completed')
        self.assertFalse(cache.exists());self.assertTrue(Path(job['output']).is_file())
    def test_package_is_portable_and_restorable_after_move_with_shared_cache(self):
        job=self.job();folder=Path(job['folder']);cache=folder/'cache';cache.mkdir();(cache/'raw_000000.exr').write_bytes(b'raw cache')
        project=self.root/'Example.ecproj';project.write_text('{}', encoding='utf-8')
        job['options']['context']=dict(project=str(project),comp=1,layer=2,path=str(self.input),name='Layer')
        job['context']=job['options']['context'];job.update(cache_dir=str(cache),frame_count=1,native_fps=24,first_frame=0,end_frame=1,cropped=False,preview=False)
        prepared=self.bundles.prepare()
        snapshot=dict(schema=2,items={'1':dict(kind=dict(type='Footage',path=str(self.input))),
                                      '2':dict(kind=dict(type='Footage',path=job['output']))})
        Path(prepared['path']).write_text(json.dumps(snapshot), encoding='utf-8')
        task=self.bundles.start(prepared['id'],str(self.root),str(project),[job['id']],True,'{"Hair":{"black":"2"}}')
        result=self.done(task);self.assertEqual(result['state'],'completed',result)
        bundle=Path(result['result']['path']);moved=self.root/'Moved';bundle.rename(moved)
        packaged=moved/'Example.ecproj';data=json.loads(packaged.read_text(encoding='utf-8'))
        self.assertTrue(all(p.is_file() for p in media_paths(data,moved)))
        self.assertTrue(all(not Path(v['kind']['path']).is_absolute() for v in data['items'].values()))
        restored=self.bundles.restore(str(packaged));self.assertEqual(restored['imported'],1)
        imported=[j for j in self.jobs.jobs.values() if j.get('package')==str(packaged)][0]
        self.assertTrue(Path(imported['cache_dir'],'raw_000000.exr').is_file())
        self.assertEqual(imported['context']['project'],str(packaged))
        self.assertEqual(self.bundles.restore(str(packaged))['imported'],0)
        self.assertTrue(Path(job['output']).is_file())
    def test_missing_media_leaves_no_partial_bundle_and_original_is_untouched(self):
        prepared=self.bundles.prepare();Path(prepared['path']).write_text(json.dumps(dict(schema=2,path=str(self.root/'missing.mov'))), encoding='utf-8')
        result=self.done(self.bundles.start(prepared['id'],str(self.root),str(self.root/'p.ecproj')))
        self.assertEqual(result['state'],'failed');self.assertIn('fehlt',result['error'])
        self.assertFalse(list(self.root.glob('*.partial')))
        self.assertTrue(self.input.is_file())
    def test_package_path_traversal_is_rejected(self):
        for value in ('../escape','/etc/passwd'):
            with self.assertRaises(ValueError):contained(self.root,value)
    def test_retry_of_cached_correction_retains_the_cache_processing_path(self):
        job=self.job();cache=Path(job['folder'])/'cache';cache.mkdir();(cache/'raw_000000.exr').write_bytes(b'raw')
        job.update(cache_dir=str(cache),frame_count=1,native_fps=24,first_frame=0,end_frame=1,cropped=False,preview=False)
        with self.jobs.condition:
            first=self.jobs.refine(job['id'],{'matte_expand':1})
            self.jobs.cancel(first['id'])
            retried=self.jobs.retry(first['id'])
            self.assertEqual(self.jobs.jobs[retried['id']]['kind'],'refine')
            self.assertEqual(self.jobs.jobs[retried['id']]['parent']['cache_dir'],str(cache))
            self.jobs.cancel(retried['id'])

    def test_package_cannot_be_created_inside_disposable_job_data(self):
        job=self.job();destination=Path(job['folder'])/'cache';destination.mkdir()
        prepared=self.bundles.prepare();Path(prepared['path']).write_text('{"schema":2,"items":{}}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Zielordner außerhalb'):
            self.bundles.start(prepared['id'],str(destination),str(self.root/'project.ecproj'))
        self.assertTrue(destination.is_dir())

    def test_background_error_is_pollable(self):
        def failure(progress):raise OSError('No space left')
        result=self.done(self.tasks.start(failure));self.assertEqual(result['state'],'failed');self.assertIn('No space',result['error'])

if __name__=='__main__':unittest.main()
