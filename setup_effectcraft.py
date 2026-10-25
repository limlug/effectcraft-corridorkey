#!/usr/bin/env python3
"""Install the add-on plus a pinned, separately fetched CorridorKey runtime."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

UPSTREAM='https://github.com/nikopueringer/CorridorKey2.0.git'
REVISION='485f5e9ab759ead6138cc990776184b59d6ea971'
ROOT=Path(__file__).resolve().parent


def commands(root, python, effectcraft, skip_weights=False, settings_dir=None):
    root=Path(root);runtime=root/'runtime/CorridorKey2.0'
    venv_python=root/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    plan=[]
    if not (runtime/'.git').exists():
        plan += [([shutil.which('git') or 'git','clone','--no-checkout',UPSTREAM,str(runtime)],root)]
    plan += [(['git','checkout','--detach',REVISION],runtime)]
    if not venv_python.is_file():plan += [([str(python),'-m','venv',str(root/'venv')],root)]
    plan += [([str(venv_python),'-m','pip','install','torch==2.9.1','torchvision==0.24.1','--index-url','https://download.pytorch.org/whl/cu128'],root),
             ([str(venv_python),'-m','pip','install','-r',str(runtime/'requirements.txt')],root)]
    if not skip_weights:plan += [([str(venv_python),str(runtime/'scripts/download_weights.py'),'--corridorkey_revision',MODEL_REVISION],root)]
    panel=[str(venv_python),str(root/'integrations/effectcraft/install.py'),'--effectcraft',str(effectcraft)]
    if settings_dir:panel += ['--settings-dir',str(settings_dir)]
    plan += [(panel,root),([str(venv_python),str(root/'integrations/effectcraft/bridge.py'),'--check'],root)]
    return plan


# Pinned model revision is recorded separately from the upstream code revision.
MODEL_REVISION='cf44a8db3f024bb49fd59daa408848ccf05f7477'


def execute(plan, runtime):
    fresh_clone=False
    for command,cwd in plan:
        if command[:3]==['git','checkout','--detach'] and (runtime/'.git').is_dir() and not fresh_clone:
            head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=runtime,text=True).strip()
            changed=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=runtime,text=True).strip()
            extra=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','*.py'],cwd=runtime,text=True).strip()
            if head!=REVISION or changed or extra:
                raise RuntimeError('Runtime differs from the original source. Use a fresh runtime folder; existing files were not reset.')
        print('> '+subprocess.list2cmdline(command),flush=True)
        subprocess.run(command,cwd=cwd,check=True,env=dict(os.environ,PYTHONIOENCODING='utf-8'))
        if len(command)>1 and command[1]=='clone':fresh_clone=True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--effectcraft',type=Path,required=True,help='EffectCraft executable or Linux AppImage')
    parser.add_argument('--skip-weights',action='store_true',help='Use models already downloaded; the final check still verifies them')
    parser.add_argument('--settings-dir',type=Path,help='Override EffectCraft settings folder')
    parser.add_argument('--dry-run',action='store_true',help='Print actions without changing or downloading anything')
    parser.add_argument('--launch',action='store_true',help='Open EffectCraft and the panel after successful setup')
    args=parser.parse_args()
    if sys.version_info[:2] not in ((3,11),(3,12)):parser.error('Use Python 3.11 or 3.12 (tested: 3.12).')
    if sys.platform=='darwin':parser.error('The current runtime requires NVIDIA CUDA. macOS is not supported.')
    if args.settings_dir and args.launch:parser.error('--launch uses the standard settings folder; omit it for a custom --settings-dir.')
    app=args.effectcraft.expanduser().resolve()
    if not args.dry_run:
        if not app.is_file():parser.error('EffectCraft executable does not exist.')
        missing=[name for name in ('git','ffmpeg','ffprobe') if not shutil.which(name)]
        if missing:parser.error('Install these prerequisites first: '+', '.join(missing))
    plan=commands(ROOT,sys.executable,app,args.skip_weights,args.settings_dir)
    if args.dry_run:
        for command,cwd in plan:print(f'[{cwd}] '+subprocess.list2cmdline(command))
        return 0
    print('CorridorKey is downloaded separately, without patches. Its license and model licenses still apply; see docs/LICENSING.md.')
    execute(plan,ROOT/'runtime/CorridorKey2.0')
    if args.launch:
        subprocess.run([str(ROOT/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')),str(ROOT/'integrations/effectcraft/launch.py')],check=True)
    print('Setup complete. Open the panel with the start command in README.md.')
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (RuntimeError,subprocess.CalledProcessError) as error:
        print(f'Setup stopped: {error}\nFix the reported issue, then run setup again. Existing files are preserved.',file=sys.stderr)
        raise SystemExit(1)
