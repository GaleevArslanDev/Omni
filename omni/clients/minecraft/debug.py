from pathlib import Path

from javascript import require

_HELPER_PATH = str(
    Path(__file__).with_name("prismarine_headless.js").resolve()
).replace("\\", "/")

start_filtered_headless = require(_HELPER_PATH)


class DebugMixin:
    def init_debug_stream(
        self,
        host: str = "127.0.0.1",
        port: int = 8089,
        width: int = 640,
        height: int = 360,
        frames: int = -1,
    ) -> None:
        self._debug_stream_enabled = True
        self._debug_stream_host = host
        self._debug_stream_port = port
        self._debug_stream_width = width
        self._debug_stream_height = height
        self._debug_stream_frames = frames
        self._debug_viewer_client = None
        self._debug_stream_last_error = None

    def start_debug_stream(self) -> None:
        if not getattr(self, "_debug_stream_enabled", False):
            return
        if self.bot is None or self._debug_viewer_client is not None:
            return

        try:
            output = f"{self._debug_stream_host}:{self._debug_stream_port}"
            self._debug_stream_last_error = None
            self._debug_viewer_client = start_filtered_headless(self.bot, {
                "output": output,
                "frames": self._debug_stream_frames,
                "width": self._debug_stream_width,
                "height": self._debug_stream_height,
            })
        except Exception as error:
            self._debug_viewer_client = None
            self._debug_stream_last_error = str(error)

    def stop_debug_stream(self) -> None:
        client = getattr(self, "_debug_viewer_client", None)
        if client is None:
            return

        try:
            if hasattr(client, "end"):
                client.end()
            elif hasattr(client, "close"):
                client.close()
        except Exception:
            pass
        finally:
            self._debug_viewer_client = None
