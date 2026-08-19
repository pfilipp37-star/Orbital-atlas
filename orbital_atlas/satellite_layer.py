from __future__ import annotations
import math, threading
import numpy as np
from ursina import Entity,Mesh,Text,Vec2,Vec3,camera,clamp,color,mouse,scene,time
from .config import AUTO_LOD_DISTANCE,AUTO_LOD_MAX_MODELS,CACHE_DIR,EARTH_EQUATORIAL_RADIUS,ISS_NORAD_ID,MINIATURE_POOL_SIZE,ORBIT_TRACK_REFRESH_SECONDS,ORBIT_TRACK_SAMPLES,ORBIT_TRACK_THICKNESS,SATELLITE_CLICK_RADIUS
from .geo import EARTH_POLAR_RADIUS_SCENE,visible_points_from_camera_mask
from .i18n import LANGUAGES,tr
from .metadata import SatcatMetadataLoader
from .miniatures import IssModel,SpaceObjectMiniature
from .orbits import SatelliteCatalogLoader,SatellitePropagationWorker,satellite_catalog_number,satellite_display_name,satellite_object_type,satellite_scene_state,satellite_track_scene_xyz

class SatelliteLayer(Entity):
    def __init__(self,root,limit,network):
        super().__init__(parent=root);self.loader=SatelliteCatalogLoader(CACHE_DIR);self.meta_loader=SatcatMetadataLoader(CACHE_DIR);self.ts=self.loader.ts;self.satellites=[];self.metadata={};self.worker=None;self.xyz=None;self.visible=None;self.mask=None;self.selected=None;self.selected_index=None;self.selected_state=None;self.language='en';self.ui=None;self.on_selected=None;self._last=None;self._orbit_t=0.;self._mouse=None;self._lock=threading.Lock();self._pc=None;self._pm=None;self.layers={};self.front_layers={}
        for cls,px in [('TINY',1.85),('SMALL',2.75),('MEDIUM',3.55),('LARGE',4.6)]:
            m=Mesh(vertices=[Vec3()],colors=[color.white],mode='point',thickness=px,render_points_in_3d=False,static=False);self.layers[cls]=(m,Entity(parent=self,model=m,unlit=True,enabled=False));fp={'TINY':4.8,'SMALL':6.2,'MEDIUM':8.,'LARGE':10.}[cls];fm=Mesh(vertices=[Vec3()],colors=[color.white],mode='point',thickness=fp,render_points_in_3d=False,static=False);self.front_layers[cls]=(fm,Entity(parent=self,model=fm,unlit=True,enabled=False))
        self.mini=[SpaceObjectMiniature(parent=self,scale=.06,enabled=False) for _ in range(MINIATURE_POOL_SIZE)];self.iss=IssModel(parent=self,scale=.11,enabled=False);self.sel_model=SpaceObjectMiniature(parent=self,scale=.17,enabled=False);self.track=Mesh(vertices=[Vec3(),Vec3()],mode='line',thickness=ORBIT_TRACK_THICKNESS,static=False);self.track_entity=Entity(parent=self,model=self.track,unlit=True,enabled=False);self.probe=Entity(parent=self,add_to_scene_entities=False);self.help=Text(parent=camera.ui,text=tr('en','help'),position=(-.84,-.472),origin=(-.5,-.5),scale=.5,color=color.rgba32(165,196,220,220));self.count=Text(parent=camera.ui,text=tr('en','catalog_loading'),position=(.84,-.472),origin=(.5,-.5),scale=.52,color=color.rgba32(150,202,235,235));self.title=Text(parent=camera.ui,text='',position=(-.83,-.115),origin=(-.5,.5),scale=.62,color=color.rgba32(255,222,78,255));self.info_bg=Entity(parent=camera.ui,model='quad',position=(-.61,-.285),scale=(.47,.32),color=color.rgba32(3,9,17,244),enabled=False);self.info=Text(parent=camera.ui,text='',position=(-.815,-.15),origin=(-.5,.5),scale=.47,color=color.rgba32(230,240,250,255),enabled=False);threading.Thread(target=self._load,args=(limit,network),daemon=True).start();threading.Thread(target=self._load_meta,args=(network,),daemon=True).start()
    def _load(self,limit,network):
        c=self.loader.load(limit,network)
        with self._lock:self._pc=c
    def _load_meta(self,network):
        m=self.meta_loader.load(network)
        with self._lock:self._pm=m
    def attach_ui(self,ui):self.ui=ui;ui.set_catalog(self.metadata,self.satellites);self.apply_filter(ui.current_filter())
    def set_language(self,l):self.language=l if l in LANGUAGES else 'en';self.help.text=tr(self.language,'help');self._info()
    def update(self):
        self._orbit_t+=float(time.dt);self._consume();self._snapshot()
        if self.selected is not None and self._orbit_t>=ORBIT_TRACK_REFRESH_SECONDS:self._orbit_t=0.;self._refresh_track()
    def input(self,key):
        if key=='left mouse down' and mouse.hovered_entity is None:self._mouse=Vec2(float(mouse.x),float(mouse.y))
        elif key=='left mouse up' and self._mouse is not None:
            d=Vec2(float(mouse.x),float(mouse.y))-self._mouse;self._mouse=None
            if d.x*d.x+d.y*d.y<.00035:self._pick()
        elif key.lower()=='c':self.clear()
    def _consume(self):
        with self._lock:c,m=self._pc,self._pm;self._pc=self._pm=None
        if m is not None:self.metadata=m
        if c is None:return
        self.ts=c.timescale;self.satellites=c.satellites;self.mask=np.ones(len(self.satellites),bool)
        if self.ui:self.ui.set_catalog(self.metadata,self.satellites);self.apply_filter(self.ui.current_filter())
        if not self.satellites:self.count.text=tr(self.language,'catalog_none');return
        self.count.text=tr(self.language,'catalog_max' if c.source_status=='MAX' else 'catalog_partial',count=f'{len(self.satellites):,}'.replace(',',' '));self.worker=SatellitePropagationWorker(self.satellites,self.ts);self.worker.start()
    def _snapshot(self):
        if not self.worker:return
        s=self.worker.latest()
        if s is None or s.generated_monotonic==self._last:return
        self._last=s.generated_monotonic;self.xyz=s.xyz;self._render()
    def _kind(self,i):
        m=self.metadata.get(satellite_catalog_number(self.satellites[i]));return m.object_type if m else satellite_object_type(self.satellites[i])
    def _cls(self,i):
        k=self._kind(i).upper();n=satellite_display_name(self.satellites[i]).upper();return 'TINY' if k=='DEBRIS' else 'MEDIUM' if k=='ROCKET BODY' else 'LARGE' if any(x in n for x in ['ISS','TIANGONG','HUBBLE','JWST']) else 'SMALL'
    @staticmethod
    def _color(k):
        k=k.upper();return color.rgba32(255,165,74,245) if k=='ROCKET BODY' else color.rgba32(165,172,182,205) if k=='DEBRIS' else color.rgba32(190,125,245,225) if k=='UNKNOWN' else color.rgba32(108,196,255,245)
    def _disc_clear(self,pts,cam):
        c=np.array([cam.x,cam.y,cam.z],float);cd=np.linalg.norm(c)
        if cd<=EARTH_EQUATORIAL_RADIUS:return np.ones(len(pts),bool)
        v=pts-c;d=np.linalg.norm(v,axis=1);u=np.zeros_like(v);ok=d>1e-9;u[ok]=v[ok]/d[ok,None];beta=np.arccos(np.clip(u@(-c/cd),-1,1));alpha=math.asin(min(.999999,EARTH_EQUATORIAL_RADIUS/cd))*1.035;return beta>alpha
    def _fill(self,buckets,layers):
        for cls,(mesh,ent) in layers.items():
            ids=buckets[cls];ent.enabled=bool(ids)
            if ids:mesh.vertices=[Vec3(*map(float,self.xyz[i])) for i in ids];mesh.colors=[self._color(self._kind(i)) for i in ids];mesh.generate()
    def _render(self):
        if self.xyz is None or not self.satellites:return
        cam=self.getRelativePoint(scene,camera.world_position);valid=np.isfinite(self.xyz).all(axis=1);vis=valid&visible_points_from_camera_mask((cam.x,cam.y,cam.z),self.xyz,equatorial_radius=EARTH_EQUATORIAL_RADIUS,polar_radius=EARTH_POLAR_RADIUS_SCENE)
        if self.mask is not None:vis&=self.mask
        self.visible=vis;clear=self._disc_clear(self.xyz,cam);outer={x:[] for x in self.layers};front={x:[] for x in self.front_layers};iss_i=None
        for i,s in enumerate(self.satellites):
            if satellite_catalog_number(s)==ISS_NORAD_ID:iss_i=i;break
        for j in np.flatnonzero(vis):
            i=int(j)
            if i==self.selected_index or i==iss_i:continue
            (outer if clear[i] else front)[self._cls(i)].append(i)
        self._fill(outer,self.layers);self._fill(front,self.front_layers)
        if iss_i is not None and valid[iss_i]:p=Vec3(*map(float,self.xyz[iss_i]));self.iss.position=p;self.iss.look_at(Vec3());self.iss.enabled=bool(vis[iss_i]) or self.selected_index==iss_i
        else:self.iss.enabled=False
        if self.selected_index is not None and valid[self.selected_index]:
            st=satellite_scene_state(self.satellites[self.selected_index],self.ts.now());self.selected_state=st
            if st and satellite_catalog_number(self.satellites[self.selected_index])!=ISS_NORAD_ID:p=Vec3(*st.xyz);self.sel_model.set_type(self._kind(self.selected_index),satellite_catalog_number(self.satellites[self.selected_index])%3);self.sel_model.position=p;self.sel_model.look_at(Vec3());self.sel_model.scale=clamp((camera.world_position-p).length()*.11,.14,.34);self.sel_model.enabled=True
            self._info()
        self._lod(vis)
    def _lod(self,vis):
        cand=np.flatnonzero(vis)
        if self.selected_index is not None:cand=cand[cand!=self.selected_index]
        cam=self.getRelativePoint(scene,camera.world_position)
        if len(cand):pts=self.xyz[cand];d2=np.sum((pts-np.array([cam.x,cam.y,cam.z]))**2,axis=1);keep=d2<=AUTO_LOD_DISTANCE**2;cand=cand[keep];d2=d2[keep];chosen=cand[np.argsort(d2)[:min(AUTO_LOD_MAX_MODELS,len(self.mini),len(cand))]] if len(cand) else []
        else:chosen=[]
        for n,m in enumerate(self.mini):
            if n>=len(chosen):m.enabled=False;continue
            i=int(chosen[n]);m.set_type(self._kind(i),satellite_catalog_number(self.satellites[i])%3);m.position=Vec3(*map(float,self.xyz[i]));m.look_at(Vec3());m.scale=.05 if self._kind(i)=='DEBRIS' else .075;m.enabled=True
    def apply_filter(self,f):
        if not self.satellites:return
        mask=np.ones(len(self.satellites),bool);cq=f.get('country','ALL').casefold()
        for i,s in enumerate(self.satellites):
            m=self.metadata.get(satellite_catalog_number(s));typ=m.object_type if m else satellite_object_type(s)
            if f.get('type','ALL')!='ALL' and typ.upper()!=f['type']:mask[i]=False;continue
            if m is None:
                if cq!='all' or f.get('status','ALL')!='ALL' or f.get('orbit','ALL')!='ALL':mask[i]=False
            else:
                if cq!='all' and cq not in m.country.casefold():mask[i]=False
                if f.get('status','ALL')!='ALL' and m.status!=f['status']:mask[i]=False
                if f.get('orbit','ALL')!='ALL' and m.orbit_class!=f['orbit']:mask[i]=False
        self.mask=mask;self.count.text=tr(self.language,'catalog_shown',shown=f'{int(mask.sum()):,}'.replace(',',' '),total=f'{len(mask):,}'.replace(',',' '));self._render() if self.xyz is not None else None
    def select(self,i):
        if not 0<=i<len(self.satellites):return
        st=satellite_scene_state(self.satellites[i],self.ts.now())
        if st is None:return
        self.selected_index=i;self.selected=self.satellites[i];self.selected_state=st;self._refresh_track();self._info();self._render() if self.xyz is not None else None
        if callable(self.on_selected):self.on_selected(i)
    def _pick(self):
        if self.xyz is None:return
        best=None;bd=SATELLITE_CLICK_RADIUS**2
        for j in np.flatnonzero(self.visible) if self.visible is not None else []:
            i=int(j);self.probe.position=Vec3(*map(float,self.xyz[i]));p=self.probe.screen_position;d=(float(p.x)-float(mouse.x))**2+(float(p.y)-float(mouse.y))**2
            if d<bd:best=i;bd=d
        if best is not None:self.select(best)
    def _refresh_track(self):
        if self.selected is None:return
        pts=satellite_track_scene_xyz(self.selected,self.ts,ORBIT_TRACK_SAMPLES)
        if len(pts)<2:self.track_entity.enabled=False;return
        self.track.vertices=[Vec3(*p) for p in pts];self.track.generate();self.track_entity.color=self._color(self._kind(self.selected_index));self.track_entity.enabled=True
    def _info(self):
        if self.selected is None or self.selected_state is None:return
        n=satellite_catalog_number(self.selected);g=self.selected_state.geodetic;m=self.metadata.get(n);self.title.text=f'{satellite_display_name(self.selected)} • NORAD {n}';self.info.text=(f'{m.country} • {m.mission}\n{tr(self.language,"selection_state")}: {m.status} • {tr(self.language,"selection_type")}: {m.object_type} • {m.orbit_class}\n{tr(self.language,"selection_launch")}: {m.launch_date or "Unknown"}\n{tr(self.language,"selection_height")}: {g.altitude_km:.0f} km' if m else f'{tr(self.language,"selection_type")}: {satellite_object_type(self.selected)}\n{tr(self.language,"selection_height")}: {g.altitude_km:.0f} km');self.info_bg.enabled=self.info.enabled=True
    def clear(self):self.selected=self.selected_state=None;self.selected_index=None;self.track_entity.enabled=False;self.sel_model.enabled=False;self.title.text='';self.info_bg.enabled=self.info.enabled=False
