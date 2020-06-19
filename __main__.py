#!/usr/bin/env python3

# Woof-KLayoutManager
# Extension for Puppy Linux's JWM desktop environment for switching between different keyboard layouts

# (C) Demian Volkov 2020

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as tk_msgbox
import _tkinter
import subprocess
import itertools

import keyboard


LANGS = itertools.cycle(("us", "ru", "ua", "cz qwerty"))

BG = "grey"
FG = "black"
FONT = "Arial 18"


class DraggableToolbar(tk.Tk):
    def __init__(self):
        super().__init__()

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self.config(cursor="fleur")
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.config(cursor="")
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        bottom_point = self.winfo_screenheight() - self.winfo_height()
        if y <= bottom_point:
            self.geometry(f"+{x}+{y}")
        else:
            self.geometry(f"+{x}+{bottom_point}")


class OKCancelBox(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ok_btn = ttk.Button(self, text="OK", command=self.master.destroy)
        self.cancel_btn = ttk.Button(self, text="Cancel", command=self.master.destroy)

        self.cancel_btn.pack(side="right", padx=4)
        self.ok_btn.pack(side="right", padx=4)


class SettingsGUI(tk.Toplevel):
    def __init__(self):
        super().__init__()

        self.title("Settings - Woof-KLayoutManager")
        self.resizable(False, False)

        self.tabs_nb = ttk.Notebook(self)
        self.tabs_nb.pack(fill="both", expand="yes")

        self.general_tab = tk.Frame(self.tabs_nb)
        self.klayouts_tab = tk.Frame(self.tabs_nb)
        self.appearance_tab = tk.Frame(self.tabs_nb)

        self.tabs_nb.add(self.general_tab, text="General")
        self.tabs_nb.add(self.klayouts_tab, text="Keyboard Layouts")
        self.tabs_nb.add(self.appearance_tab, text="Appearance")

        self.okcancel_box = OKCancelBox(self)
        self.okcancel_box.pack(fill="y", padx=10, pady=10, anchor="e")

        self.wait_window()


class MainGUI(DraggableToolbar):
    def __init__(self):
        super().__init__()

        self.config(bg=BG)

        keyboard.add_hotkey('alt+shift', self.switch_layout)

        self.lang_label = tk.Label(self, bg=BG, fg=FG, font=FONT)
        self.lang_label.pack()

        self.overrideredirect(True)

        self.geometry("25x35")
        self.update()
        self.geometry(
            "+%s+%s" % (self.winfo_screenwidth() - self.winfo_width(), self.winfo_screenheight() - self.winfo_height()))
        self.update()

        self.after(0, self.switch_layout)  # switch to the default keyboard layout
        self.after(0, self.make_topmost)

        self.right_click_menu = tk.Menu(self, tearoff=False)
        self.right_click_menu.add_command(label="Settings...", command=self.open_settings)
        self.right_click_menu.add_command(label="About...", command=lambda: tk_msgbox.showinfo("About...",
                                                                                               ("Woof-KLayoutManager\n"
                                                                                                "(C) Demian Volkov 2020\n\n"
                                                                                                "Extension for Puppy Linux's JWM desktop environment for switching between different keyboard layouts.\n\n"
                                                                                                "Thank you for using my program!")))
        self.right_click_menu.add_command(label="Exit...", command=self.destroy)
        self.bind("<Button-3>", self.show_right_click_menu)

    def switch_layout(self, lang=None):
        if not lang:
            lang = next(LANGS)
        try:
            subprocess.check_call(" ".join(("setxkbmap", lang)), shell=True)
        except Exception as details:
            # Show the popup menu with the error
            def skip_countdown(secs):
                if not secs:
                    menu.destroy()
                else:
                    try:
                        menu.entryconfig(3, label="Skip? (automatically in %s seconds)" % secs)
                    except _tkinter.TclError:
                        pass
                    else:
                        self.after(1000, lambda secs=secs - 1: skip_countdown(secs))

            menu = tk.Menu(self, tearoff=False)
            menu.add_command(label="While switching keyboard layout to \"%s\", an error occurred:" % lang,
                             state="disabled")
            menu.add_command(label="Details: %s (%s)" % (details.__class__.__name__, details), state="disabled")
            menu.add_command(label="Retry?", command=lambda lang=lang: self.switch_layout(lang))
            menu.add_command(label="Skip? (automatically in 10 seconds)", command=menu.destroy)
            menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() - 50, 0)
            self.after(0, lambda: skip_countdown(10))
        else:
            self.lang_label.config(text=lang.split()[0])

    def make_topmost(self):
        self.attributes("-topmost", True)
        self.after(100, self.make_topmost)

    def show_right_click_menu(self, event):
        try:
            self.right_click_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.right_click_menu.grab_release()

    def restart(self):
        print("restarting")

    def open_settings(self):
        SettingsGUI()
        self.restart()


if __name__ == "__main__":
    MainGUI().mainloop()
