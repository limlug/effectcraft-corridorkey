"""Own image finishing for linear BGRA images exported by an external program.

No CorridorKey implementation, private API or model code is used here.
"""
import math
import os
from pathlib import Path
import subprocess
import tempfile
from processes import check_cancel

os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
FINISHING={'despill','matte_black','matte_white','matte_expand','matte_feather','output_format','exr_dtype','keep_warm'}


def refine_alpha(alpha,black=0.,white=1.,expand=0,feather=0.):
    import cv2
    import numpy as np
    if not 0<=black<white<=1 or not -32<=expand<=32 or not 0<=feather<=16:raise ValueError('Invalid matte settings')
    result=np.clip((alpha-black)/(white-black),0,1).astype(np.float32)
    radius=abs(int(expand))
    if radius:
        kernel=np.ones((radius*2+1,radius*2+1),np.uint8)
        result=(cv2.dilate if expand>0 else cv2.erode)(result,kernel)
    if feather:
        radius=math.ceil(3*feather)
        weights=np.exp(-np.arange(-radius,radius+1,dtype=np.float64)**2/(2*feather**2))
        weights=(weights/weights.sum()).astype(np.float32)
        result=cv2.sepFilter2D(result,-1,weights,weights,borderType=cv2.BORDER_REPLICATE)
    return np.clip(result,0,1)


def finish_pixels(raw,options,video):
    import numpy as np
    pixels=raw.astype(np.float32,copy=True)
    pixels[:,:,3]=refine_alpha(pixels[:,:,3],options['matte_black'],options['matte_white'],options['matte_expand'],options['matte_feather'])
    rgb=pixels[:,:,:3]
    if video:
        positive=np.maximum(rgb,0)
        rgb[:]=np.clip(np.where(positive<=.0031308,positive*12.92,1.055*positive**(1/2.4)-.055),0,1)
    # Green-spill reduction is our independent channel operation.
    excess=np.maximum(rgb[:,:,1]-(rgb[:,:,0]+rgb[:,:,2])*.5,0)
    rgb[:,:,1]-=float(options['despill'])*excess
    return pixels


class VideoWriter:
    def __init__(self,path,fps,width,height):
        self.error=tempfile.TemporaryFile()
        args=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgra64le','-s',f'{width}x{height}',
              '-r',str(fps),'-i','pipe:0','-an','-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le',
              '-alpha_bits','16','-color_trc','iec61966-2-1','-threads','2',str(path)]
        try:self.process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=self.error)
        except BaseException:self.error.close();raise

    def write(self,pixels):
        import numpy as np
        if self.process.poll() is not None:raise OSError('Video encoder stopped')
        data=(np.clip(pixels,0,1)*65535).round().astype('<u2')
        self.process.stdin.write(data.tobytes())

    def close(self):
        failure=None
        try:self.process.stdin.close()
        except OSError as error:failure=error
        try:code=self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill();self.process.wait();code=-1
        self.error.seek(0);detail=self.error.read().decode('utf-8','replace');self.error.close()
        if code or failure:raise OSError(detail or str(failure or 'Video encoder did not finish'))


def render(cache_dir,frame_count,fps,options,folder,cancel):
    import cv2
    import numpy as np
    paths=sorted(Path(cache_dir).glob('raw_*.exr'))
    if len(paths)!=frame_count or not paths:raise ValueError('Correction data unavailable; run the AI again')
    first=cv2.imread(str(paths[0]),cv2.IMREAD_UNCHANGED)
    if first is None or first.ndim!=3 or first.shape[2]!=4:raise ValueError('Invalid correction data')
    height,width=first.shape[:2]
    sequence=options['output_format']=='exr' and not options['preview']
    output=Path(folder)/('corrected_cutout_exr' if sequence else 'corrected_cutout.mov')
    writer=None
    if sequence:output.mkdir()
    else:writer=VideoWriter(output,fps,width,height)
    try:
        for index,path in enumerate(paths):
            check_cancel(cancel)
            raw=cv2.imread(str(path),cv2.IMREAD_UNCHANGED)
            if raw is None or raw.shape!=first.shape or not np.isfinite(raw).all():raise ValueError('Invalid correction frame')
            pixels=finish_pixels(raw,options,not sequence)
            if sequence:
                dtype=cv2.IMWRITE_EXR_TYPE_FLOAT if options['exr_dtype']=='float' else cv2.IMWRITE_EXR_TYPE_HALF
                if not cv2.imwrite(str(output/f'cutout_{index:06d}.exr'),pixels,[cv2.IMWRITE_EXR_TYPE,dtype]):raise OSError('EXR write failed')
            else:writer.write(pixels)
            print(f'Finishing frame {index+1}/{len(paths)}',flush=True)
    finally:
        if writer:writer.close()
    check_cancel(cancel)
    return str(sorted(output.glob('*.exr'))[0] if sequence else output),sequence
