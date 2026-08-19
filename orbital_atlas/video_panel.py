from __future__ import annotations

import threading
from dataclasses import dataclass
import cv2
import numpy as np
from PIL import Image, ImageDraw
from ursina import Entity, Texture, camera, color
from .config import NASA_HD_STREAM_URL, VIDEO_HEIGHT, VIDEO_OPEN_TIMEOUT_MS, VIDEO_PANEL_DISTANCE, VIDEO_PANEL_HEIGHT, VIDEO_PANEL_RIGHT, VIDEO_PANEL_UP, VIDEO_PANEL_WIDTH, VIDEO_READ_TIMEOUT_MS, VIDEO_WIDTH

@dataclass(slots=True)
class FramePacket:
    frame_id: int
    bgr: np.ndarray

class OpenCVStreamReader:
    def __init__(self, url: str):
        self.url=url; self._lock=threading.Lock(); self._stop=threading.Event(); self._thread=None; self._latest=None; self._frame_id=0; self._active_capture=None
    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear(); self._thread=threading.Thread(target=self._run, name="nasa-video", daemon=True); self._thread.start()
    def stop(self):
        self._stop.set(); cap=self._active_capture
        if cap is not None:
            try: cap.release()
            except Exception: pass
        if self._thread and self._thread.is_alive(): self._thread.join(timeout=1.0)
    def latest(self):
        with self._lock:
            if self._latest is None: return None
            return FramePacket(self._latest.frame_id, self._latest.bgr.copy())
    def _open_capture(self):
        params=[]
        op=getattr(cv2,"CAP_PROP_OPEN_TIMEOUT_MSEC",None); rd=getattr(cv2,"CAP_PROP_READ_TIMEOUT_MSEC",None)
        if op is not None: params += [int(op), int(VIDEO_OPEN_TIMEOUT_MS)]
        if rd is not None: params += [int(rd), int(VIDEO_READ_TIMEOUT_MS)]
        try: cap=cv2.VideoCapture(self.url, cv2.CAP_FFMPEG, params) if params else cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        except (TypeError, cv2.error): cap=cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        if not cap.isOpened(): cap.release(); cap=cv2.VideoCapture(self.url)
        try: cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
        except Exception: pass
        return cap
    def _run(self):
        while not self._stop.is_set():
            cap=self._open_capture(); self._active_capture=cap
            if not cap.isOpened(): cap.release(); self._active_capture=None; self._stop.wait(2.0); continue
            misses=0
            while not self._stop.is_set():
                ok, frame=cap.read()
                if not ok or frame is None:
                    misses += 1
                    if misses >= 12: break
                    self._stop.wait(0.08); continue
                misses=0; self._frame_id += 1
                with self._lock: self._latest=FramePacket(self._frame_id, frame)
            cap.release(); self._active_capture=None; self._stop.wait(0.5)

class NasaLivePanel(Entity):
    def __init__(self, stream_url: str = NASA_HD_STREAM_URL, enabled: bool = True):
        self.stream_url=stream_url; self.reader=None; self._last_uploaded_frame_id=-1
        placeholder="NASA LIVE\nset a current direct .m3u8 URL" if "PLACEHOLDER" in stream_url else "NASA LIVE\nconnecting..."
        self.video_texture=Texture(_make_placeholder_texture(placeholder), filtering="bilinear")
        super().__init__(model="quad", texture=self.video_texture, color=color.white, scale=(VIDEO_PANEL_WIDTH,VIDEO_PANEL_HEIGHT), billboard=True, unlit=True, always_on_top=True, double_sided=True, enabled=enabled)
        if enabled and "PLACEHOLDER" not in stream_url: self.reader=OpenCVStreamReader(stream_url); self.reader.start()
    def update(self):
        if not self.enabled: return
        self.world_position = camera.world_position + camera.forward*VIDEO_PANEL_DISTANCE + camera.right*VIDEO_PANEL_RIGHT + camera.up*VIDEO_PANEL_UP
        if self.reader is None: return
        packet=self.reader.latest()
        if packet is None or packet.frame_id == self._last_uploaded_frame_id: return
        frame=cv2.resize(packet.bgr,(VIDEO_WIDTH,VIDEO_HEIGHT),interpolation=cv2.INTER_AREA); rgba=cv2.cvtColor(frame,cv2.COLOR_BGR2RGBA); rgba=np.ascontiguousarray(np.flipud(rgba))
        self.video_texture._texture.setRamImageAs(rgba.tobytes(),"RGBA"); self._last_uploaded_frame_id=packet.frame_id
    def on_destroy(self):
        if self.reader is not None: self.reader.stop()

def _make_placeholder_texture(text: str) -> Image.Image:
    image=Image.new("RGBA",(VIDEO_WIDTH,VIDEO_HEIGHT),(3,5,9,255)); draw=ImageDraw.Draw(image)
    draw.rectangle((10,10,VIDEO_WIDTH-10,VIDEO_HEIGHT-10),outline=(55,180,255,255),width=3); draw.multiline_text((28,28),text,fill=(225,240,255,255),spacing=8); return image
