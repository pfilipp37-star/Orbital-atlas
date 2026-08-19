from __future__ import annotations
import math, random
from ursina import Entity, Mesh, Vec2, Vec3, camera, clamp, color, held_keys, mouse, time
from .config import CAMERA_DRAG_SENSITIVITY,CAMERA_MAX_DISTANCE,CAMERA_MAX_PITCH_DEG,CAMERA_MIN_DISTANCE,CAMERA_SHAKE_DECAY,CAMERA_SHAKE_MAX,CAMERA_START_DISTANCE,CAMERA_ZOOM_STEP,FOCUS_ANIMATION_SECONDS,FOCUS_CAMERA_DISTANCE,STAR_COUNT,STAR_MAX_RADIUS,STAR_MIN_RADIUS

def _star_vertices(count: int) -> tuple[list[Vec3], list[object]]:
    rng = random.Random(744); vertices=[]; colors=[]
    for _ in range(count):
        z=rng.uniform(-1.,1.); a=rng.uniform(0.,math.tau); rxy=math.sqrt(max(0.,1.-z*z)); radius=rng.uniform(STAR_MIN_RADIUS,STAR_MAX_RADIUS)
        vertices.append(Vec3(radius*rxy*math.cos(a),radius*z,radius*rxy*math.sin(a))); v=rng.randint(155,255); colors.append(color.rgba32(v,v,min(255,v+8),rng.randint(145,235)))
    return vertices,colors
class Starfield(Entity):
    def __init__(self):
        v,c=_star_vertices(STAR_COUNT); super().__init__(model=Mesh(vertices=v,colors=c,mode="point",thickness=1.4,render_points_in_3d=False,static=True),unlit=True)
class OrbitCamera(Entity):
    def __init__(self):
        super().__init__(); self.distance=CAMERA_START_DISTANCE; self.yaw=0.; self.pitch=4.; self.dragging=False; self.last_mouse=Vec2(0,0); self.shake=0.; self.rng=random.Random(997); self.enabled=True; self.apply()
    def input(self,key):
        if not self.enabled:return
        if key=="left mouse down" and mouse.hovered_entity is None:self.dragging=True;self.last_mouse=Vec2(float(mouse.x),float(mouse.y))
        elif key=="left mouse up":self.dragging=False
        elif key=="scroll up" and mouse.hovered_entity is None:self.distance=max(CAMERA_MIN_DISTANCE,self.distance-CAMERA_ZOOM_STEP)
        elif key=="scroll down" and mouse.hovered_entity is None:self.distance=min(CAMERA_MAX_DISTANCE,self.distance+CAMERA_ZOOM_STEP)
    def update(self):
        if not self.enabled:return
        if self.dragging and held_keys["left mouse"]:
            now=Vec2(float(mouse.x),float(mouse.y));d=now-self.last_mouse;self.last_mouse=now;self.yaw-=float(d.x)*CAMERA_DRAG_SENSITIVITY;self.pitch=clamp(self.pitch-float(d.y)*CAMERA_DRAG_SENSITIVITY,-CAMERA_MAX_PITCH_DEG,CAMERA_MAX_PITCH_DEG)
        self.shake=max(0.,self.shake-CAMERA_SHAKE_DECAY*float(time.dt));self.apply()
    def apply(self):
        yaw=math.radians(self.yaw);pitch=math.radians(self.pitch);cp=math.cos(pitch);p=Vec3(self.distance*cp*math.sin(yaw),self.distance*math.sin(pitch),-self.distance*cp*math.cos(yaw))
        if self.shake:
            a=CAMERA_SHAKE_MAX*self.shake;p+=Vec3(self.rng.uniform(-a,a),self.rng.uniform(-a,a),self.rng.uniform(-a,a))
        camera.position=p;camera.look_at(Vec3(0,0,0));camera.rotation_z=0
    def add_shake(self,amount):self.shake=min(1.,self.shake+max(0.,float(amount)))
    def sync_from_camera(self):
        p=camera.position;d=max(1e-6,p.length());self.distance=clamp(d,CAMERA_MIN_DISTANCE,CAMERA_MAX_DISTANCE);self.pitch=math.degrees(math.asin(clamp(float(p.y)/d,-1.,1.)));self.yaw=math.degrees(math.atan2(float(p.x),-float(p.z)));self.shake=0.
    def reset(self):self.distance=CAMERA_START_DISTANCE;self.yaw=0.;self.pitch=4.;self.shake=0.
class FreeFly(Entity):
    def __init__(self,orbit):super().__init__(enabled=False);self.orbit=orbit;self.dragging=False;self.last_mouse=Vec2(0,0)
    def enable_mode(self):self.enabled=True;self.orbit.enabled=False
    def disable_mode(self):self.enabled=False;self.dragging=False;self.orbit.enabled=True;self.orbit.sync_from_camera()
    def input(self,key):
        if not self.enabled:return
        if key=="right mouse down":self.dragging=True;self.last_mouse=Vec2(float(mouse.x),float(mouse.y))
        elif key=="right mouse up":self.dragging=False
    def update(self):
        if not self.enabled:return
        if self.dragging and held_keys["right mouse"]:
            now=Vec2(float(mouse.x),float(mouse.y));d=now-self.last_mouse;self.last_mouse=now;camera.rotation_y+=float(d.x)*170.;camera.rotation_x=clamp(camera.rotation_x-float(d.y)*170.,-89,89);camera.rotation_z=0
        speed=15. if held_keys["shift"] else 5.;move=Vec3(0,0,0)
        if held_keys["w"]:move+=camera.forward
        if held_keys["s"]:move-=camera.forward
        if held_keys["d"]:move+=camera.right
        if held_keys["a"]:move-=camera.right
        if held_keys["e"]:move+=Vec3(0,1,0)
        if held_keys["q"]:move-=Vec3(0,1,0)
        if move.length()>0:camera.position+=move.normalized()*speed*float(time.dt)
class FocusAnimator(Entity):
    def __init__(self,free):super().__init__();self.free=free;self.active=False;self.t=0.;self.start=Vec3();self.target_fn=None;self.distance=FOCUS_CAMERA_DISTANCE
    def begin(self,target_fn,distance=FOCUS_CAMERA_DISTANCE):self.free.enable_mode();self.active=True;self.t=0.;self.start=Vec3(camera.world_position);self.target_fn=target_fn;self.distance=distance
    def update(self):
        if not self.active or self.target_fn is None:return
        target=Vec3(self.target_fn());radial=target.normalized() if target.length()>0 else Vec3(0,0,-1);end=target+radial*self.distance;self.t=min(1.,self.t+float(time.dt)/max(.05,FOCUS_ANIMATION_SECONDS));q=self.t*self.t*(3-2*self.t);camera.position=self.start*(1-q)+end*q;camera.look_at(target);camera.rotation_z=0
        if self.t>=1:self.active=False
