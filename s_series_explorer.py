"""S-Series Explorer: a small offline file explorer for Windows and Linux."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, Y, Button, Entry, Frame, Label, Menu, Tk, filedialog, messagebox, simpledialog, ttk

__version__ = "1.0.1"


@dataclass(frozen=True)
class FileRow:
    """Display information for one filesystem entry."""

    name: str
    path: Path
    kind: str
    size: str
    modified: str


class SSeriesExplorer:
    """Tkinter based offline file explorer."""

    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title(f"S-Series Explorer {__version__}")
        self.root.geometry("1000x650")
        self.current_path = Path.home()
        self.clipboard_path: Path | None = None
        self.clipboard_mode: str | None = None
        self.show_hidden = False

        self._build_ui()
        self.open_path(self.current_path)

    def _build_ui(self) -> None:
        top = Frame(self.root, padx=8, pady=8)
        top.pack(fill=X)

        Button(top, text="Zurück", command=self.go_up).pack(side=LEFT, padx=(0, 4))
        Button(top, text="Home", command=lambda: self.open_path(Path.home())).pack(side=LEFT, padx=4)
        Button(top, text="Aktualisieren", command=self.refresh).pack(side=LEFT, padx=4)

        self.path_entry = Entry(top)
        self.path_entry.pack(side=LEFT, fill=X, expand=True, padx=8)
        self.path_entry.bind("<Return>", lambda _event: self.open_path(Path(self.path_entry.get())))
        Button(top, text="Öffnen", command=lambda: self.open_path(Path(self.path_entry.get()))).pack(side=LEFT)

        main = Frame(self.root)
        main.pack(fill=BOTH, expand=True, padx=8, pady=(0, 8))

        columns = ("name", "kind", "size", "modified")
        self.tree = ttk.Treeview(main, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Name", command=lambda: self.sort_by("name"))
        self.tree.heading("kind", text="Typ", command=lambda: self.sort_by("kind"))
        self.tree.heading("size", text="Größe", command=lambda: self.sort_by("size"))
        self.tree.heading("modified", text="Geändert", command=lambda: self.sort_by("modified"))
        self.tree.column("name", width=420, anchor="w")
        self.tree.column("kind", width=130, anchor="w")
        self.tree.column("size", width=110, anchor="e")
        self.tree.column("modified", width=170, anchor="w")
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(main, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda _event: self.open_selected())
        self.tree.bind("<Return>", lambda _event: self.open_selected())
        self.tree.bind("<Button-3>", self.show_context_menu)

        bottom = Frame(self.root, padx=8)
        bottom.pack(fill=X, pady=(0, 8))
        Button(bottom, text="Neuer Ordner", command=self.create_folder).pack(side=LEFT, padx=(0, 4))
        Button(bottom, text="Neue Datei", command=self.create_file).pack(side=LEFT, padx=4)
        Button(bottom, text="Kopieren", command=lambda: self.copy_or_cut("copy")).pack(side=LEFT, padx=4)
        Button(bottom, text="Ausschneiden", command=lambda: self.copy_or_cut("cut")).pack(side=LEFT, padx=4)
        Button(bottom, text="Einfügen", command=self.paste).pack(side=LEFT, padx=4)
        Button(bottom, text="Umbenennen", command=self.rename_selected).pack(side=LEFT, padx=4)
        Button(bottom, text="Löschen", command=self.delete_selected).pack(side=LEFT, padx=4)
        Button(bottom, text="Versteckte anzeigen", command=self.toggle_hidden).pack(side=LEFT, padx=4)
        self.status = Label(bottom, text="Bereit", anchor="w")
        self.status.pack(side=RIGHT, fill=X, expand=True)

        self.context_menu = Menu(self.root, tearoff=False)
        self.context_menu.add_command(label="Öffnen", command=self.open_selected)
        self.context_menu.add_command(label="Kopieren", command=lambda: self.copy_or_cut("copy"))
        self.context_menu.add_command(label="Ausschneiden", command=lambda: self.copy_or_cut("cut"))
        self.context_menu.add_command(label="Einfügen", command=self.paste)
        self.context_menu.add_command(label="Umbenennen", command=self.rename_selected)
        self.context_menu.add_command(label="Löschen", command=self.delete_selected)

    def open_path(self, path: Path) -> None:
        try:
            path = path.expanduser().resolve()
            if path.is_file():
                self.open_file(path)
                return
            if not path.is_dir():
                raise FileNotFoundError(f"Pfad nicht gefunden: {path}")
            self.current_path = path
            self.path_entry.delete(0, END)
            self.path_entry.insert(0, str(path))
            self.populate()
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))

    def populate(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = self._scan_directory(self.current_path)
        for file_row in rows:
            self.tree.insert("", END, values=(file_row.name, file_row.kind, file_row.size, file_row.modified), tags=(str(file_row.path),))
        self.status.config(text=f"{len(rows)} Einträge")

    def _scan_directory(self, path: Path) -> list[FileRow]:
        rows: list[FileRow] = []
        for entry in path.iterdir():
            if not self.show_hidden and entry.name.startswith("."):
                continue
            try:
                stat = entry.stat()
                kind = "Ordner" if entry.is_dir() else entry.suffix.lower().lstrip(".") or "Datei"
                size = "" if entry.is_dir() else self._format_size(stat.st_size)
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                rows.append(FileRow(entry.name, entry, kind, size, modified))
            except OSError:
                rows.append(FileRow(entry.name, entry, "Unzugänglich", "", ""))
        return sorted(rows, key=lambda item: (item.kind != "Ordner", item.name.lower()))

    def selected_path(self) -> Path | None:
        selection = self.tree.selection()
        if not selection:
            return None
        values = self.tree.item(selection[0], "tags")
        return Path(values[0]) if values else None

    def open_selected(self) -> None:
        path = self.selected_path()
        if path is not None:
            self.open_path(path)

    def open_file(self, path: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Datei öffnen", str(exc))

    def go_up(self) -> None:
        parent = self.current_path.parent
        if parent != self.current_path:
            self.open_path(parent)

    def refresh(self) -> None:
        self.open_path(self.current_path)

    def create_folder(self) -> None:
        name = simpledialog.askstring("Neuer Ordner", "Ordnername:")
        if name:
            self._safe_create(self.current_path / name, is_folder=True)

    def create_file(self) -> None:
        name = simpledialog.askstring("Neue Datei", "Dateiname:")
        if name:
            self._safe_create(self.current_path / name, is_folder=False)

    def _safe_create(self, path: Path, is_folder: bool) -> None:
        try:
            if path.exists():
                raise FileExistsError(f"Existiert bereits: {path.name}")
            if is_folder:
                path.mkdir()
            else:
                path.write_text("", encoding="utf-8")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Erstellen fehlgeschlagen", str(exc))

    def copy_or_cut(self, mode: str) -> None:
        path = self.selected_path()
        if path is None:
            messagebox.showinfo("Auswahl", "Bitte zuerst eine Datei oder einen Ordner auswählen.")
            return
        self.clipboard_path = path
        self.clipboard_mode = mode
        self.status.config(text=f"{'Kopiert' if mode == 'copy' else 'Ausgeschnitten'}: {path.name}")

    def paste(self) -> None:
        if self.clipboard_path is None or self.clipboard_mode is None:
            messagebox.showinfo("Zwischenablage", "Keine Datei im Programm kopiert oder ausgeschnitten.")
            return
        source = self.clipboard_path
        target = self.current_path / source.name
        try:
            if target.exists():
                target = self._unique_target(target)
            if self.clipboard_mode == "cut":
                shutil.move(str(source), str(target))
                self.clipboard_path = None
                self.clipboard_mode = None
            elif source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Einfügen fehlgeschlagen", str(exc))

    def rename_selected(self) -> None:
        path = self.selected_path()
        if path is None:
            return
        new_name = simpledialog.askstring("Umbenennen", "Neuer Name:", initialvalue=path.name)
        if new_name and new_name != path.name:
            try:
                path.rename(path.with_name(new_name))
                self.refresh()
            except Exception as exc:
                messagebox.showerror("Umbenennen fehlgeschlagen", str(exc))

    def delete_selected(self) -> None:
        path = self.selected_path()
        if path is None:
            return
        if not messagebox.askyesno("Löschen bestätigen", f"'{path.name}' wirklich löschen?"):
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Löschen fehlgeschlagen", str(exc))

    def toggle_hidden(self) -> None:
        self.show_hidden = not self.show_hidden
        self.refresh()

    def sort_by(self, column: str) -> None:
        rows = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        rows.sort(key=lambda value: value[0].lower())
        for index, (_value, item) in enumerate(rows):
            self.tree.move(item, "", index)

    def show_context_menu(self, event: object) -> None:
        pointer_event = event  # Tkinter event object with x_root/y_root attributes.
        self.context_menu.tk_popup(pointer_event.x_root, pointer_event.y_root)  # type: ignore[attr-defined]

    @staticmethod
    def _format_size(size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
            value /= 1024
        return f"{size} B"

    @staticmethod
    def _unique_target(path: Path) -> Path:
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        while True:
            candidate = parent / f"{stem} - Kopie {counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1


def main() -> None:
    root = Tk()
    SSeriesExplorer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
