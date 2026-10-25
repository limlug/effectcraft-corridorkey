"""Own frame inspection and colour-seeded mask assistant; no runtime imports."""
from pathlib import Path
import json
import subprocess
import threading
import uuid
from options import file_path,number,MOVIES,IMAGES


def decode_frame(source,index):
    import cv2
    import numpy as np
    data=subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-vf',f'select=eq(n\\,{index})',
        '-frames:v','1','-f','image2pipe','-c:v','png','-threads','2','pipe:1'],timeout=60)
    result=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_UNCHANGED)
    if result is None:raise ValueError('Frame unavailable')
    if result.dtype==np.uint16:result=(result/257).round().astype(np.uint8)
    return result


def composite(original,rgba,background='checker',split=.5,view='comparison',backdrop=None):
    import numpy as np
    h,w=rgba.shape[:2]
    if backdrop is not None:bg=backdrop[:,:,:3]
    elif background=='checker':
        y,x=np.indices((h,w));bg=np.repeat(np.where(((x//16+y//16)%2)[...,None],160,100),3,axis=2)
    else:bg=np.full((h,w,3),{'white':255,'black':0,'grey':128}[background],np.uint8)
    alpha=rgba[:,:,3:4].astype(np.float32)/255
    result=np.clip(rgba[:,:,:3]*alpha+bg*(1-alpha),0,255).astype(np.uint8)
    if view=='original':return original.copy()
    if view=='matte':return np.repeat(rgba[:,:,3:4],3,axis=2)
    if view=='comparison':result[:,:int(w*split)]=original[:,:int(w*split)]
    return result


def seeded_mask(image,points):
    """GrabCut on at most 1280px; explicit positive/negative colour seeds."""
    import cv2
    import numpy as np
    if not isinstance(points,list) or not 1<=len(points)<=128:raise ValueError('Use 1 to 128 selection points')
    h,w=image.shape[:2];scale=min(1,1280/max(w,h));size=(max(2,round(w*scale)),max(2,round(h*scale)))
    small=cv2.resize(image[:,:,:3],size);labels=np.full(small.shape[:2],cv2.GC_PR_BGD,np.uint8)
    # Unmarked pixels start as probable background; positive seeds establish
    # foreground colours. Never assume the entire interior is foreground.
    positive=False
    for point in points:
        if not isinstance(point,dict) or set(point)!={'x','y','keep'} or not isinstance(point['keep'],bool):raise ValueError('Invalid selection point')
        x=number(point['x'],'x',0,1);y=number(point['y'],'y',0,1);positive|=point['keep']
        cv2.circle(labels,(min(size[0]-1,round(x*(size[0]-1))),min(size[1]-1,round(y*(size[1]-1)))),max(2,round(min(size)*.015)),cv2.GC_FGD if point['keep'] else cv2.GC_BGD,-1)
    if not positive:raise ValueError('Mark at least one foreground point')
    cv2.setRNGSeed(0)
    cv2.grabCut(small,labels,None,np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),5,cv2.GC_INIT_WITH_MASK)
    mask=np.where((labels==cv2.GC_FGD)|(labels==cv2.GC_PR_FGD),255,0).astype(np.uint8)
    # Fill only small enclosed holes (eyes or dark buttons); larger gaps stay open.
    count,components,stats,_=cv2.connectedComponentsWithStats(255-mask)
    for i in range(1,count):
        left,top,width,height,area=stats[i]
        if left>0 and top>0 and left+width<mask.shape[1] and top+height<mask.shape[0] and area<=max(16,mask.size*.001):mask[components==i]=255
    return cv2.resize(mask,(w,h),interpolation=cv2.INTER_NEAREST)


class Review:
    def __init__(self,jobs,tasks):
        self.jobs,self.tasks=jobs,tasks
        self.root=jobs.output_root/'_review'
        self.references={};self.lock=threading.RLock()

    def reference(self,params):
        source=file_path(params.get('input'),'Video',MOVIES)
        frame=number(params.get('frame',0),'Frame',0,1e9)
        if int(frame)!=frame:raise ValueError('Frame must be an integer')
        hint=params.get('hint','')
        if hint:hint=file_path(hint,'Mask',IMAGES)
        stack=params.get('mask_stack')
        if stack is not None:
            from mask_hint import validate_stack
            validate_stack(stack)
        def action(progress):
            import cv2
            import numpy as np
            from worker import probe
            progress(0,1,'Preparing reference')
            fps,total,w,h=probe(source)
            if frame>=total or w*h>40_000_000:raise ValueError('Reference frame outside source or image too large')
            image=decode_frame(source,int(frame))[:,:,:3]
            if image.shape[:2]!=(h,w):raise ValueError('Invalid source frame')
            self.root.mkdir(exist_ok=True)
            identity=uuid.uuid4().hex;folder=self.root/identity;folder.mkdir()
            if not cv2.imwrite(str(folder/'source.png'),image):raise OSError('Cannot write reference')
            display=image
            mask_path=hint
            if stack is not None:
                from mask_hint import rasterize_stack
                mask_path=rasterize_stack(stack,folder/'layer-mask.png')
            if mask_path:
                mask=cv2.imread(mask_path,cv2.IMREAD_GRAYSCALE)
                if mask is None or mask.shape!=(h,w):raise ValueError('Mask must match source dimensions')
                display=image.copy();red=np.zeros_like(image);red[:,:,2]=255
                strength=(1-mask.astype(np.float32)/255)[:,:,None]*.5
                display=np.clip(display*(1-strength)+red*strength,0,255).astype(np.uint8)
            ratio=min(1,320/w,180/h);display=cv2.resize(display,(round(w*ratio),round(h*ratio)))
            cv2.imwrite(str(folder/'overlay.png'),display)
            stat=Path(source).stat()
            record=dict(id=identity,input=source,frame=int(frame),fps=fps,width=w,height=h,total=total,source_size=stat.st_size,source_mtime=stat.st_mtime_ns)
            with self.lock:self.references[identity]=record
            progress(1,1,'Reference ready')
            return dict(record,path=str(folder/'overlay.png'))
        return self.tasks.start(action)

    def select(self,identity,points,preview_only=False):
        with self.lock:
            if identity not in self.references:raise ValueError('Open reference again')
            record=dict(self.references[identity])
        if not isinstance(points,list):raise ValueError('Invalid selection points')
        def action(progress):
            import cv2
            progress(0,1,'Building colour selection')
            stat=Path(record['input']).stat()
            if (stat.st_size,stat.st_mtime_ns)!=(record['source_size'],record['source_mtime']):raise ValueError('Source changed; open reference again')
            folder=self.root/identity;image=cv2.imread(str(folder/'source.png'))
            if preview_only:
                if not isinstance(points,list) or len(points)>128:raise ValueError('Too many selection points')
                overlay=image.copy();h,w=image.shape[:2]
                for point in points:
                    x=number(point.get('x'),'x',0,1);y=number(point.get('y'),'y',0,1)
                    cv2.circle(overlay,(round(x*(w-1)),round(y*(h-1))),max(3,round(w*.01)),(0,255,0) if point.get('keep') else (0,0,255),-1)
                ratio=min(1,320/w,180/h);overlay=cv2.resize(overlay,(round(w*ratio),round(h*ratio)))
                path=folder/(uuid.uuid4().hex+'-points.png');cv2.imwrite(str(path),overlay)
                progress(1,1,'Points ready')
                return dict(record,path=str(path),points=len(points))
            mask=seeded_mask(image,points);path=folder/(uuid.uuid4().hex+'.png')
            if not cv2.imwrite(str(path),mask):raise OSError('Cannot write selection')
            overlay=image.copy();overlay[mask==0]=(overlay[mask==0]*.4).astype('uint8')
            ratio=min(1,320/image.shape[1],180/image.shape[0]);overlay=cv2.resize(overlay,(round(image.shape[1]*ratio),round(image.shape[0]*ratio)))
            preview=path.with_name(path.stem+'-overlay.png');cv2.imwrite(str(preview),overlay)
            progress(1,1,'Selection ready')
            return dict(record,hint=str(path),path=str(preview))
        return self.tasks.start(action)

    def detail(self,params):
        identity=params.get('id')
        with self.jobs.lock:
            if identity not in self.jobs.jobs:raise ValueError('Unknown job')
            job=dict(self.jobs.jobs[identity])
        if job['state']!='completed':raise ValueError('Select a finished job first')
        frame=number(params.get('frame',0),'Frame',0,job['frame_count']-1)
        if int(frame)!=frame:raise ValueError('Frame must be an integer')
        zoom=number(params.get('zoom',1),'Zoom',1,16)
        x=number(params.get('x',.5),'Centre x',0,1);y=number(params.get('y',.5),'Centre y',0,1)
        split=number(params.get('split',.5),'Comparison',0,1)
        view=params.get('view','comparison');background=params.get('background','checker')
        if view not in ('comparison','checker','matte','original') or background not in ('checker','white','black','grey'):raise ValueError('Invalid review mode')
        backdrop=params.get('backdrop','')
        if backdrop:backdrop=file_path(backdrop,'Background',IMAGES|MOVIES)
        def action(progress):
            import cv2
            import numpy as np
            progress(0,1,'Preparing detail')
            original=decode_frame(job['input'],job['first_frame']+int(frame))[:,:,:3]
            if job.get('sequence'):
                files=sorted(Path(job['output']).parent.glob('*.exr'));rgba=cv2.imread(str(files[int(frame)]),cv2.IMREAD_UNCHANGED)
                if rgba is None:raise ValueError('Output frame missing')
                rgb=rgba[:,:,:3];rgba[:,:,:3]=np.where(rgb<=.0031308,rgb*12.92,1.055*np.maximum(rgb,0)**(1/2.4)-.055)
                rgba=np.clip(rgba*255,0,255).astype(np.uint8)
            else:rgba=decode_frame(job['output'],int(frame))
            h,w=rgba.shape[:2]
            if rgba.ndim!=3 or rgba.shape[2]!=4 or w*h>40_000_000:raise ValueError('Output alpha missing or frame too large')
            original=cv2.resize(original,(w,h))
            back=None
            if backdrop:
                if Path(backdrop).suffix.lower() in IMAGES:back=cv2.imread(backdrop)
                else:
                    from worker import probe
                    bf,bn,_,_=probe(backdrop);back=decode_frame(backdrop,min(bn-1,round(frame/job['native_fps']*bf)))
                if back is None:raise ValueError('Background unavailable')
                back=cv2.resize(back[:,:,:3],(w,h))
            result=composite(original,rgba,background,split,view,back)
            cw,ch=max(1,round(w/zoom)),max(1,round(h/zoom))
            left=max(0,min(w-cw,round(x*w-cw/2)));top=max(0,min(h-ch,round(y*h-ch/2)))
            result=result[top:top+ch,left:left+cw]
            ratio=min(1,768/cw,432/ch);result=cv2.resize(result,(max(1,round(cw*ratio)),max(1,round(ch*ratio))))
            self.root.mkdir(exist_ok=True)
            path=self.root/('detail-'+uuid.uuid4().hex+'.png')
            if not cv2.imwrite(str(path),result):raise OSError('Cannot write detail')
            for old in sorted(self.root.glob('detail-*.png'),key=lambda p:p.stat().st_mtime)[:-64]:old.unlink(missing_ok=True)
            progress(1,1,'Detail ready')
            return dict(path=str(path),frame=int(frame),frames=job['frame_count'],fps=job['native_fps'],width=w,height=h)
        return self.tasks.start(action)


def gpu_status():
    try:
        result=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
        devices=[]
        if result.returncode==0:
            for line in result.stdout.strip().splitlines():
                name,total,used,free=line.rsplit(',',3);devices.append(dict(name=name.strip(),total_mb=int(total),used_mb=int(used),free_mb=int(free)))
        return dict(available=bool(devices),devices=devices)
    except (OSError,ValueError,subprocess.TimeoutExpired):return dict(available=False,devices=[])
