from __future__ import annotations

import ctypes
import os
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from .compare import COMPARISON_MODES, MODE_RELATIVE_PATH, compare_records
from .csv_export import export_rows
from .models import ComparisonRow, FileRecord
from .scanner import scan_folder

__version__ = "0.3.1"

_COLUMNS = [
    ("status", "Vergleich", 115),
    ("type", "Objekt", 70),
    *[(f"seg{i}", f"Teil {i}", 105) for i in range(1, 13)],
    ("issue", "Ausgabe", 65),
    ("inwork", "InWork", 60),
    ("language", "Sprache", 65),
    ("country", "Land", 50),
    ("corel", "Corel-DES-Version", 205),
    ("ext", "Endung", 65),
    ("size", "Größe", 85),
    ("modified", "Geändert", 125),
    ("relative", "Relativer Pfad", 260),
    ("filename", "Originaldateiname", 380),
]

_STATUS_VALUES = (
    "Alle",
    "Identisch",
    "Geändert",
    "Nur Ordner A",
    "Nur Ordner B",
    "Gleicher Inhalt",
    "Ungültiger Name",
    "Corel DES",
)


class SSeriesExplorerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("S-Series Explorer")
        self.geometry("1550x820")
        self.minsize(1000, 650)

        self.folder_a = tk.StringVar()
        self.folder_b = tk.StringVar()
        self.recursive = tk.BooleanVar(value=True)
        self.compare_mode = tk.StringVar(value=MODE_RELATIVE_PATH)
        self.search_text = tk.StringVar()
        self.status_filter = tk.StringVar(value="Alle")
        self.progress_value = tk.IntVar(value=0)
        self.status_text = tk.StringVar(value="Bereit")
        self.action_mode = tk.StringVar(value="Explorer: Ordner anzeigen")
        self.current_folder = tk.StringVar(value=str(Path.home()))
        self._history: list[Path] = []
        self._history_index = -1
        self._clipboard_path: Path | None = None
        self._clipboard_cut = False

        self.records_a: list[FileRecord] = []
        self.records_b: list[FileRecord] = []
        self.all_rows: list[ComparisonRow] = []
        self.visible_rows: list[ComparisonRow] = []
        self.row_lookup: dict[str, ComparisonRow] = {}
        self._result_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self._navigation_lookup: dict[str, Path] = {}

        self._build_ui()
        self.after(100, self._poll_queue)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        toolbar = ttk.Frame(self, padding=8)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="Adresse / Ordner A").grid(row=0, column=0, sticky="w", padx=(0, 6))
        address_entry = ttk.Entry(toolbar, textvariable=self.folder_a)
        address_entry.grid(row=0, column=1, sticky="ew")
        address_entry.bind("<Return>", lambda _event: self.open_address())
        address_actions = ttk.Frame(toolbar)
        address_actions.grid(row=0, column=2, padx=6)
        ttk.Button(address_actions, text="Zurück", command=self.go_back).grid(row=0, column=0, padx=1)
        ttk.Button(address_actions, text="Vor", command=self.go_forward).grid(row=0, column=1, padx=1)
        ttk.Button(address_actions, text="Hoch", command=self.go_up).grid(row=0, column=2, padx=1)
        ttk.Button(address_actions, text="Öffnen", command=self.open_address).grid(row=0, column=3, padx=1)
        toolbar.bind_all("<Alt-Left>", lambda _event: self.go_back())
        toolbar.bind_all("<Alt-Right>", lambda _event: self.go_forward())
        toolbar.bind_all("<Alt-Up>", lambda _event: self.go_up())

        ttk.Label(toolbar, text="Ordner B").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(6, 0))
        ttk.Entry(toolbar, textvariable=self.folder_b).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        ttk.Button(toolbar, text="Durchsuchen…", command=lambda: self._choose_folder(self.folder_b)).grid(
            row=1, column=2, padx=6, pady=(6, 0)
        )

        actions = ttk.Frame(toolbar)
        actions.grid(row=0, column=3, rowspan=2, sticky="ns", padx=(8, 0))
        ttk.Label(actions, text="Funktion").grid(row=0, column=0, sticky="w", padx=2)
        ttk.Combobox(
            actions,
            textvariable=self.action_mode,
            values=("Explorer: Ordner anzeigen", "Vergleich: Ordner A gegen B"),
            state="readonly",
            width=28,
        ).grid(row=0, column=1, columnspan=2, padx=2, sticky="ew")
        ttk.Button(actions, text="Ausführen", command=self.run_selected_function).grid(row=1, column=0, padx=2, pady=(6, 0))
        ttk.Button(actions, text="CSV exportieren", command=self.export_csv).grid(row=1, column=1, padx=2, pady=(6, 0))
        ttk.Button(actions, text="Leeren", command=self.clear).grid(row=1, column=2, padx=2, pady=(6, 0))

        filters = ttk.Frame(self, padding=(8, 0, 8, 8))
        filters.grid(row=1, column=0, sticky="ew")
        filters.columnconfigure(5, weight=1)

        ttk.Checkbutton(filters, text="Unterordner", variable=self.recursive).grid(row=0, column=0, padx=(0, 12))
        ttk.Label(filters, text="Vergleich nach").grid(row=0, column=1, padx=(0, 5))
        ttk.Combobox(
            filters,
            textvariable=self.compare_mode,
            values=COMPARISON_MODES,
            state="readonly",
            width=24,
        ).grid(row=0, column=2, padx=(0, 14))
        ttk.Label(filters, text="Ansicht").grid(row=0, column=3, padx=(0, 5))
        status_combo = ttk.Combobox(
            filters,
            textvariable=self.status_filter,
            values=_STATUS_VALUES,
            state="readonly",
            width=18,
        )
        status_combo.grid(row=0, column=4, padx=(0, 14))
        status_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_filter())
        search = ttk.Entry(filters, textvariable=self.search_text)
        search.grid(row=0, column=5, sticky="ew")
        search.bind("<KeyRelease>", lambda _event: self.apply_filter())
        ttk.Label(filters, text="Suche über alle Spalten").grid(row=0, column=6, padx=(6, 0))

        main_pane = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main_pane.grid(row=2, column=0, sticky="nsew", padx=8)

        sidebar = ttk.Frame(main_pane)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(1, weight=1)
        main_pane.add(sidebar, weight=1)

        ttk.Label(sidebar, text="Dieser PC", font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.navigation_tree = ttk.Treeview(sidebar, show="tree", selectmode="browse")
        navigation_scroll = ttk.Scrollbar(sidebar, orient=tk.VERTICAL, command=self.navigation_tree.yview)
        self.navigation_tree.configure(yscrollcommand=navigation_scroll.set)
        self.navigation_tree.grid(row=1, column=0, sticky="nsew")
        navigation_scroll.grid(row=1, column=1, sticky="ns")
        self.navigation_tree.bind("<<TreeviewOpen>>", self._expand_navigation_item)
        self.navigation_tree.bind("<<TreeviewSelect>>", self._select_navigation_item)
        self.navigation_tree.bind("<Double-1>", lambda _event: self.scan_a())

        pane = ttk.Panedwindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(pane, weight=5)

        table_frame = ttk.Frame(pane)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        pane.add(table_frame, weight=5)

        column_ids = [column_id for column_id, _, _ in _COLUMNS]
        self.tree = ttk.Treeview(
            table_frame,
            columns=column_ids,
            show="headings",
            selectmode="browse",
        )
        for column_id, title, width in _COLUMNS:
            self.tree.heading(column_id, text=title, command=lambda c=column_id: self._sort_by(c, False))
            self.tree.column(column_id, width=width, minwidth=45, stretch=False, anchor="w")

        xscroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        yscroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("changed", background="#fff4d6")
        self.tree.tag_configure("only", background="#ffe3e3")
        self.tree.tag_configure("invalid", background="#ffd0d0")
        self.tree.tag_configure("same", background="#e6f4e6")
        self.tree.bind("<<TreeviewSelect>>", self._show_details)
        self.tree.bind("<Double-1>", lambda _event: self.open_selected())
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Delete>", lambda _event: self.delete_selected())
        self.tree.bind("<F2>", lambda _event: self.rename_selected())
        self.tree.bind("<Control-c>", lambda _event: self.copy_file_selected())
        self.tree.bind("<Control-x>", lambda _event: self.cut_file_selected())
        self.tree.bind("<Control-v>", lambda _event: self.paste_file())

        details_frame = ttk.LabelFrame(pane, text="Details", padding=6)
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        pane.add(details_frame, weight=1)
        self.details = tk.Text(details_frame, height=8, wrap="word", state="disabled")
        self.details.grid(row=0, column=0, sticky="nsew")

        statusbar = ttk.Frame(self, padding=8)
        statusbar.grid(row=3, column=0, sticky="ew")
        statusbar.columnconfigure(0, weight=1)
        ttk.Label(statusbar, textvariable=self.status_text).grid(row=0, column=0, sticky="w")
        ttk.Progressbar(statusbar, variable=self.progress_value, maximum=100, length=260).grid(row=0, column=1)

        self.context_menu = tk.Menu(self, tearoff=False)
        self.context_menu.add_command(label="Öffnen", command=self.open_selected)
        self.context_menu.add_command(label="Im Explorer anzeigen", command=self.reveal_selected)
        self.context_menu.add_command(label="Pfad kopieren", command=self.copy_selected_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kopieren", command=self.copy_file_selected)
        self.context_menu.add_command(label="Ausschneiden", command=self.cut_file_selected)
        self.context_menu.add_command(label="Einfügen", command=self.paste_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Neu: Ordner", command=self.create_folder)
        self.context_menu.add_command(label="Umbenennen", command=self.rename_selected)
        self.context_menu.add_command(label="Löschen", command=self.delete_selected)

        self._populate_navigation_roots()
        self.navigate_to(Path.home(), add_history=True)

    def _populate_navigation_roots(self) -> None:
        self.navigation_tree.delete(*self.navigation_tree.get_children())
        self._navigation_lookup.clear()
        for root in _navigation_roots():
            label = _navigation_label(root)
            item = self.navigation_tree.insert("", "end", text=label, open=False)
            self._navigation_lookup[item] = root
            self._add_navigation_placeholder(item, root)

    def _expand_navigation_item(self, _event=None) -> None:
        item = self.navigation_tree.focus()
        path = self._navigation_lookup.get(item)
        if path is not None:
            self._load_navigation_children(item, path)

    def _select_navigation_item(self, _event=None) -> None:
        item = self.navigation_tree.focus()
        path = self._navigation_lookup.get(item)
        if path is not None:
            self.navigate_to(path, add_history=True)

    def _load_navigation_children(self, item: str, path: Path) -> None:
        children = self.navigation_tree.get_children(item)
        if len(children) == 1 and self.navigation_tree.item(children[0], "text") == "Lädt…":
            self.navigation_tree.delete(children[0])
        else:
            return
        try:
            directories = sorted(
                (entry for entry in path.iterdir() if entry.is_dir()),
                key=lambda entry: entry.name.casefold(),
            )
        except (OSError, PermissionError):
            self.navigation_tree.insert(item, "end", text="Zugriff verweigert", values=("error",))
            return
        for directory in directories:
            child = self.navigation_tree.insert(item, "end", text=directory.name or str(directory), open=False)
            self._navigation_lookup[child] = directory
            self._add_navigation_placeholder(child, directory)

    def _add_navigation_placeholder(self, item: str, path: Path) -> None:
        try:
            has_child = any(entry.is_dir() for entry in path.iterdir())
        except (OSError, PermissionError):
            has_child = False
        if has_child:
            self.navigation_tree.insert(item, "end", text="Lädt…")

    def _choose_folder(self, variable: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=variable.get() or None)
        if selected:
            variable.set(selected)
            if variable is self.folder_a:
                self.navigate_to(Path(selected), add_history=True)
            else:
                self.current_folder.set(selected)

    def open_address(self) -> None:
        self.navigate_to(Path(self.folder_a.get()).expanduser(), add_history=True)

    def navigate_to(self, path: Path, *, add_history: bool) -> None:
        if not path.is_dir():
            messagebox.showerror("S-Series Explorer", f"Kein gültiger Ordner:\n{path}")
            return
        resolved = path.resolve()
        self.folder_a.set(str(resolved))
        self.current_folder.set(str(resolved))
        if add_history:
            del self._history[self._history_index + 1 :]
            self._history.append(resolved)
            self._history_index = len(self._history) - 1
        self.scan_a()

    def go_back(self) -> None:
        if self._history_index > 0:
            self._history_index -= 1
            self.navigate_to(self._history[self._history_index], add_history=False)

    def go_forward(self) -> None:
        if self._history_index + 1 < len(self._history):
            self._history_index += 1
            self.navigate_to(self._history[self._history_index], add_history=False)

    def go_up(self) -> None:
        path = Path(self.folder_a.get()).expanduser()
        if path.parent != path:
            self.navigate_to(path.parent, add_history=True)

    def run_selected_function(self) -> None:
        if self.action_mode.get().startswith("Vergleich"):
            self.compare_folders()
        else:
            self.scan_a()

    def scan_a(self) -> None:
        root = self._validated_folder(self.folder_a.get(), "Ordner A")
        if not root:
            return
        self._start_worker(
            "scan_a",
            lambda: scan_folder(
                root,
                recursive=self.recursive.get(),
                include_directories=True,
                progress=self._progress,
            ),
        )

    def compare_folders(self) -> None:
        root_a = self._validated_folder(self.folder_a.get(), "Ordner A")
        root_b = self._validated_folder(self.folder_b.get(), "Ordner B")
        if not root_a or not root_b:
            return

        def work() -> tuple[list[FileRecord], list[FileRecord], list[ComparisonRow]]:
            records_a = scan_folder(root_a, recursive=self.recursive.get(), progress=self._progress)
            records_b = scan_folder(root_b, recursive=self.recursive.get(), progress=self._progress)
            rows = compare_records(
                records_a,
                records_b,
                mode=self.compare_mode.get(),
                progress=self._progress,
            )
            return records_a, records_b, rows

        self._start_worker("compare", work)

    def _start_worker(self, operation: str, function) -> None:
        self.status_text.set("Arbeite…")
        self.progress_value.set(0)

        def runner() -> None:
            try:
                result = function()
                self._result_queue.put((operation, result))
            except Exception as exc:  # UI boundary: display a useful error
                self._result_queue.put(("error", exc))

        threading.Thread(target=runner, daemon=True).start()

    def _progress(self, value: int, filename: str) -> None:
        self._result_queue.put(("progress", (value, filename)))

    def _poll_queue(self) -> None:
        try:
            while True:
                operation, payload = self._result_queue.get_nowait()
                if operation == "progress":
                    value, filename = payload
                    self.progress_value.set(value)
                    self.status_text.set(f"{value}% – {filename}")
                elif operation == "scan_a":
                    self.records_a = payload
                    self.records_b = []
                    self.all_rows = [ComparisonRow(status="Ordner A", left=item) for item in self.records_a]
                    self.apply_filter()
                    self.current_folder.set(self.folder_a.get())
                    self.status_text.set(f"{len(self.records_a)} Elemente in {self.folder_a.get()}")
                    self.progress_value.set(100)
                elif operation == "compare":
                    self.records_a, self.records_b, self.all_rows = payload
                    self.apply_filter()
                    self.status_text.set(
                        f"{len(self.records_a)} Dateien in A, {len(self.records_b)} Dateien in B, "
                        f"{len(self.all_rows)} Vergleichszeilen"
                    )
                    self.progress_value.set(100)
                elif operation == "error":
                    self.progress_value.set(0)
                    self.status_text.set("Fehler")
                    messagebox.showerror("S-Series Explorer", str(payload))
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def apply_filter(self) -> None:
        query = self.search_text.get().casefold().strip()
        status_filter = self.status_filter.get()
        rows: list[ComparisonRow] = []

        for row in self.all_rows:
            record = row.record
            if status_filter != "Alle":
                if status_filter == "Ungültiger Name" and record.parsed.is_valid:
                    continue
                if status_filter == "Corel DES" and record.parsed.extension != "des":
                    continue
                if status_filter not in ("Ungültiger Name", "Corel DES") and row.status != status_filter:
                    continue
            values = self._row_values(row)
            if query and query not in " ".join(str(value).casefold() for value in values):
                continue
            rows.append(row)

        self.visible_rows = rows
        self._render_rows()

    def _render_rows(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.row_lookup.clear()
        for index, row in enumerate(self.visible_rows):
            item_id = f"row-{index}"
            self.row_lookup[item_id] = row
            self.tree.insert("", "end", iid=item_id, values=self._row_values(row), tags=self._tags(row))
        self.status_text.set(f"{len(self.visible_rows)} von {len(self.all_rows)} Zeilen angezeigt")

    def _row_values(self, row: ComparisonRow) -> tuple[object, ...]:
        record = row.record
        parsed = record.parsed
        status = row.status if parsed.is_valid else f"{row.status} / Name fehlerhaft"
        return (
            status,
            "Ordner" if record.path.is_dir() else parsed.object_type,
            *(parsed.segment(index) for index in range(12)),
            parsed.issue,
            parsed.in_work,
            parsed.language,
            parsed.country,
            record.corel.display,
            parsed.extension,
            "" if record.path.is_dir() else _human_size(record.size),
            record.modified_display,
            record.relative_path,
            record.filename,
        )

    def _tags(self, row: ComparisonRow) -> tuple[str, ...]:
        if not row.record.parsed.is_valid:
            return ("invalid",)
        if row.status in ("Identisch", "Gleicher Inhalt"):
            return ("same",)
        if row.status == "Geändert":
            return ("changed",)
        if row.status.startswith("Nur"):
            return ("only",)
        return ()

    def _show_details(self, _event=None) -> None:
        row = self._selected_row()
        if not row:
            return
        record = row.record
        parsed = record.parsed
        lines = [
            f"Datei: {record.path}",
            f"Vergleich: {row.status}",
            f"Vergleichsdetails: {row.details or '-'}",
            f"Dateiname gültig: {'Ja' if parsed.is_valid else 'Nein'}",
        ]
        if parsed.messages:
            lines.append("Hinweise: " + "; ".join(parsed.messages))
        if parsed.semantic_fields:
            lines.append("\nInterpretierte Felder:")
            lines.extend(f"  {name}: {value}" for name, value in parsed.semantic_fields.items())
        if record.corel.display:
            lines.append("\nCorel-DES-Analyse:")
            lines.append(f"  Ergebnis: {record.corel.display}")
            lines.append(f"  Sicherheit: {record.corel.confidence}")
            lines.extend(f"  {note}" for note in record.corel.notes)
        if row.left and row.right:
            lines.append(f"\nOrdner A: {row.left.path}")
            lines.append(f"Ordner B: {row.right.path}")

        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")

    def _selected_row(self) -> ComparisonRow | None:
        selected = self.tree.selection()
        return self.row_lookup.get(selected[0]) if selected else None

    def _show_context_menu(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def open_selected(self) -> None:
        row = self._selected_row()
        if row:
            path = row.record.path
            if path.is_dir():
                self.navigate_to(path, add_history=True)
            else:
                _open_path(path)

    def reveal_selected(self) -> None:
        row = self._selected_row()
        if not row:
            return
        path = row.record.path
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", str(path)])
        else:
            _open_path(path.parent)

    def copy_selected_path(self) -> None:
        row = self._selected_row()
        if row:
            self.clipboard_clear()
            self.clipboard_append(str(row.record.path))


    def create_folder(self) -> None:
        root = self._validated_folder(self.folder_a.get(), "aktueller Ordner")
        if not root:
            return
        name = simpledialog.askstring("Neuer Ordner", "Ordnername:", parent=self)
        if not name:
            return
        target = root / name
        try:
            target.mkdir()
        except OSError as exc:
            messagebox.showerror("S-Series Explorer", str(exc))
            return
        self.scan_a()

    def rename_selected(self) -> None:
        row = self._selected_row()
        if not row:
            return
        old_path = row.record.path
        new_name = simpledialog.askstring(
            "Umbenennen", "Neuer Name:", initialvalue=old_path.name, parent=self
        )
        if not new_name or new_name == old_path.name:
            return
        try:
            old_path.rename(old_path.with_name(new_name))
        except OSError as exc:
            messagebox.showerror("S-Series Explorer", str(exc))
            return
        self.scan_a()

    def delete_selected(self) -> None:
        row = self._selected_row()
        if not row:
            return
        path = row.record.path
        if not messagebox.askyesno("Löschen", f"{path.name} wirklich löschen?"):
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            messagebox.showerror("S-Series Explorer", str(exc))
            return
        self.scan_a()

    def copy_file_selected(self) -> None:
        row = self._selected_row()
        if row:
            self._clipboard_path = row.record.path
            self._clipboard_cut = False
            self.status_text.set(f"Kopiert: {self._clipboard_path}")

    def cut_file_selected(self) -> None:
        row = self._selected_row()
        if row:
            self._clipboard_path = row.record.path
            self._clipboard_cut = True
            self.status_text.set(f"Ausgeschnitten: {self._clipboard_path}")

    def paste_file(self) -> None:
        if self._clipboard_path is None:
            return
        root = self._validated_folder(self.folder_a.get(), "aktueller Ordner")
        if not root:
            return
        target = _unique_destination(root / self._clipboard_path.name)
        try:
            if self._clipboard_cut:
                shutil.move(str(self._clipboard_path), str(target))
                self._clipboard_path = None
                self._clipboard_cut = False
            elif self._clipboard_path.is_dir():
                shutil.copytree(self._clipboard_path, target)
            else:
                shutil.copy2(self._clipboard_path, target)
        except OSError as exc:
            messagebox.showerror("S-Series Explorer", str(exc))
            return
        self.scan_a()

    def export_csv(self) -> None:
        if not self.visible_rows:
            messagebox.showinfo("S-Series Explorer", "Keine sichtbaren Zeilen zum Exportieren.")
            return
        target = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="s-series-explorer.csv",
        )
        if target:
            export_rows(Path(target), self.visible_rows)
            self.status_text.set(f"CSV gespeichert: {target}")

    def clear(self) -> None:
        self.records_a.clear()
        self.records_b.clear()
        self.all_rows.clear()
        self.visible_rows.clear()
        self.tree.delete(*self.tree.get_children())
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.configure(state="disabled")
        self.progress_value.set(0)
        self.status_text.set("Bereit")

    def _validated_folder(self, value: str, label: str) -> Path | None:
        if not value:
            messagebox.showwarning("S-Series Explorer", f"Bitte {label} auswählen.")
            return None
        path = Path(value)
        if not path.is_dir():
            messagebox.showerror("S-Series Explorer", f"{label} ist kein gültiger Ordner:\n{path}")
            return None
        return path

    def _sort_by(self, column: str, descending: bool) -> None:
        children = list(self.tree.get_children(""))
        children.sort(key=lambda item: self.tree.set(item, column).casefold(), reverse=descending)
        for index, item in enumerate(children):
            self.tree.move(item, "", index)
        self.tree.heading(column, command=lambda: self._sort_by(column, not descending))


def _navigation_roots() -> list[Path]:
    if os.name == "nt":
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        return [Path(f"{chr(65 + index)}:/") for index in range(26) if bitmask & (1 << index)]
    return [Path("/")]


def _navigation_label(path: Path) -> str:
    if os.name == "nt" and path.drive:
        return f"Lokaler Datenträger ({path.drive})"
    return str(path)


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _open_path(path: Path) -> None:
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    elif os.uname().sysname == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def main() -> None:
    app = SSeriesExplorerApp()
    app.mainloop()


def _unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem} - Kopie {index}{suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Kein freier Zielname für {path}")
