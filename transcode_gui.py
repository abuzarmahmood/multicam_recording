#!/usr/bin/env python3
"""
Tkinter GUI for video compression / transcoding.
Provides the same functionality as postprocessing/transcode_copy_videos.sh
and postprocessing/transcode_simple.sh through a point-and-click interface.
"""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


QUALITY_PRESETS = {
    "low":    {"crf": "28", "preset": "fast",     "label": "Low – smaller files, faster"},
    "medium": {"crf": "23", "preset": "medium",   "label": "Medium – balanced"},
    "high":   {"crf": "18", "preset": "slow",     "label": "High – better quality"},
    "ultra":  {"crf": "15", "preset": "veryslow",  "label": "Ultra – best quality, slowest"},
}

VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")


class TranscodeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Compression / Transcoding")
        self.geometry("780x620")
        self.resizable(True, True)
        self.transcode_thread = None
        self._cancel_flag = False
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # --- File selection ---
        frame_files = tk.LabelFrame(self, text="Input Videos", padx=8, pady=4)
        frame_files.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        btn_row = tk.Frame(frame_files)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Add Files…", command=self._add_files).pack(side="left", padx=(0, 4))
        tk.Button(btn_row, text="Add Folder…", command=self._add_folder).pack(side="left", padx=(0, 4))
        tk.Button(btn_row, text="Remove Selected", command=self._remove_selected).pack(side="left", padx=(0, 4))
        tk.Button(btn_row, text="Clear All", command=self._clear_files).pack(side="left")

        self.file_listbox = tk.Listbox(frame_files, selectmode="extended", height=8)
        self.file_listbox.pack(fill="both", expand=True, pady=(4, 0))

        # --- Quality preset ---
        frame_quality = tk.LabelFrame(self, text="Quality Preset", padx=8, pady=4)
        frame_quality.pack(fill="x", padx=10, pady=4)

        self.quality_var = tk.StringVar(value="medium")
        for key, info in QUALITY_PRESETS.items():
            tk.Radiobutton(
                frame_quality, text=info["label"],
                variable=self.quality_var, value=key,
            ).pack(anchor="w")

        # --- Output options ---
        frame_out = tk.LabelFrame(self, text="Output Options", padx=8, pady=4)
        frame_out.pack(fill="x", padx=10, pady=4)

        tk.Label(frame_out, text="Output suffix:").pack(side="left")
        self.suffix_var = tk.StringVar(value="_transcoded")
        tk.Entry(frame_out, textvariable=self.suffix_var, width=20).pack(side="left", padx=(4, 12))

        self.scale_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_out, text="Scale to width:", variable=self.scale_var).pack(side="left")
        self.scale_width_var = tk.StringVar(value="960")
        tk.Entry(frame_out, textvariable=self.scale_width_var, width=6).pack(side="left", padx=(4, 0))
        tk.Label(frame_out, text="px").pack(side="left")

        # --- Buttons ---
        frame_btns = tk.Frame(self, pady=6)
        frame_btns.pack(fill="x", padx=10)

        self.start_btn = tk.Button(
            frame_btns, text="Start Transcoding", bg="#4CAF50", fg="white",
            font=("sans-serif", 12, "bold"), command=self._start_transcode,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.cancel_btn = tk.Button(
            frame_btns, text="Cancel", bg="#f44336", fg="white",
            font=("sans-serif", 12, "bold"), command=self._cancel_transcode,
            state="disabled",
        )
        self.cancel_btn.pack(side="left")

        self.status_label = tk.Label(frame_btns, text="Idle", fg="gray")
        self.status_label.pack(side="right")

        # --- Progress ---
        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 4))

        # --- Log ---
        frame_log = tk.LabelFrame(self, text="Log", padx=4, pady=4)
        frame_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(frame_log, height=8, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

    # ── File management ───────────────────────────────────────────────

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select video files",
            filetypes=[("Video files", " ".join(f"*{e}" for e in VIDEO_EXTENSIONS)), ("All files", "*.*")],
        )
        for p in paths:
            if p not in self.file_listbox.get(0, "end"):
                self.file_listbox.insert("end", p)

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select folder with videos")
        if not folder:
            return
        count = 0
        for root, _dirs, files in os.walk(folder):
            for f in sorted(files):
                if any(f.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                    full = os.path.join(root, f)
                    if full not in self.file_listbox.get(0, "end"):
                        self.file_listbox.insert("end", full)
                        count += 1
        self._log(f"Added {count} video(s) from {folder}\n")

    def _remove_selected(self):
        for idx in reversed(self.file_listbox.curselection()):
            self.file_listbox.delete(idx)

    def _clear_files(self):
        self.file_listbox.delete(0, "end")

    # ── Helpers ───────────────────────────────────────────────────────

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_status(self, text, color="gray"):
        self.status_label.config(text=text, fg=color)

    # ── Transcoding ───────────────────────────────────────────────────

    def _start_transcode(self):
        files = list(self.file_listbox.get(0, "end"))
        if not files:
            messagebox.showwarning("No files", "Add at least one video file.")
            return

        quality = self.quality_var.get()
        preset_info = QUALITY_PRESETS[quality]
        suffix = self.suffix_var.get().strip() or "_transcoded"

        self._cancel_flag = False
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress["maximum"] = len(files)
        self.progress["value"] = 0
        self._set_status("Transcoding…", "blue")

        self.transcode_thread = threading.Thread(
            target=self._transcode_worker,
            args=(files, preset_info, suffix),
            daemon=True,
        )
        self.transcode_thread.start()

    def _cancel_transcode(self):
        self._cancel_flag = True
        self._log("Cancelling after current file…\n")

    def _transcode_worker(self, files, preset_info, suffix):
        crf = preset_info["crf"]
        preset = preset_info["preset"]
        success = 0

        for idx, input_path in enumerate(files):
            if self._cancel_flag:
                self.after(0, self._log, "Cancelled.\n")
                break

            base, ext = os.path.splitext(input_path)
            output_path = f"{base}{suffix}.mp4"

            if os.path.exists(output_path):
                self.after(0, self._log, f"Skipping (output exists): {output_path}\n")
                self.after(0, self._advance_progress, idx + 1)
                success += 1
                continue

            # Build ffmpeg command
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-c:v", "libx264", "-preset", preset, "-crf", crf,
                "-c:a", "copy",
            ]

            if self.scale_var.get():
                width = self.scale_width_var.get().strip() or "960"
                cmd += ["-vf", f"scale={width}:-1"]

            cmd.append(output_path)

            self.after(0, self._log, f"[{idx+1}/{len(files)}] {os.path.basename(input_path)} → {os.path.basename(output_path)}\n")

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # Show size comparison
                    orig_mb = os.path.getsize(input_path) / (1024 * 1024)
                    new_mb = os.path.getsize(output_path) / (1024 * 1024)
                    reduction = (1 - new_mb / orig_mb) * 100 if orig_mb > 0 else 0
                    self.after(
                        0, self._log,
                        f"  Done: {orig_mb:.1f} MB → {new_mb:.1f} MB ({reduction:.0f}% reduction)\n",
                    )
                    success += 1
                else:
                    self.after(0, self._log, f"  FAILED: {result.stderr[:300]}\n")
            except Exception as exc:
                self.after(0, self._log, f"  ERROR: {exc}\n")

            self.after(0, self._advance_progress, idx + 1)

        self.after(0, self._transcode_done, success, len(files))

    def _advance_progress(self, value):
        self.progress["value"] = value

    def _transcode_done(self, success, total):
        self._set_status("Idle", "gray")
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self._log(f"\nFinished: {success}/{total} files transcoded.\n")


def main():
    app = TranscodeGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
