#!/usr/bin/env python3

# Woof-KLayoutManager
# Extension for Puppy Linux's JWM desktop environment for switching between different keyboard layouts

# (C) Demian Volkov 2020

import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showinfo
from tkinter.colorchooser import askcolor
import _tkinter
import subprocess
import itertools
import random

from tkfontchooser import askfont
from PIL import Image, ImageTk, ImageColor

import keyboard


_KLAYOUTS = ("us", "ru", "ua", "cz qwerty")
KLAYOUTS = itertools.cycle(_KLAYOUTS)

BG = "#444444"
FG = "black"
FONT = "Arial 14 bold"


# TODO: make a klayout a separate class instead of a string

def _get_klayout_lang(klayout):
    return klayout.split()[0]


def _get_klayout_type(klayout):
    try:
        lang, type_ = klayout.split()
    except ValueError:
        raise ValueError("this keyboard doesn't have a type specified")
    else:
        return type_


def fontactual2str(actual):
    # TODO: rewrite in a clearer way
    return " ".join((f"{actual['family'] if not len(actual['family'].split()) > 1 else '{' + actual['family'] + '}'} "
                     f"{actual['size']} {actual['weight']} {actual['slant']} {'underline' if actual['underline'] else ''} "
                     f"{'overstrike' if actual['overstrike'] else ''}").split())


# raise ArithmeticError

class FrameWithPadding(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.inner_frame = tk.Frame(self)
        self.inner_frame.pack(padx=10, pady=10, fill="both", expand="yes")


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
    def __init__(self, master, ok_command, cancel_command, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.ok_btn = ttk.Button(self, text="OK", command=ok_command)
        self.cancel_btn = ttk.Button(self, text="Cancel", command=cancel_command)

        self.cancel_btn.pack(side="right", padx=4)
        self.ok_btn.pack(side="right", padx=4)


class SettingsGUI(tk.Toplevel):
    def __init__(self):
        super().__init__()

        self.is_updated = False

        self.new_settings = {"run_on_os_startup": tk.BooleanVar(self, False),

                             "layouts_list": [],

                             "background_color": tk.StringVar(self, "#444444"),
                             "foreground_color": tk.StringVar(self, "#000000"),
                             "font_settings": tk.StringVar(self, "Arial 14 bold"),
                             "default_position": tk.StringVar(self, "last saved")}

        self.title("Settings - Woof-KLayoutManager")
        self.resizable(False, False)

        self.tabs_nb = ttk.Notebook(self)
        self.tabs_nb.pack(fill="both", expand="yes")

        self.general_tab = FrameWithPadding(self.tabs_nb)
        self.tabs_nb.add(self.general_tab, text="General")
        self.general_tab = self.general_tab.inner_frame
        tk.Checkbutton(self.general_tab, text="Automatically run on OS startup",
                       variable=self.new_settings["run_on_os_startup"]).pack()

        self.klayouts_tab = FrameWithPadding(self.tabs_nb)
        self.tabs_nb.add(self.klayouts_tab, text="Keyboard Layouts")
        self.klayouts_tab = self.klayouts_tab.inner_frame
        # TODO: add scrollbar
        self.klayouts_tview = ttk.Treeview(self.klayouts_tab, columns=("layout", "variant"), show="headings")
        self.klayouts_tview.heading("layout", text="Layout")
        self.klayouts_tview.heading("variant", text="Variant")
        self.klayouts_tview.pack()
        self.klayouts_controls = tk.Frame(self.klayouts_tab)
        tk.Button(self.klayouts_controls, text="➕ Add").pack(side="left", fill="x", expand="yes")
        tk.Button(self.klayouts_controls, text="✎ Modify").pack(side="left", fill="x", expand="yes")
        tk.Button(self.klayouts_controls, text="➖ Remove").pack(side="left", fill="x", expand="yes")
        self.klayouts_controls.pack(fill="x")

        self.appearance_tab = FrameWithPadding(self.tabs_nb)
        self.tabs_nb.add(self.appearance_tab, text="Appearance")
        self.appearance_tab = self.appearance_tab.inner_frame
        self.bg_color_btn = ttk.Button(self.appearance_tab, compound="left", text="Background Color",
                                       command=self.set_bg_color)
        self.bg_color_btn.pack()
        self.fg_color_btn = ttk.Button(self.appearance_tab, compound="left", text="Text (Foreground) Color",
                                       command=self.set_fg_color)
        self.fg_color_btn.pack()
        self.font_btn = ttk.Button(self.appearance_tab, text="Font Settings", command=self.set_font_settings)
        self.font_btn.pack()

        self.__update_btn_color_img(self.bg_color_btn, self.new_settings["background_color"].get())
        self.__update_btn_color_img(self.fg_color_btn, self.new_settings["foreground_color"].get())

        self.okcancel_box = OKCancelBox(self, self.ok, self.destroy)
        self.okcancel_box.pack(fill="y", padx=10, pady=10, anchor="e")

        self.focus_force()

        self.wait_window()

    def ok(self):
        self.is_updated = True
        for option in self.new_settings:
            if hasattr(self.new_settings[option], "get"):
                self.new_settings[option] = self.new_settings[option].get()
        self.destroy()

    def set_bg_color(self):
        self.__update_color_setting("background_color")
        self.__update_btn_color_img(self.bg_color_btn, self.new_settings["background_color"].get())

    def set_fg_color(self):
        self.__update_color_setting("foreground_color")
        self.__update_btn_color_img(self.fg_color_btn, self.new_settings["foreground_color"].get())

    def set_font_settings(self):
        new_font = askfont(self, _get_klayout_lang(random.choice(_KLAYOUTS)))
        if new_font:
            self.new_settings["font_settings"].set(fontactual2str(new_font))

    def __update_color_setting(self, option):
        new_color = askcolor()
        if new_color != (None, None):
            self.new_settings[option].set(new_color[1])

    @staticmethod
    def __update_btn_color_img(btn, color):
        btn.__color_img = ImageTk.PhotoImage(Image.new("RGB", (16, 16), ImageColor.getrgb(color)))
        btn.configure(image=btn.__color_img)


class MainGUI(DraggableToolbar):
    def __init__(self):
        super().__init__()

        self.config(bg=BG)

        keyboard.add_hotkey('alt+shift', self.switch_layout)

        self.lang_label = tk.Label(self, bg=BG, fg=FG, font=FONT)
        self.lang_label.place(relx=0.5, rely=0.5, anchor="c")

        self.overrideredirect(True)

        self.geometry("25x30")
        self.update()
        self.geometry(
            "+%s+%s" % (self.winfo_screenwidth() - self.winfo_width(), self.winfo_screenheight() - self.winfo_height()))
        self.update()

        self.after(0, self.switch_layout)  # switch to the default keyboard layout
        self.after(0, self.make_topmost)

        self.right_click_menu = tk.Menu(self, tearoff=False)
        self.right_click_menu.add_command(label="Settings...", command=self.open_settings)
        self.right_click_menu.add_command(label="About...", command=lambda: showinfo("About...",
                                                                                               ("Woof-KLayoutManager\n"
                                                                                                "(C) Demian Volkov 2020\n\n"
                                                                                                "Extension for Puppy Linux's JWM desktop environment for switching between different keyboard layouts.\n\n"
                                                                                                "Thank you for using my program!")))
        self.right_click_menu.add_command(label="Exit...", command=self.destroy)
        self.bind("<Button-3>", self.show_right_click_menu)

    def switch_layout(self, lang=None):
        if not lang:
            lang = next(KLAYOUTS)
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
        if SettingsGUI().is_updated:
            self.restart()


if __name__ == "__main__":
    SettingsGUI()
    MainGUI().mainloop()
