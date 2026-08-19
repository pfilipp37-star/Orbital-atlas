from __future__ import annotations
import threading
from dataclasses import dataclass
from datetime import datetime,timezone
from ursina import Entity,Text,Vec3,camera,clamp,color,destroy,scene,time
from .camera import OrbitCamera
from .config import CACHE_DIR,EARTH_EQUATORIAL_RADIUS,LAUNCH_ANIMATION_DURATION_SECONDS,LAUNCH_SHAKE_SECONDS,LAUNCH_SITE_LIMIT,LAUNCH_SMOKE_PARTICLES,LAUNCH_TIMER_LABEL_LIMIT
from .geo import EARTH_POLAR_RADIUS_SCENE,geodetic_to_scene_xyz,segment_intersects_wgs84_ellipsoid
from .i18n import LANGUAGES,tr
from .launches import LaunchEvent,UpcomingLaunchLoader
from .rockets import LaunchSiteModel,RocketVisual

@dataclass
class LaunchVisual:
    event:LaunchEvent; model:LaunchSiteModel; timer:Text

class LaunchLayer(Entity):
    def __init__(self,root:Entity,orbit:OrbitCamera,allow_network:bool):
        super().__init__(parent=root);self.orbit=orbit;self.loader=UpcomingLaunchLoader(CACHE_DIR);self.events=[];self.visuals=[];self.pending=None;self.lock=threading.Lock();self.language="en";self.active_id="";self.flight=Entity(parent=self,enabled=False);self.rocket=None;self.smoke=[Entity(parent=self,model="sphere",scale=.02,color=color.rgba32(190,194,198,0),unlit=True,enabled=False) for _ in range(LAUNCH_SMOKE_PARTICLES)];self.smoke_age=[99.0]*len(self.smoke);self.status=Text(parent=camera.ui,text=tr("en","launches_loading"),position=(.82,-.425),origin=(.5,-.5),scale=.47,color=color.rgba32(255,184,90,235));threading.Thread(target=self._load,args=(allow_network,),daemon=True).start()
    def _load(self,n):
        e=self.loader.load(n)
        with self.lock:self.pending=e
    def set_language(self,l):self.language=l if l in LANGUAGES else "en"
    def update(self):
        with self.lock:p=self.pending;self.pending=None
        if p is not None:self.events=p;self._build()
        self._timers();self._next();self._liftoff()
    def _build(self):
        for v in self.visuals:destroy(v.model);destroy(v.timer)
        self.visuals=[];seen=set()
        for e in self.events:
            key=(round(e.latitude,3),round(e.longitude,3))
            if key in seen:continue
            seen.add(key);xyz=geodetic_to_scene_xyz(e.latitude,e.longitude,0,exaggerate_altitude=False)
            if xyz is None:continue
            radial=Vec3(*xyz).normalized();pos=Vec3(*xyz)+radial*.07;m=LaunchSiteModel(e.rocket,parent=self,position=pos,scale=.095);m.look_at(pos+radial);m.rotation_x+=90;txt=Text(parent=camera.ui,text="",origin=(0,0),scale=.58,color=color.rgba32(255,184,76,255),enabled=False);self.visuals.append(LaunchVisual(e,m,txt))
            if len(self.visuals)>=LAUNCH_SITE_LIMIT:break
    @staticmethod
    def countdown(s):
        sign="T-" if s>=0 else "T+";x=abs(int(s));d,r=divmod(x,86400);h,r=divmod(r,3600);m,sec=divmod(r,60);return f"{sign}{d}d {h:02}:{m:02}:{sec:02}" if d else f"{sign}{h:02}:{m:02}:{sec:02}"
    def _timers(self):
        cam=self.getRelativePoint(scene,camera.world_position);c=(cam.x,cam.y,cam.z)
        for i,v in enumerate(self.visuals):
            if i>=LAUNCH_TIMER_LABEL_LIMIT:v.timer.enabled=False;continue
            p=v.model.position
            if segment_intersects_wgs84_ellipsoid(c,(p.x,p.y,p.z),equatorial_radius=EARTH_EQUATORIAL_RADIUS,polar_radius=EARTH_POLAR_RADIUS_SCENE):v.timer.enabled=False;continue
            sp=v.model.screen_position
            if abs(float(sp.x))>.95 or abs(float(sp.y))>.52:v.timer.enabled=False;continue
            v.timer.position=(float(sp.x),float(sp.y)+.038);v.timer.text=f"{v.event.rocket[:18]}\n{self.countdown(v.event.seconds_until)}";v.timer.enabled=True
    def _next(self):
        future=[e for e in self.events if e.net>=datetime.now(timezone.utc)]
        if not future:self.status.text=tr(self.language,"launches_none");return
        e=min(future,key=lambda x:x.net);self.status.text=tr(self.language,"next_launch",rocket=e.rocket,provider=e.provider,countdown=self.countdown(e.seconds_until))
    def _liftoff(self):
        candidates=[e for e in self.events if -LAUNCH_ANIMATION_DURATION_SECONDS<=e.seconds_until<=LAUNCH_SHAKE_SECONDS]
        if not candidates:self.flight.enabled=False;return
        e=min(candidates,key=lambda x:abs(x.seconds_until));xyz=geodetic_to_scene_xyz(e.latitude,e.longitude,0,exaggerate_altitude=False)
        if xyz is None:return
        radial=Vec3(*xyz).normalized();progress=clamp(max(0,-e.seconds_until)/LAUNCH_ANIMATION_DURATION_SECONDS,0,1);self.flight.position=Vec3(*xyz)+radial*(.08+progress*1.25);self.flight.look_at(self.flight.position+radial);self.flight.enabled=True
        if self.rocket is None or self.active_id!=e.launch_id:
            if self.rocket:destroy(self.rocket)
            self.rocket=RocketVisual(e.rocket,parent=self.flight,scale=.15);self.active_id=e.launch_id
        if -e.seconds_until<LAUNCH_SHAKE_SECONDS:self.orbit.add_shake(.25*float(time.dt))
