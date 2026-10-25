"""Rasterize a snapshot of one closed EffectCraft Add mask in source pixels."""
from options import number


def validate_mask(mask):
    if not isinstance(mask, dict) or set(mask) != {'vertices','inTangents','outTangents','width','height','inverted','opacity','feather','expansion'}:
        raise ValueError('Ungültige Ebenenmaske')
    for key in ('width','height'):
        number(mask[key],key,1,16384)
        if int(mask[key])!=mask[key]: raise ValueError('Ungültige Bildgröße')
    if mask['width']*mask['height']>40_000_000: raise ValueError('Maskenbild zu groß')
    vertices=mask['vertices']
    if not isinstance(vertices,list) or not 3<=len(vertices)<=512: raise ValueError('Maske benötigt 3 bis 512 Punkte')
    for key in ('vertices','inTangents','outTangents'):
        points=mask[key]
        if not isinstance(points,list) or len(points)!=len(vertices):raise ValueError('Ungültige Maskenkurve')
        for point in points:
            if not isinstance(point,list) or len(point)!=2:raise ValueError('Ungültiger Maskenpunkt')
            for value in point:number(value,'Maskenpunkt',-1e6,1e6)
    if not isinstance(mask['inverted'],bool):raise ValueError('Ungültige Maskeninvertierung')
    number(mask['opacity'],'Maskendeckkraft',0,100)
    number(mask['expansion'],'Maskenausdehnung',-128,128)
    if not isinstance(mask['feather'],list) or len(mask['feather'])!=2:raise ValueError('Ungültige Maskenweichheit')
    for value in mask['feather']:number(value,'Maskenweichheit',0,128)
    return mask


def rasterize(mask, path):
    import cv2
    import numpy as np
    validate_mask(mask)
    v=np.array(mask['vertices']); incoming=np.array(mask['inTangents']); outgoing=np.array(mask['outTangents'])
    points=[]
    for i in range(len(v)):
        j=(i+1)%len(v)
        # Sample cubic Bezier including handles, up to roughly one sample/pixel.
        length=sum(np.linalg.norm(b-a) for a,b in zip([v[i],v[i]+outgoing[i],v[j]+incoming[j]],[v[i]+outgoing[i],v[j]+incoming[j],v[j]]))
        t=np.linspace(0,1,min(4096,max(8,int(length)+1)))[:,None]
        points.append((1-t)**3*v[i]+3*(1-t)**2*t*(v[i]+outgoing[i])+3*(1-t)*t**2*(v[j]+incoming[j])+t**3*v[j])
    pixels=np.zeros((int(mask['height']),int(mask['width'])),dtype='uint8')
    cv2.fillPoly(pixels,[np.round(np.concatenate(points)).astype('int32')],255,lineType=cv2.LINE_AA)
    expansion=round(abs(mask['expansion']))
    if expansion:
        kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*expansion+1,2*expansion+1))
        pixels=(cv2.dilate if mask['expansion']>0 else cv2.erode)(pixels,kernel)
    x,y=mask['feather']
    if x or y: pixels=cv2.GaussianBlur(pixels,(2*int(x*3)+1,2*int(y*3)+1),sigmaX=max(.001,x),sigmaY=max(.001,y))
    if mask['inverted']:pixels=255-pixels
    pixels=np.round(pixels*(mask['opacity']/100)).astype('uint8')
    if not cv2.imwrite(str(path),pixels):raise RuntimeError('Startmaske konnte nicht gespeichert werden')
    return str(path)
