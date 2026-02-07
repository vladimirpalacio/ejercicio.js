#!/usr/bin/env python3
"""
Interfaz grafica para descargar anuncios con Meta Ad Library API.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from queue import Empty, Queue
from tkinter import filedialog, messagebox, scrolledtext, ttk


class AdsGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Descarga de anuncios Meta")
        self.geometry("860x720")
        self.resizable(True, True)

        self.queue = Queue()
        self.process = None
        self.running = False

        self.token_var = tk.StringVar()
        self.show_token_var = tk.BooleanVar(value=False)
        self.page_id_var = tk.StringVar(value="636758826348325")
        self.page_name_var = tk.StringVar(value="Hawkers Co.")
        self.countries_var = tk.StringVar(value="ES")
        self.ad_status_var = tk.StringVar(value="ACTIVE")
        self.ad_type_var = tk.StringVar(value="ALL")
        self.limit_var = tk.StringVar(value="50")
        self.max_ads_var = tk.StringVar(value="50")
        self.api_version_var = tk.StringVar(value="v24.0")
        self.download_media_var = tk.BooleanVar(value=False)
        self.keep_snapshot_token_var = tk.BooleanVar(value=False)
        self.allow_gif_var = tk.BooleanVar(value=False)
        self.media_dir_var = tk.StringVar()
        self.min_bytes_var = tk.StringVar(value="10240")
        self.output_dir_var = tk.StringVar(value=os.getcwd())

        self._build_ui()
        self.after(200, self._poll_queue)

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            frame, text="Meta Ad Library - Descargador", font=("Arial", 16, "bold")
        )
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        row = 1
        ttk.Label(frame, text="Access token").grid(row=row, column=0, sticky="w")
        self.token_entry = ttk.Entry(
            frame, textvariable=self.token_var, show="*", width=60
        )
        self.token_entry.grid(row=row, column=1, columnspan=2, sticky="we", padx=(0, 8))
        ttk.Checkbutton(
            frame, text="Mostrar", variable=self.show_token_var, command=self._toggle_token
        ).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(frame, text="Page ID").grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.page_id_var, width=30).grid(
            row=row, column=1, sticky="we", padx=(0, 8)
        )
        ttk.Label(frame, text="Page name").grid(row=row, column=2, sticky="w")
        ttk.Entry(frame, textvariable=self.page_name_var, width=30).grid(
            row=row, column=3, sticky="we"
        )

        row += 1
        ttk.Label(frame, text="Countries (ISO)").grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.countries_var, width=20).grid(
            row=row, column=1, sticky="we", padx=(0, 8)
        )
        ttk.Label(frame, text="API version").grid(row=row, column=2, sticky="w")
        ttk.Entry(frame, textvariable=self.api_version_var, width=12).grid(
            row=row, column=3, sticky="w"
        )

        row += 1
        ttk.Label(frame, text="Ad status").grid(row=row, column=0, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.ad_status_var,
            values=["ALL", "ACTIVE", "INACTIVE"],
            state="readonly",
            width=12,
        ).grid(row=row, column=1, sticky="w", padx=(0, 8))
        ttk.Label(frame, text="Ad type").grid(row=row, column=2, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.ad_type_var,
            values=["ALL", "POLITICAL_AND_ISSUE_ADS"],
            state="readonly",
            width=26,
        ).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(frame, text="Limit").grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.limit_var, width=10).grid(
            row=row, column=1, sticky="w", padx=(0, 8)
        )
        ttk.Label(frame, text="Max ads").grid(row=row, column=2, sticky="w")
        ttk.Entry(frame, textvariable=self.max_ads_var, width=10).grid(
            row=row, column=3, sticky="w"
        )

        row += 1
        ttk.Checkbutton(
            frame,
            text="Descargar media (imagenes/videos)",
            variable=self.download_media_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(
            frame,
            text="Mantener token en URLs (no recomendado)",
            variable=self.keep_snapshot_token_var,
        ).grid(row=row, column=2, columnspan=2, sticky="w")
        row += 1
        ttk.Checkbutton(
            frame,
            text="Permitir GIF (puede traer pixeles)",
            variable=self.allow_gif_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, text="Min bytes").grid(row=row, column=2, sticky="w")
        ttk.Entry(frame, textvariable=self.min_bytes_var, width=10).grid(
            row=row, column=3, sticky="w"
        )

        row += 1
        ttk.Label(frame, text="Media dir (opcional)").grid(
            row=row, column=0, sticky="w"
        )
        ttk.Entry(frame, textvariable=self.media_dir_var, width=40).grid(
            row=row, column=1, columnspan=3, sticky="we"
        )

        row += 1
        ttk.Label(frame, text="Output dir").grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.output_dir_var, width=60).grid(
            row=row, column=1, columnspan=2, sticky="we", padx=(0, 8)
        )
        ttk.Button(frame, text="Buscar", command=self._browse_output).grid(
            row=row, column=3, sticky="w"
        )

        row += 1
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=(8, 8))
        self.start_button = ttk.Button(
            button_frame, text="Descargar anuncios", command=self._start_download
        )
        self.start_button.pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Abrir carpeta", command=self._open_output).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(button_frame, text="Limpiar log", command=self._clear_log).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        row += 1
        ttk.Label(frame, text="Log").grid(row=row, column=0, sticky="w")
        row += 1
        self.log_text = scrolledtext.ScrolledText(frame, height=18, wrap=tk.WORD)
        self.log_text.grid(row=row, column=0, columnspan=4, sticky="nsew")

        for col in range(4):
            frame.columnconfigure(col, weight=1)
        frame.rowconfigure(row, weight=1)

    def _toggle_token(self):
        self.token_entry.configure(show="" if self.show_token_var.get() else "*")

    def _browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir_var.set(path)

    def _open_output(self):
        path = self.output_dir_var.get().strip() or os.getcwd()
        if not os.path.isdir(path):
            messagebox.showerror("Error", "La carpeta de salida no existe.")
            return
        try:
            if sys.platform.startswith("darwin"):
                subprocess.Popen(["open", path])
            elif os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {exc}")

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def _validate_inputs(self):
        if not self.page_id_var.get().strip():
            messagebox.showerror("Error", "Page ID es obligatorio.")
            return False
        if not self.countries_var.get().strip():
            messagebox.showerror("Error", "Countries es obligatorio.")
            return False
        for label, var in [
            ("Limit", self.limit_var),
            ("Max ads", self.max_ads_var),
            ("Min bytes", self.min_bytes_var),
        ]:
            if var.get().strip():
                try:
                    int(var.get().strip())
                except ValueError:
                    messagebox.showerror("Error", f"{label} debe ser un numero.")
                    return False
        return True

    def _start_download(self):
        if self.running:
            return
        if not self._validate_inputs():
            return

        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "descargar_anuncios_meta.py"
        )
        if not os.path.exists(script_path):
            messagebox.showerror(
                "Error", "No se encontro descargar_anuncios_meta.py en esta carpeta."
            )
            return

        cmd = [
            sys.executable,
            script_path,
            "--page-id",
            self.page_id_var.get().strip(),
            "--page-name",
            self.page_name_var.get().strip() or "pagina",
            "--countries",
            self.countries_var.get().strip(),
            "--ad-status",
            self.ad_status_var.get(),
            "--ad-type",
            self.ad_type_var.get(),
            "--limit",
            self.limit_var.get().strip(),
            "--max-ads",
            self.max_ads_var.get().strip(),
            "--api-version",
            self.api_version_var.get().strip() or "v24.0",
        ]

        if self.download_media_var.get():
            cmd.append("--download-media")
            if self.media_dir_var.get().strip():
                cmd.extend(["--media-dir", self.media_dir_var.get().strip()])
            cmd.extend(["--min-bytes", self.min_bytes_var.get().strip()])
        if self.keep_snapshot_token_var.get():
            cmd.append("--keep-snapshot-token")
        if self.allow_gif_var.get():
            cmd.append("--allow-gif")

        output_dir = self.output_dir_var.get().strip() or os.getcwd()
        if not os.path.isdir(output_dir):
            messagebox.showerror("Error", "La carpeta de salida no existe.")
            return

        env = os.environ.copy()
        token = self.token_var.get().strip()
        if token:
            env["META_ACCESS_TOKEN"] = token

        self._append_log("Iniciando descarga...\n")
        self.running = True
        self.start_button.configure(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._run_process, args=(cmd, env, output_dir), daemon=True
        )
        thread.start()

    def _run_process(self, cmd, env, output_dir):
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                cwd=output_dir,
            )
            if self.process.stdout:
                for line in self.process.stdout:
                    self.queue.put(line.rstrip())
            code = self.process.wait()
            self.queue.put(f"\nProceso finalizado con codigo {code}.")
        except Exception as exc:
            self.queue.put(f"Error ejecutando el proceso: {exc}")
        finally:
            self.queue.put("__DONE__")

    def _append_log(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def _poll_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg == "__DONE__":
                    self.running = False
                    self.start_button.configure(state=tk.NORMAL)
                else:
                    self._append_log(msg + "\n")
        except Empty:
            pass
        self.after(200, self._poll_queue)


def main():
    app = AdsGui()
    app.mainloop()


if __name__ == "__main__":
    main()
