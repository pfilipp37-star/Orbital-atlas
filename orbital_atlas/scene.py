from __future__ import annotations
from ursina import Button,Entity,Text,Texture,Vec3,camera,color
from .camera import FocusAnimator,FreeFly,OrbitCamera,Starfield
from .catalog_ui import SatelliteCatalogUI
from .config import APP_VERSION,SATELLITE_LIMIT
from .earth_mesh import build_wgs84_earth_mesh
from .font_support import configure_multilingual_font
from .i18n import LANGUAGES,tr
from .launch_layer import LaunchLayer
from .point_style import apply_satellite_point_style
from .satellite_layer import SatelliteLayer
from .textures import ensure_earth_texture
from .video_panel import NasaLivePanel

class OrbitalAtlasScene(Entity):
    def __init__(self,earth_texture=None,stream_url=None,show_video=True,satellite_limit=SATELLITE_LIMIT,allow_network=True):
        super().__init__();configure_multilingual_font();Starfield();self.language="en";self.version=Text(parent=camera.ui,text=f"ORBITAL ATLAS  {APP_VERSION}",position=(-.875,.475),origin=(-.5,.5),scale=.48,color=color.rgba32(92,176,225,210));self.legend=Text(parent=camera.ui,text=tr("en","legend"),position=(-.875,.447),origin=(-.5,.5),scale=.37,color=color.rgba32(130,166,191,205));self.root=Entity();tex=Texture(ensure_earth_texture(earth_texture),filtering="bilinear");tex.repeat=False;self.earth=Entity(parent=self.root,model=build_wgs84_earth_mesh(),texture=tex,color=color.white,unlit=True,double_sided=True);self.orbit=OrbitCamera();self.free=FreeFly(self.orbit);self.focus=FocusAnimator(self.free);self.sats=SatelliteLayer(self.root,satellite_limit,allow_network);apply_satellite_point_style(self.sats);self.launches=LaunchLayer(self.root,self.orbit,allow_network);self.sats.on_selected=self._focus_selected;self.ui=SatelliteCatalogUI(on_filter_change=self.sats.apply_filter,on_language_change=self.set_language,language="en");self.sats.attach_ui(self.ui);self.free_btn=Button(parent=camera.ui,text=tr("en","mode_free"),position=(.61,.456),scale=(.085,.041),color=color.rgba32(20,42,62,255),on_click=self.toggle_free);self.focus_btn=Button(parent=camera.ui,text=tr("en","focus"),position=(.705,.456),scale=(.10,.041),color=color.rgba32(16,60,95,255),on_click=self.focus_selected);self.earth_btn=Button(parent=camera.ui,text=tr("en","earth"),position=(.815,.456),scale=(.085,.041),color=color.rgba32(22,52,76,255),on_click=self.reset_view);enabled=bool(show_video and stream_url and "PLACEHOLDER" not in stream_url);self.video=NasaLivePanel(stream_url=stream_url,enabled=enabled) if stream_url else NasaLivePanel(enabled=False)
    def set_language(self,l):
        self.language=l if l in LANGUAGES else "en";self.legend.text=tr(self.language,"legend");self.ui.language=self.language;self.ui._sync_filter_labels();self.sats.set_language(self.language);self.launches.set_language(self.language);self.free_btn.text=tr(self.language,"mode_orbit") if self.free.enabled else tr(self.language,"mode_free");self.focus_btn.text=tr(self.language,"focus");self.earth_btn.text=tr(self.language,"earth")
    def input(self,key):
        if key.lower()=="f":self.toggle_free()
        elif key.lower()=="g":self.focus_selected()
        elif key.lower()=="r":self.reset_view()
    def toggle_free(self):
        if self.free.enabled:self.free.disable_mode()
        else:self.free.enable_mode()
        self.free_btn.text=tr(self.language,"mode_orbit") if self.free.enabled else tr(self.language,"mode_free")
    def _focus_selected(self,_i):self.focus_selected()
    def focus_selected(self):
        if self.sats.selected_state:self.focus.begin(lambda:Vec3(*self.sats.selected_state.xyz),.62)
    def reset_view(self):
        self.focus.active=False
        if self.free.enabled:self.free.disable_mode()
        self.orbit.reset();self.orbit.apply();self.free_btn.text=tr(self.language,"mode_free")
