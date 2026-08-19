from __future__ import annotations

from ursina import Entity, color

def _box(parent, position, scale, tint): return Entity(parent=parent, model="cube", position=position, scale=scale, color=tint, unlit=True)

class PayloadVariantA(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); metal=color.rgb(205,213,220); panel=color.rgb(28,78,158); cell=color.rgb(62,118,192)
        _box(self,(0,0,0),(0.34,0.25,0.29),metal)
        for x in (-0.43,0.43):
            _box(self,(x,0,0),(0.50,0.025,0.21),panel)
            for z in (-0.065,0.0,0.065): _box(self,(x,0.014,z),(0.45,0.009,0.018),cell)
        Entity(parent=self,model="sphere",position=(0,-0.02,-0.20),scale=(0.22,0.10,0.08),color=color.rgb(235,235,228),unlit=True)
class PayloadVariantB(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); body=color.rgb(196,201,205); panel=color.rgb(24,92,165)
        _box(self,(0,0,0),(0.28,0.34,0.28),body); _box(self,(0,0.24,0),(0.18,0.12,0.18),color.rgb(105,112,120)); _box(self,(-0.36,0,0),(0.42,0.035,0.32),panel); _box(self,(0.36,0,0),(0.42,0.035,0.32),panel)
        Entity(parent=self,model="sphere",position=(0,0,-0.24),scale=(0.18,0.18,0.09),color=color.rgb(225,226,220),unlit=True)
class PayloadVariantC(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); gold=color.rgb(191,153,72); panel=color.rgb(41,87,155)
        _box(self,(0,0,0),(0.42,0.24,0.24),gold); _box(self,(0,0,0.28),(0.22,0.18,0.34),color.rgb(184,188,193))
        for y in (-0.31,0.31): _box(self,(0,y,0),(0.28,0.42,0.03),panel)
        Entity(parent=self,model="sphere",position=(0,0,-0.22),scale=(0.17,0.12,0.07),color=color.rgb(238,238,232),unlit=True)
class RocketBodyVariantA(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); metal=color.rgb(205,208,204); dark=color.rgb(86,91,98); _box(self,(0,0,0),(0.22,0.22,0.86),metal); Entity(parent=self,model="sphere",position=(0,0,0.46),scale=(0.23,0.23,0.18),color=metal,unlit=True); _box(self,(0,0,-0.50),(0.32,0.32,0.18),dark); _box(self,(0,0,-0.64),(0.16,0.16,0.20),dark)
class RocketBodyVariantB(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); _box(self,(0,0,0),(0.28,0.28,0.72),color.rgb(185,191,197)); _box(self,(0,0,0.38),(0.34,0.34,0.10),color.rgb(183,104,49)); _box(self,(0,0,-0.42),(0.38,0.38,0.16),color.rgb(78,82,88))
class RocketBodyVariantC(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); white=color.rgb(224,225,221); dark=color.rgb(66,72,79); _box(self,(0,0,0),(0.18,0.18,0.98),white); _box(self,(0,0,0.48),(0.24,0.24,0.10),dark); _box(self,(0,0,-0.53),(0.34,0.34,0.18),dark)
class DebrisVariantA(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); _box(self,(0,0,0),(0.28,0.13,0.42),color.rgb(150,154,158)); _box(self,(0.16,0.08,-0.12),(0.23,0.08,0.19),color.rgb(95,99,105)); self.rotation=(17,31,13)
class DebrisVariantB(Entity):
    def __init__(self, **kwargs): super().__init__(**kwargs); _box(self,(0,0,0),(0.20,0.08,0.52),color.rgb(135,140,147)); self.rotation=(34,11,27)
class DebrisVariantC(Entity):
    def __init__(self, **kwargs): super().__init__(**kwargs); _box(self,(0,0,0),(0.22,0.20,0.18),color.rgb(147,151,156)); self.rotation=(9,48,22)
class SpaceObjectMiniature(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); self.payload_variants=[PayloadVariantA(parent=self),PayloadVariantB(parent=self,enabled=False),PayloadVariantC(parent=self,enabled=False)]; self.rocket_variants=[RocketBodyVariantA(parent=self,enabled=False),RocketBodyVariantB(parent=self,enabled=False),RocketBodyVariantC(parent=self,enabled=False)]; self.debris_variants=[DebrisVariantA(parent=self,enabled=False),DebrisVariantB(parent=self,enabled=False),DebrisVariantC(parent=self,enabled=False)]
    def set_type(self, object_type: str, variant: int = 0):
        kind=(object_type or "UNKNOWN").upper(); variant=int(variant)%3
        for e in self.payload_variants+self.rocket_variants+self.debris_variants: e.enabled=False
        (self.rocket_variants if kind=="ROCKET BODY" else self.debris_variants if kind=="DEBRIS" else self.payload_variants)[variant].enabled=True
class IssModel(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs); metal=color.rgb(218,224,230); dark=color.rgb(128,140,150); panel=color.rgb(34,82,158); radiator=color.rgb(236,238,238)
        _box(self,(0,0,0),(4.8,0.09,0.09),dark); _box(self,(0,0,0),(0.92,0.26,0.32),metal); _box(self,(0,0,0.33),(0.35,0.24,0.76),metal); _box(self,(0,0,-0.34),(0.29,0.22,0.65),metal)
        for x in (-1.05,1.05): _box(self,(x,0.28,0),(0.62,0.04,0.58),radiator); _box(self,(x,-0.28,0),(0.62,0.04,0.58),radiator)
        for x in (-2.12,-1.53,1.53,2.12):
            _box(self,(x,0,0),(0.06,0.78,0.06),dark)
            for y in (-0.88,0.88): _box(self,(x,y,0),(0.44,1.30,0.035),panel)

def build_satellite_model(parent: Entity, is_iss: bool=False) -> Entity: return IssModel(parent=parent,scale=.25) if is_iss else SpaceObjectMiniature(parent=parent,scale=.12)
