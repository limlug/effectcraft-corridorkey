"""Portable EffectCraft snapshots: verified media copies and relative paths."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import time
import uuid

MANIFEST='corridorkey-package.json'


def media_paths(data, base):
    """EffectCraft schema 2: footage/proxy `path` and `sequence` paths."""
    result=set()
    def walk(node):
        if isinstance(node,dict):
            for key,value in node.items():
                if key=='path' and isinstance(value,str) and value:
                    result.add((base/value).resolve() if not Path(value).is_absolute() else Path(value).resolve())
                elif key=='sequence' and isinstance(value,list):
                    for entry in value:
                        if isinstance(entry,str) and entry:result.add((base/entry).resolve() if not Path(entry).is_absolute() else Path(entry).resolve())
                        else:walk(entry)
                else:walk(value)
        elif isinstance(node,list):
            for child in node:walk(child)
    walk(data)
    return result


def rewrite_media(data,base,mapping):
    def mapped(value):
        path=(base/value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
        return mapping.get(path,value)
    def walk(node):
        if isinstance(node,dict):
            return {k:(mapped(v) if k=='path' and isinstance(v,str) and v else
                      [mapped(x) if isinstance(x,str) and x else walk(x) for x in v] if k=='sequence' and isinstance(v,list) else walk(v)) for k,v in node.items()}
        if isinstance(node,list):return [walk(x) for x in node]
        return node
    return walk(data)


def contained(base,relative):
    if not isinstance(relative,str) or Path(relative).is_absolute():raise ValueError('Paketpfad muss relativ sein')
    path=(base/relative).resolve()
    if not path.is_relative_to(base.resolve()):raise ValueError('Paketpfad liegt außerhalb des Pakets')
    return path


class Bundles:
    def __init__(self,jobs,tasks):
        self.jobs,self.tasks=jobs,tasks
        self.prepared={}

    def prepare(self):
        identity=uuid.uuid4().hex
        folder=self.jobs.output_root/'_snapshots'/identity
        folder.mkdir(parents=True)
        self.prepared[identity]=folder/'snapshot.ecproj'
        return dict(id=identity,path=str(self.prepared[identity]))

    def start(self,identity,destination,project,jobs=None,include_cache=True,presets='{}'):
        if identity not in self.prepared:raise ValueError('Projektschnappschuss fehlt')
        snapshot=self.prepared[identity]
        if not snapshot.is_file():raise ValueError('Projektschnappschuss zuerst erstellen')
        if not isinstance(destination,str) or not Path(destination).is_absolute() or not Path(destination).is_dir():raise ValueError('Einen vorhandenen Zielordner wählen')
        if not isinstance(project,str) or not Path(project).is_absolute() or Path(project).suffix.lower()!='.ecproj':raise ValueError('Projekt zuerst speichern')
        if not isinstance(include_cache,bool):raise ValueError('Ungültige Cache-Auswahl')
        if jobs is not None and (not isinstance(jobs,list) or len(jobs)>100 or not all(isinstance(x,str) for x in jobs)):raise ValueError('Ungültige Auftragsliste')
        dest=Path(destination).resolve()
        if dest.is_relative_to(self.jobs.output_root):
            parts=dest.relative_to(self.jobs.output_root).parts
            if parts and (re.fullmatch('[0-9a-f]{32}',parts[0]) or parts[0]=='_snapshots'):
                raise ValueError('Zielordner außerhalb von Auftrags- und Zwischendaten wählen')
        if not isinstance(presets,str):raise ValueError('Ungültige Vorlagen')
        preset_data=json.loads(presets)
        if not isinstance(preset_data,dict) or len(presets)>65536:raise ValueError('Ungültige Vorlagen')
        with self.jobs.lock:
            selected=[]
            for job in self.jobs.jobs.values():
                if job['state']=='completed' and (job['id'] in jobs if jobs is not None else job.get('context',{}).get('project')==project):
                    selected.append(json.loads(json.dumps({k:v for k,v in job.items() if k not in ('cancel','parent')})))
        def action(progress):
            try:return self._copy(snapshot,Path(destination).resolve(),project,selected,include_cache,preset_data,progress)
            finally:
                snapshot.unlink(missing_ok=True)
                self.prepared.pop(identity,None)
        return self.tasks.start(action)

    def _copy(self,snapshot,destination,project,jobs,include_cache,presets,progress):
        data=json.loads(snapshot.read_text(encoding='utf-8'))
        if data.get('schema')!=2:raise ValueError('Dieses EffectCraft-Projektformat wird noch nicht unterstützt')
        assets=media_paths(data,snapshot.parent)
        jobs=[job for job in jobs if Path(job["output"]).resolve() in assets]
        mapping={}
        copies={}
        def add(path,relative=None):
            path=Path(path).resolve()
            if path in mapping:return mapping[path]
            if not path.is_file():raise FileNotFoundError('Benötigte Mediendatei fehlt: '+str(path))
            relative=relative or ('Media/'+hashlib.sha256(str(path.parent).encode()).hexdigest()[:12]+'/'+path.name)
            mapping[path]=relative;copies[path]=relative
            return relative
        for path in assets:add(path)
        for job in jobs:
            if job.get('sequence'):
                for path in sorted(Path(job['output']).parent.glob('*.exr')):add(path)
            else:add(job['output'])
            for thumb in job.get('thumbnails',{}).values():
                if Path(thumb).is_file():add(thumb)
            for key in ('input','hint','hint_video'):
                if job['options'].get(key):add(job['options'][key])
            if include_cache and job.get('cache_dir') and Path(job['cache_dir']).is_dir():
                cache=Path(job['cache_dir']).resolve()
                prefix='CorridorKey/Corrections/'+hashlib.sha256(str(cache).encode()).hexdigest()[:12]
                for path in sorted(cache.glob('raw_*.exr')):add(path,prefix+'/'+path.name)
                mapping[cache]=prefix
        total=sum(p.stat().st_size for p in copies)
        if shutil.disk_usage(destination).free < total+64*1024*1024:raise OSError('Nicht genügend freier Speicher für das Projektpaket')
        name=Path(project).stem[:100]+' – CorridorKey '+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
        target=destination/name
        temporary=destination/('.'+name+'.partial')
        temporary.mkdir()
        done=0;checksums=[]
        try:
            for source,relative in copies.items():
                progress(done,total,'Kopiere '+source.name)
                out=contained(temporary,relative);out.parent.mkdir(parents=True,exist_ok=True)
                initial=source.stat();digest=hashlib.sha256()
                with source.open('rb') as src,out.open('xb') as dst:
                    while True:
                        chunk=src.read(1024*1024)
                        if not chunk:break
                        dst.write(chunk);digest.update(chunk);done+=len(chunk)
                        progress(done,total,'Kopiere '+source.name)
                final=source.stat()
                if (initial.st_size,initial.st_mtime_ns)!=(final.st_size,final.st_mtime_ns):raise OSError('Quelldatei wurde beim Kopieren geändert: '+source.name)
                verify=hashlib.sha256()
                with out.open('rb') as copied:
                    while True:
                        chunk=copied.read(1024*1024)
                        if not chunk:break
                        verify.update(chunk);progress(done,total,'Prüfe '+source.name)
                if verify.digest()!=digest.digest():raise OSError('Kopie konnte nicht verifiziert werden: '+source.name)
                checksums.append(dict(path=relative,bytes=initial.st_size,sha256=digest.hexdigest()))
            project_name=Path(project).name
            portable=rewrite_media(data,snapshot.parent,mapping)
            (temporary/project_name).write_text(json.dumps(portable,ensure_ascii=False,indent=2), encoding='utf-8')
            def remap(node):
                if isinstance(node,dict):return {k:remap(v) for k,v in node.items()}
                if isinstance(node,list):return [remap(v) for v in node]
                if isinstance(node,str):
                    if node==project:return project_name
                    if Path(node).is_absolute():return mapping.get(Path(node).resolve(),node)
                return node
            portable_jobs=[]
            for job in jobs:
                relative_cache=mapping.get(Path(job['cache_dir']).resolve()) if job.get('cache_dir') else None
                entry=remap(job)
                entry.update(folder='CorridorKey/Jobs/'+job['id'],log='CorridorKey/Jobs/'+job['id']+'/inference.log',cache_dir=relative_cache)
                # No local machine paths or obsolete parent-job payload in the package.
                entry['options']['context']['project']=project_name
                entry['context']['project']=project_name
                (temporary/entry['folder']).mkdir(parents=True,exist_ok=True)
                (temporary/entry['log']).write_text('Aus verifiziertem CorridorKey-Projektpaket übernommen.\n', encoding='utf-8')
                portable_jobs.append(entry)
            manifest=dict(api=1,project=project_name,jobs=portable_jobs,presets=presets,assets=checksums)
            (temporary/MANIFEST).write_text(json.dumps(manifest,ensure_ascii=False,indent=2), encoding='utf-8')
            progress(total,total,'Projektpaket fertig')
            temporary.rename(target)
            return dict(path=str(target),project=str(target/project_name),bytes=total,files=len(copies))
        except Exception:
            shutil.rmtree(temporary,ignore_errors=True)
            raise

    def restore(self,project):
        if not isinstance(project,str) or not Path(project).is_absolute():raise ValueError('Ungültiger Projektpfad')
        path=Path(project).resolve();base=path.parent
        manifest=base/MANIFEST
        if not manifest.is_file():return dict(imported=0,presets={})
        if manifest.stat().st_size>8*1024*1024:raise ValueError('Paketbeschreibung zu groß')
        data=json.loads(manifest.read_text(encoding='utf-8'))
        if data.get('api')!=1 or contained(base,data.get('project',''))!=path:raise ValueError('Paket gehört zu einem anderen Projekt')
        entries=data.get('jobs',[])
        if not isinstance(entries,list) or len(entries)>100:raise ValueError('Ungültige Paketaufträge')
        prepared=[]
        from options import validate
        for entry in entries:
            if not isinstance(entry,dict):raise ValueError('Ungültiger Paketauftrag')
            old=entry.get('id')
            if not isinstance(old,str) or not re.fullmatch('[0-9a-f]{32}',old):raise ValueError('Ungültige Paketkennung')
            identity=uuid.uuid5(uuid.NAMESPACE_URL,str(path)+'#'+old).hex
            def absolute(node,key=''):
                if isinstance(node,dict):return {k:absolute(v,k) for k,v in node.items()}
                if isinstance(node,list):return [absolute(v,key) for v in node]
                if isinstance(node,str) and node and key in ('input','hint','hint_video','path','project','output','cache_dir','log','folder','checker','matte','comparison','original'):
                    return str(contained(base,node))
                return node
            job=absolute(entry)
            job['options']=validate(job['options'])
            if job['options']['context'].get('project')!=str(path):raise ValueError('Ungültiger Projektebenenbezug')
            if not Path(job['output']).is_file():raise ValueError('Paket-Ausgabedatei fehlt')
            if job.get('sequence') and len(list(Path(job['output']).parent.glob('*.exr')))!=job['frame_count']:raise ValueError('EXR-Paketsequenz ist unvollständig')
            job.update(id=identity,state='completed',package=str(path),cache_owner=identity,
                       folder=str(self.jobs.output_root/identity),log=str(self.jobs.output_root/identity/'inference.log'))
            prepared.append(job)
        imported=0
        with self.jobs.condition:
            for job in prepared:
                if job['id'] in self.jobs.jobs:continue
                folder=Path(job['folder']);folder.mkdir(exist_ok=True)
                (folder/'inference.log').write_text('Korrekturdaten und Ausgabe liegen im geöffneten Projektpaket.\n', encoding='utf-8')
                import threading
                job['cancel']=threading.Event()
                self.jobs.jobs[job['id']]=job;self.jobs._persist(job);imported+=1
        return dict(imported=imported,presets=data.get('presets',{}))
