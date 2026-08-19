from __future__ import annotations
from dataclasses import dataclass
from ursina import Entity, color

def _box(parent,pos,scale,tint): return Entity(parent=parent,model="cube",position=pos,scale=scale,color=tint,unlit=True)
@dataclass(frozen=True,slots=True)
class RocketStyle:
    family:str; body:object; accent:object; booster_count:int; tallness:float; width:float

def rocket_style(name:str)->RocketStyle:
    n=(name or "").upper(); white=color.rgb(238,239,235); black=color.rgb(45,48,53); orange=color.rgb(225,118,37); grey=color.rgb(180,184,188)
    if "NEW GLENN" in n: return RocketStyle("New Glenn",white,color.rgb(55,104,155),0,1.32,0.17)
    if "VEGA" in n: return RocketStyle("Vega",white,black,0,0.90,0.085)
    if "PSLV" in n: return RocketStyle("PSLV",white,color.rgb(190,65,50),4,0.98,0.11)
    if "GSLV" in n or "LVM3" in n: return RocketStyle("LVM3",white,black,2,1.10,0.14)
    if "ANGARA" in n: return RocketStyle("Angara",white,color.rgb(45,88,165),4,1.08,0.11)
    if "PROTON" in n: return RocketStyle("Proton",color.rgb(205,210,205),black,4,1.04,0.15)
    if "STARSHIP" in n: return RocketStyle("Starship",color.rgb(185,190,194),black,0,1.35,0.18)
    if "FALCON 9" in n or "FALCON HEAVY" in n: return RocketStyle("Falcon",white,black,2 if "HEAVY" in n else 0,1.22,0.12)
    if "SOYUZ" in n: return RocketStyle("Soyuz",color.rgb(188,204,194),orange,4,1.05,0.13)
    if "ELECTRON" in n: return RocketStyle("Electron",black,white,0,0.82,0.08)
    if "ARIANE" in n: return RocketStyle("Ariane",white,color.rgb(50,96,165),2,1.15,0.13)
    if "LONG MARCH" in n or "CHANG ZHENG" in n or "CZ-" in n: return RocketStyle("Long March",white,color.rgb(190,45,45),4,1.08,0.12)
    if "VULCAN" in n: return RocketStyle("Vulcan",white,color.rgb(175,80,40),2,1.12,0.13)
    if "ATLAS" in n: return RocketStyle("Atlas",white,color.rgb(188,120,45),0,1.07,0.12)
    if "SLS" in n: return RocketStyle("SLS",orange,white,2,1.30,0.15)
    if "H3" in n or "H-II" in n: return RocketStyle("H3",white,color.rgb(45,95,180),2,1.08,0.12)
    return RocketStyle("Rocket",white,grey,0,1.0,0.11)
class RocketVisual(Entity):
    def __init__(self,rocket_name:str,**kwargs):
        super().__init__(**kwargs); st=rocket_style(rocket_name); h=st.tallness; w=st.width
        _box(self,(0,0.42*h,0),(w,0.78*h,w),st.body); _box(self,(0,0.86*h,0),(w*.78,.22*h,w*.78),st.accent); Entity(parent=self,model="sphere",position=(0,1.02*h,0),scale=(w*.85,.18*h,w*.85),color=st.body,unlit=True); _box(self,(0,.02*h,0),(w*1.10,.10*h,w*1.10),color.rgb(70,73,78))
        if st.booster_count:
            radius=w*(1.55 if st.booster_count==4 else 1.45); coords=((radius,0),(-radius,0),(0,radius),(0,-radius))
            for x,z in coords[:st.booster_count]: _box(self,(x,.34*h,z),(w*.56,.58*h,w*.56),st.body)
class LaunchSiteModel(Entity):
    def __init__(self,rocket_name:str,**kwargs):
        super().__init__(**kwargs); concrete=color.rgb(42,84,118); steel=color.rgb(242,152,58); dark=color.rgb(24,34,45)
        _box(self,(0,0,0),(.92,.07,.92),concrete); _box(self,(0,.05,0),(.34,.07,.34),dark); _box(self,(-.31,.42,0),(.09,.82,.09),steel); _box(self,(-.16,.55,0),(.28,.04,.05),steel); _box(self,(-.16,.72,0),(.28,.04,.05),steel); self.rocket=RocketVisual(rocket_name,parent=self,position=(.08,.08,0),scale=.48)
