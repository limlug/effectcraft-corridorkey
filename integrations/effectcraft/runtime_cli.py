"""Only the upstream CLI is invoked; no CorridorKey Python modules are imported."""
from pathlib import Path
import sys


def arguments(root,source,folder,options,initial_hint=None,hint_video=None):
    args=[sys.executable,str(Path(root)/'infer.py'),'--input',str(source),
        '--output_dir',str(Path(folder)/'prediction'),'--outputs','cutout',
        '--output_format','exr','--exr_dtype','float','--despill_strength','0',
        '--temp_dir',str(Path(folder)/'temp'),
        '--hint_quality',str(options['hint_quality']),
        '--model_scale',str(options['preview_scale'] if options['preview'] else 1)]
    if options['low_vram']:args.append('--low_vram')
    if initial_hint:args += ['--hint_first_frame',str(initial_hint)]
    if hint_video:args += ['--hint_video',str(hint_video)]
    return args
