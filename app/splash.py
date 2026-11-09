"""启动画面：应用起来之前的过渡窗口。

设计成两段，避免黑屏：
    阶段 A  图标旋转，此时还在导入模块；
    阶段 B  转速放慢、底部出现进度条，表示在解压运行库 / 启动界面。

三处容易踩坑的地方：
    1. 图标只有 60° 旋转对称，所以帧序列必须正好覆盖 60°，否则循环时会"倒转"；
    2. 角度由时间推算而不是帧计数，线程被抢占后不会落后再追赶（视觉上的抽搐）；
    3. 用 Tk 的 after 主循环驱动，而不是自己 while + sleep，节奏更稳。
"""

import ctypes
import threading
import time

try:
    import tkinter as tk

    from PIL import Image, ImageTk
except Exception:  # pragma: no cover - 缺依赖时静默降级
    tk = None
    Image = None
    ImageTk = None

from app.theme import ACCENT, BG, BORDER, FG, MUTED

WIDTH = 420
HEIGHT = 250
LOGO = 120

FRAMES = 72                 # 每帧 60/72 ≈ 0.83°，肉眼连续
SYMMETRY = 60.0              # 图形的旋转对称周期
ANIMATION_SECONDS = 1.5
SPEED_FAST = 130.0           # 阶段 A：度/秒
SPEED_SLOW = 42.0            # 阶段 B：度/秒
TICK_MS = 16                 # ≈60fps
TIMEOUT_SECONDS = 30.0

APP_TITLE = "Game Data Agent"


def _native_splash():
    """返回 PyInstaller 原生启动图模块，没有则返回 None。

    onefile 构建时它已经在显示（覆盖解压阶段），此时不能再开 Tk 窗口——
    Tcl 在子线程里跟解释器收尾会打架，实测会以 0x80000003 崩在 tcl86t.dll。
    """
    try:
        import pyi_splash  # type: ignore[import-not-found]

        return pyi_splash
    except Exception:
        return None


def _close_native_splash() -> None:
    """关掉 PyInstaller 原生启动图。"""
    native = _native_splash()
    if native is None:
        return
    try:
        native.close()
    except Exception:
        pass


def _build_frames() -> list:
    """预渲染一个完整对称周期内的旋转帧，背景填成窗口底色。"""
    from core.paths import resource_dir

    path = resource_dir() / "assets" / "icon.png"
    if not path.exists():
        return []

    source = Image.open(path).convert("RGBA").resize((LOGO, LOGO), Image.LANCZOS)
    frames = []
    for index in range(FRAMES):
        angle = -SYMMETRY * index / FRAMES
        canvas = Image.new("RGBA", (LOGO, LOGO), BG)
        rotated = source.rotate(
            angle, resample=Image.BICUBIC, center=(LOGO / 2, LOGO / 2)
        )
        canvas.alpha_composite(rotated)
        frames.append(ImageTk.PhotoImage(canvas.convert("RGB")))
    return frames


class SplashScreen:
    """线程安全的启动画面；所有 Tk 操作都发生在自己的线程里。"""

    def __init__(self) -> None:
        self._status = "正在启动…"
        self._status_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._started_at = 0.0

        self._root = None
        self._canvas = None
        self._frames: list = []
        self._image_id = None
        self._status_id = None
        self._track_id = None
        self._bar_id = None

        self._angle = 0.0
        self._last_tick = 0.0
        self._ticks = 0
        self._closing = False

    # ---- 主线程调用 ----

    def start(self) -> None:
        if _native_splash() is not None:
            # onefile：用原生的，等主窗口出现再收掉
            self._watch_native()
            return
        if tk is None:
            return
        self._started_at = time.perf_counter()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_status(self, text: str) -> None:
        with self._status_lock:
            self._status = text
        native = _native_splash()
        if native is not None:
            try:
                native.update_text(text)
            except Exception:
                pass

    def _watch_native(self) -> None:
        """原生启动图没有动画，只能靠轮询窗口来决定何时收掉。"""

        def run() -> None:
            while not self._app_window_exists():
                time.sleep(0.2)
            time.sleep(0.15)
            _close_native_splash()

        threading.Thread(target=run, daemon=True).start()

    def close(self) -> None:
        self._closing = True

    # ---- 以下都在 splash 线程内执行 ----

    def _read_status(self) -> str:
        with self._status_lock:
            return self._status

    def _run(self) -> None:
        try:
            root = tk.Tk()
        except Exception:
            return

        self._root = root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        x = (root.winfo_screenwidth() - WIDTH) // 2
        y = (root.winfo_screenheight() - HEIGHT) // 2 - 40
        root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
        root.configure(bg=BG)

        canvas = tk.Canvas(
            root,
            width=WIDTH,
            height=HEIGHT,
            bg=BG,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        canvas.pack()
        self._canvas = canvas

        self._frames = _build_frames()
        if self._frames:
            self._image_id = canvas.create_image(WIDTH / 2, 92, image=self._frames[0])

        canvas.create_text(
            WIDTH / 2,
            172,
            text=APP_TITLE,
            fill=FG,
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        self._status_id = canvas.create_text(
            WIDTH / 2,
            198,
            text="正在启动…",
            fill=MUTED,
            font=("Microsoft YaHei UI", 9),
        )

        track_y = 222
        self._track_id = canvas.create_line(
            60, track_y, WIDTH - 60, track_y, fill=BORDER, width=3, state="hidden"
        )
        self._bar_id = canvas.create_line(
            60, track_y, 150, track_y, fill=ACCENT, width=3, state="hidden"
        )

        self._last_tick = time.perf_counter()
        root.after(80, _close_native_splash)
        root.after(0, self._tick)
        root.mainloop()

    def _tick(self) -> None:
        if self._closing:
            return

        now = time.perf_counter()
        delta = now - self._last_tick
        self._last_tick = now
        elapsed = now - self._started_at
        self._ticks += 1

        if elapsed > TIMEOUT_SECONDS:
            self._start_fade()
            return

        stage_b = elapsed > ANIMATION_SECONDS
        speed = SPEED_SLOW if stage_b else SPEED_FAST

        # 角度按时间累加，掉帧也不会影响转速；模掉一个对称周期实现无缝循环
        self._angle = (self._angle + speed * delta) % SYMMETRY
        if self._frames:
            index = int(self._angle / SYMMETRY * FRAMES) % FRAMES
            self._canvas.itemconfigure(self._image_id, image=self._frames[index])

        status = self._read_status()
        self._canvas.itemconfigure(self._status_id, text=status)

        if stage_b:
            self._canvas.itemconfigure(self._track_id, state="normal")
            self._canvas.itemconfigure(self._bar_id, state="normal")
            span = WIDTH - 120 - 90
            phase = (elapsed - ANIMATION_SECONDS) % 1.6 / 1.6
            offset = phase * 2 if phase < 0.5 else (1 - phase) * 2
            left = 60 + span * offset
            self._canvas.coords(self._bar_id, left, 222, left + 90, 222)

        # 每 6 帧（约 100ms）查一次主窗口，省掉频繁的系统调用
        if self._ticks % 6 == 0 and self._app_window_exists():
            self._start_fade()
            return

        self._root.after(TICK_MS, self._tick)

    def _app_window_exists(self) -> bool:
        try:
            return bool(ctypes.windll.user32.FindWindowW(None, APP_TITLE))
        except Exception:
            return False

    def _start_fade(self) -> None:
        self._closing = True
        self._fade(10)

    def _fade(self, level: int) -> None:
        if level < 0:
            try:
                self._root.destroy()
            except Exception:
                pass
            return
        try:
            self._root.attributes("-alpha", level / 10)
            self._root.after(18, lambda: self._fade(level - 1))
        except Exception:
            try:
                self._root.destroy()
            except Exception:
                pass
