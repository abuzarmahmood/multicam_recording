#!/usr/bin/env python3
"""
Tkinter GUI for multicam video recording via ffmpeg.
Wraps the same ffmpeg commands used by parallel2video_ffmpeg.sh with a
point-and-click interface so non-coders can start recordings without
touching the terminal.
"""

import json
import os
import signal
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
DEFAULT_OUTPUT_DIR = "./recorded_videos"


def load_config():
    """Load config.json and return the dict."""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        messagebox.showerror("Config Error", f"Cannot load config.json:\n{exc}")
        sys.exit(1)


class RecordingGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Multicam Recording (FFmpeg)")
        self.geometry("700x580")
        self.resizable(True, True)
        self.config_data = load_config()
        self.recording_process = None
        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self):
        # --- Output directory ---
        frame_dir = tk.LabelFrame(self, text="Output Directory", padx=8, pady=4)
        frame_dir.pack(fill="x", padx=10, pady=(10, 4))

        self.output_dir_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        tk.Entry(frame_dir, textvariable=self.output_dir_var, width=60).pack(
            side="left", fill="x", expand=True, padx=(0, 6)
        )
        tk.Button(frame_dir, text="Browse…", command=self._browse_dir).pack(side="right")

        # --- Recording name ---
        frame_name = tk.LabelFrame(self, text="Recording Name", padx=8, pady=4)
        frame_name.pack(fill="x", padx=10, pady=4)

        self.name_var = tk.StringVar()
        tk.Entry(frame_name, textvariable=self.name_var, width=40).pack(
            side="left", fill="x", expand=True
        )

        # --- Camera devices ---
        frame_cams = tk.LabelFrame(self, text="Camera Devices (from config.json)", padx=8, pady=4)
        frame_cams.pack(fill="x", padx=10, pady=4)

        devices = self.config_data.get("video_devices", [])
        self.device_vars = []
        for dev in devices:
            var = tk.BooleanVar(value=True)
            self.device_vars.append((dev, var))
            tk.Checkbutton(frame_cams, text=dev, variable=var).pack(anchor="w")

        if not devices:
            tk.Label(frame_cams, text="No devices configured in config.json", fg="red").pack()

        # --- FFmpeg recording mode ---
        frame_mode = tk.LabelFrame(self, text="Recording Mode", padx=8, pady=4)
        frame_mode.pack(fill="x", padx=10, pady=4)

        self.mode_var = tk.StringVar(value="full_color")
        tk.Radiobutton(
            frame_mode, text="Full color (H.264, 1280x720, 30 fps)",
            variable=self.mode_var, value="full_color",
        ).pack(anchor="w")
        tk.Radiobutton(
            frame_mode, text="Single channel – Y/luminance only (better performance)",
            variable=self.mode_var, value="single_channel",
        ).pack(anchor="w")
        tk.Radiobutton(
            frame_mode, text="Copy mode (-c:v copy) – fastest, no transcoding",
            variable=self.mode_var, value="copy_mode",
        ).pack(anchor="w")

        # --- Buttons ---
        frame_btns = tk.Frame(self, pady=6)
        frame_btns.pack(fill="x", padx=10)

        self.start_btn = tk.Button(
            frame_btns, text="Start Recording", bg="#4CAF50", fg="white",
            font=("sans-serif", 12, "bold"), command=self._start_recording,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(
            frame_btns, text="Stop Recording", bg="#f44336", fg="white",
            font=("sans-serif", 12, "bold"), command=self._stop_recording,
            state="disabled",
        )
        self.stop_btn.pack(side="left")

        self.status_label = tk.Label(frame_btns, text="Idle", fg="gray")
        self.status_label.pack(side="right")

        # --- Log output ---
        frame_log = tk.LabelFrame(self, text="Log", padx=4, pady=4)
        frame_log.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        self.log_text = scrolledtext.ScrolledText(frame_log, height=10, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

    # ── Helpers ───────────────────────────────────────────────────────

    def _browse_dir(self):
        d = filedialog.askdirectory(title="Select output directory")
        if d:
            self.output_dir_var.set(d)

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_status(self, text, color="gray"):
        self.status_label.config(text=text, fg=color)

    # ── Recording control ─────────────────────────────────────────────

    def _start_recording(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Please enter a recording name.")
            return

        selected_devices = [dev for dev, var in self.device_vars if var.get()]
        if not selected_devices:
            messagebox.showwarning("No cameras", "Select at least one camera device.")
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("No directory", "Please choose an output directory.")
            return

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        fin_name = f"{name}_video_{timestamp}"
        rec_dir = os.path.join(output_dir, fin_name)
        os.makedirs(rec_dir, exist_ok=True)

        # Build the parallel ffmpeg command (mirrors parallel2video_ffmpeg.sh)
        device_list = "\\n".join(f"{i}:{dev}" for i, dev in enumerate(selected_devices))
        num_cams = len(selected_devices)
        mode = self.mode_var.get()

        if mode == "single_channel":
            cmd = (
                f"echo -e '{device_list}' | parallel -j {num_cams} --colsep ':' "
                f"ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -i {{2}} "
                f"-s 1280x720 -r 30 -vf \"extractplanes=y\" -c:v libx264 -preset ultrafast "
                f"-crf 23 -pix_fmt yuv420p {rec_dir}/{fin_name}_cam{{1}}.mp4"
            )
        elif mode == "copy_mode":
            cmd = (
                f"echo -e '{device_list}' | parallel -j {num_cams} --colsep ':' "
                f"ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -input_format mjpeg "
                f"-i {{2}} -r 60 -c:v copy {rec_dir}/{fin_name}_cam{{1}}.mp4"
            )
        else:  # full_color
            cmd = (
                f"echo -e '{device_list}' | parallel -j {num_cams} --colsep ':' "
                f"ffmpeg -use_wallclock_as_timestamps 1 -copyts -f v4l2 -i {{2}} "
                f"-s 1280x720 -r 30 -c:v libx264 -preset ultrafast -crf 23 "
                f"-pix_fmt yuv420p {rec_dir}/{fin_name}_cam{{1}}.mp4"
            )

        # Write start marker
        marker_path = os.path.join(rec_dir, f"{fin_name}_markers.txt")
        with open(marker_path, "w") as f:
            f.write(f"{datetime.now().timestamp():.3f}\n")

        self._log(f"Recording to: {rec_dir}\n")
        self._log(f"Mode: {mode}\n")
        self._log(f"Cameras: {', '.join(selected_devices)}\n\n")
        self._set_status("Recording…", "red")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        self._marker_path = marker_path
        self._rec_dir = rec_dir
        self._fin_name = fin_name
        self._num_cams = num_cams

        # Launch in background thread
        self.recording_process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )
        threading.Thread(target=self._read_output, daemon=True).start()

    def _read_output(self):
        proc = self.recording_process
        for line in iter(proc.stdout.readline, b""):
            self.after(0, self._log, line.decode(errors="replace"))
        proc.wait()
        self.after(0, self._recording_finished)

    def _stop_recording(self):
        if self.recording_process and self.recording_process.poll() is None:
            # Send SIGINT to the process group so ffmpeg flushes properly
            os.killpg(os.getpgid(self.recording_process.pid), signal.SIGINT)
            self._log("\nStopping recording…\n")

    def _recording_finished(self):
        # Write stop marker
        if hasattr(self, "_marker_path"):
            with open(self._marker_path, "a") as f:
                f.write(f"{datetime.now().timestamp():.3f}\n")

        # Extract timestamps from video files
        if hasattr(self, "_rec_dir"):
            self._log("Extracting timestamps from video files…\n")
            for i in range(self._num_cams):
                video_file = os.path.join(self._rec_dir, f"{self._fin_name}_cam{i}.mp4")
                ts_file = os.path.join(self._rec_dir, f"cam{i}_timestamps.txt")
                if os.path.isfile(video_file):
                    subprocess.run(
                        ["ffmpeg", "-i", video_file, "-f", "mkvtimestamp_v2", "-copyts", ts_file],
                        capture_output=True,
                    )
                    self._log(f"  Timestamps saved to {ts_file}\n")

        self._set_status("Idle", "gray")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._log("\nRecording complete.\n")
        self.recording_process = None


def main():
    app = RecordingGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
