"""Wrapper worker supervising the separate, original CorridorKey CLI. stdout is reserved for JSON replies."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'


def command(args, cancel):
    from processes import run
    run(args,cancel,log=sys.stdout)


def probe(path):
    data = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=avg_frame_rate,nb_frames,duration,width,height:format=duration', '-of', 'json', str(path)]))
    stream = data['streams'][0]
    a, b = map(float, stream['avg_frame_rate'].split('/'))
    fps = a / b
    total = stream.get('nb_frames', 'N/A')
    if total == 'N/A':
        counted = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'json', str(path)]))
        total = counted['streams'][0]['nb_read_frames']
    return fps, int(total), int(stream['width']), int(stream['height'])


def crop(source, target, first, last, cancel, reverse=False):
    if reverse:
        # Disk-backed reversal avoids FFmpeg's whole-clip reverse RAM buffer.
        import shutil
        import tempfile
        fps,total,width,height=probe(source)
        if shutil.disk_usage(Path(target).parent).free < width*height*4*(last-first)+64*1024*1024:
            raise OSError('Not enough disk space for reference reversal')
        with tempfile.TemporaryDirectory(prefix='reverse-',dir=Path(target).parent) as folder:
            folder=Path(folder)
            command(['ffmpeg','-v','error','-y','-i',str(source),'-an','-vf',
                f'trim=start_frame={first}:end_frame={last},setpts=PTS-STARTPTS',
                '-vsync','0','-threads','2',str(folder/'frame_%09d.png')],cancel)
            frames=sorted(folder.glob('frame_*.png'))
            if len(frames)!=last-first:raise ValueError('Reference reversal frame count mismatch')
            for index,path in enumerate(reversed(frames)):path.rename(folder/f'reverse_{index:09d}.png')
            command(['ffmpeg','-v','error','-y','-framerate',str(fps),'-i',str(folder/'reverse_%09d.png'),
                '-an','-c:v','ffv1','-pix_fmt','bgr0','-threads','2',str(target)],cancel)
    else:
        command(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-an', '-vf',
            f'trim=start_frame={first}:end_frame={last},setpts=PTS-STARTPTS',
            '-c:v', 'ffv1', '-pix_fmt', 'bgr0', '-threads', '2', str(target)], cancel)
    return str(target)


def thumbnails(output, sequence, folder, source, first, cancel):
    import cv2
    import numpy as np
    raw = folder / 'preview-rgba.png'
    if sequence:
        rgba = cv2.imread(str(output), cv2.IMREAD_UNCHANGED)
        rgb = rgba[..., :3]
        rgba[..., :3] = np.where(rgb <= .0031308, rgb * 12.92, 1.055 * np.maximum(rgb, 0) ** (1 / 2.4) - .055)
        rgba = np.clip(rgba * 255, 0, 255).astype('uint8')
    else:
        command(['ffmpeg', '-v', 'error', '-y', '-i', str(output), '-frames:v', '1', '-vf', 'scale=384:-1', '-pix_fmt', 'rgba', str(raw)], cancel)
        rgba = cv2.imread(str(raw), cv2.IMREAD_UNCHANGED)
    if rgba is not None and rgba.dtype == np.uint16: rgba=(rgba / 257).round().astype('uint8')
    if rgba is None or rgba.ndim != 3 or rgba.shape[2] != 4: raise RuntimeError('Vorschaubild enthält keinen Alphakanal')
    height, width = rgba.shape[:2]
    size = (min(384, width), max(1, round(height * min(384, width) / width)))
    rgba = cv2.resize(rgba, size)
    h, w = rgba.shape[:2]
    alpha = rgba[..., 3:4].astype('float32') / 255
    y, x = np.indices((h, w))
    checker = np.where(((x // 16 + y // 16) % 2)[..., None], 160, 100)
    comp = (rgba[..., :3] * alpha + checker * (1 - alpha)).astype('uint8')
    matte = np.repeat(rgba[..., 3:4], 3, axis=2)
    original = folder / 'preview-original.png'
    command(['ffmpeg', '-v', 'error', '-y', '-i', source, '-vf', f'select=eq(n\\,{first}),scale={w}:{h}', '-frames:v', '1', str(original)], cancel)
    before = cv2.imread(str(original))
    comparison = comp.copy()
    if before is not None: comparison[:, :w // 2] = before[:, :w // 2]
    result = {}
    for name, pixels in [('checker', comp), ('matte', matte), ('comparison', comparison)]:
        path = folder / ('preview-' + name + '.png')
        if not cv2.imwrite(str(path), pixels): raise RuntimeError('Vorschaubild konnte nicht geschrieben werden')
        result[name] = str(path)
    result["original"]=str(original)
    return result


def main():
    import shutil
    import signal
    from processes import check_cancel,stop_all
    from runtime_cli import arguments
    from options import frame_range
    from postprocess import render
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True)
    root=Path(parser.parse_args().root).resolve()
    def terminate(signum,frame):
        stop_all();raise SystemExit(128+signum)
    signal.signal(signal.SIGTERM,terminate)
    loads=0
    for line in sys.stdin:
        spec=json.loads(line)['spec'];folder=Path(spec['folder']);options=spec['options']
        options.setdefault('keep_cache',True)
        options.setdefault('mask_stack',None)
        options.setdefault('reference_frame',None)
        cancel=folder/'cancel';reply={}
        with open(folder/'inference.log','a',buffering=1,encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            try:
                check_cancel(cancel)
                if spec.get('kind')=='refine':
                    parent=spec['parent']
                    output,sequence=render(parent['cache_dir'],parent['frame_count'],parent['native_fps'],options,folder,cancel)
                    thumbs=thumbnails(output,sequence,folder,options['input'],parent['first_frame'],cancel)
                    reply=dict(ok=True,output=output,sequence=sequence,thumbnails=thumbs,cache_dir=parent['cache_dir'],
                        cache_owner=parent.get('cache_owner') or parent['id'],
                        **{k:parent[k] for k in ('first_frame','end_frame','native_fps','frame_count','cropped','preview')})
                else:
                    fps,total,_,_=probe(options['input'])
                    first,last=frame_range(fps,total,options['range_start'],options['range_end'],options['preview'],options['preview_seconds'])
                    source=options['input']
                    if first or last!=total:source=crop(source,folder/'range.mkv',first,last,cancel)
                    hint=options['hint_video'] or None
                    if hint:
                        hf,hn,_,_=probe(hint)
                        if abs(hf-fps)>.001 or hn!=total:raise ValueError('Mask video must match source frame rate and count')
                        if first or last!=total:hint=crop(hint,folder/'hint-range.mkv',first,last,cancel)
                    initial=options['hint'] or None
                    if options['mask_stack'] is not None:
                        from mask_hint import rasterize_stack
                        initial=rasterize_stack(options['mask_stack'],folder/'layer-mask.png')
                    if options['layer_mask'] is not None:
                        from mask_hint import rasterize
                        initial=rasterize(options['layer_mask'],folder/'layer-mask.png')
                    reference=first if options['reference_frame'] is None else options['reference_frame']
                    if not first<=reference<last:raise ValueError('Reference frame outside processed range')
                    if hint and reference!=first:raise ValueError('Mask video uses the original frame alignment; leave reference automatic')
                    if reference!=first and not initial:raise ValueError('Select a starting mask for the chosen reference frame')
                    if reference==first:
                        command(arguments(root,source,folder,options,initial,hint),cancel);loads+=1
                        raw=sorted((folder/'prediction').glob('*_cutout_exr/*.exr'))
                    else:
                        # Run the original CLI from the reference in both directions.
                        # Reverse decoded images only; timeline/output order remains original.
                        forward=folder/'forward';backward=folder/'backward';forward.mkdir();backward.mkdir()
                        fs=crop(options['input'],folder/'forward.mkv',reference,last,cancel)
                        bs=crop(options['input'],folder/'backward.mkv',first,reference+1,cancel,reverse=True)
                        command(arguments(root,fs,forward,options,initial,None),cancel);loads+=1
                        command(arguments(root,bs,backward,options,initial,None),cancel);loads+=1
                        front=sorted((forward/'prediction').glob('*_cutout_exr/*.exr'))
                        back=sorted((backward/'prediction').glob('*_cutout_exr/*.exr'))
                        if len(front)!=last-reference or len(back)!=reference-first+1:raise RuntimeError('Reference passes returned wrong frame count')
                        raw=list(reversed(back))[:-1]+front
                    if len(raw)!=last-first:raise RuntimeError('Original CLI did not produce the expected frame count')
                    cache=folder/'cache';cache.mkdir(exist_ok=True)
                    for index,path in enumerate(raw):path.rename(cache/f'raw_{index:06d}.exr')
                    output,sequence=render(cache,last-first,fps,options,folder,cancel)
                    thumbs=thumbnails(output,sequence,folder,options['input'],first,cancel)
                    reply=dict(ok=True,output=output,sequence=sequence,first_frame=first,end_frame=last,native_fps=fps,
                        frame_count=last-first,cropped=first!=0 or last!=total,preview=options['preview'],thumbnails=thumbs,
                        cache_dir=str(cache) if options['keep_cache'] else None,cache_owner=spec.get('id') or folder.name)
                    if not options['keep_cache']:shutil.rmtree(cache)
                check_cancel(cancel)
            except Exception as error:
                traceback.print_exc();reply=dict(ok=False,error=str(error))
            finally:
                for name in ('range.mkv','hint-range.mkv','forward.mkv','backward.mkv'):(folder/name).unlink(missing_ok=True)
                for name in ('temp','prediction','forward','backward'):shutil.rmtree(folder/name,ignore_errors=True)
                if not reply.get('ok'):shutil.rmtree(folder/'cache',ignore_errors=True)
        reply.update(resident=False,model_loads=loads,worker_pid=os.getpid())
        print(json.dumps(reply),flush=True)


if __name__=='__main__':main()
