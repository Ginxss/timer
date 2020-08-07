import sys
import time
import threading
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tk_font
import tkinter.filedialog as fd
from playsound import playsound


class NewTimerWindow(tk.Toplevel):
    def __init__(self, master=None):
        tk.Toplevel.__init__(self, master)
        self.title("Create New Timer")

        # Frames
        entry_frame = tk.Frame(self)
        entry_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        # Entry
        entry_info_font = tk_font.Font(family="Arial", size=12)
        entry_info_label = tk.Label(entry_frame, text="Format: <Name>:<minutes>:<seconds>", anchor="w", justify=tk.LEFT,
                                    font=entry_info_font)
        entry_info_label.pack(fill=tk.X)

        entry_font = tk_font.Font(family="Arial", size=11)
        self.entry = tk.Text(entry_frame, font=entry_font)
        self.entry.insert(tk.END, "Name of Interval 1: 1:30\n\nName of Interval 2: 0:5")
        self.entry.pack(fill=tk.BOTH, expand=True, pady=10)

        scrollbar = ttk.Scrollbar(self.entry, command=self.entry.yview)
        self.entry.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        cancel_button = tk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.RIGHT)

        save_button = tk.Button(button_frame, text="Save", command=self.save)
        save_button.pack(side=tk.RIGHT, ipadx=8, padx=10)

    def cancel(self):
        self.destroy()

    def save(self):
        data = [("Timer files", "*.tmr")]
        filename = fd.asksaveasfilename(filetype=data, defaultextension=data)
        if filename == "":
            return
        
        file = open(filename, "w", encoding="utf-8")
        file.write(self.entry.get("1.0", tk.END))
        file.close()
        self.destroy()


class TimerApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Variables
        self.intervals = []
        self.interval_index = 0
        if len(sys.argv) > 1:
            self.read_file(sys.argv[1])
        else:
            self.read_file("tmr/timer.tmr")

        self.minutes = 0
        self.seconds = 0
        self.loop = tk.BooleanVar()
        self.loop.set(False)
        self.time_text = tk.StringVar()
        self.interval_name = tk.StringVar()
        self.next_interval_name = tk.StringVar()

        self.set_interval(0)
        self.update_time()

        self.go_sound = "sounds/go.mp3"
        self.ready_sound = "sounds/ready.mp3"

        self.play_img = tk.PhotoImage(file="img/play.png")
        self.pause_img = tk.PhotoImage(file="img/pause.png")
        self.stop_img = tk.PhotoImage(file="img/stop.png")

        # Countdown Thread
        self.thread_running = True
        self.thread_paused = True
        self.duration = 0

        self.thread = threading.Thread(target=self.count_thread_function)
        self.thread.start()

        # UI
        self.create_ui()

    def create_ui(self):
        self.title("Timer")
        self.iconbitmap("img/icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.exit_handler)

        # Menu
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New Timer", command=self.new_timer)
        file_menu.add_command(label="Open Timer", command=self.open_timer)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=False)
        edit_menu.add_checkbutton(label="Loop", variable=self.loop)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Frames
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.TOP, padx=10, pady=10)

        time_frame = tk.Frame(self)
        time_frame.pack(side=tk.TOP, pady=10)

        # Buttons
        play_button = tk.Button(button_frame, image=self.play_img, command=self.play)
        play_button.pack(side=tk.LEFT, padx=20)

        pause_button = tk.Button(button_frame, image=self.pause_img, command=self.pause)
        pause_button.pack(side=tk.LEFT)

        stop_button = tk.Button(button_frame, image=self.stop_img, command=self.stop)
        stop_button.pack(side=tk.LEFT, padx=20)

        # Time Display
        text_font = tk_font.Font(family="Arial", size=20)
        interval_name_label = tk.Label(time_frame, textvariable=self.interval_name, font=text_font)
        interval_name_label.pack(side=tk.TOP)

        time_font = tk_font.Font(family="Arial", size=80)
        time_label = tk.Label(time_frame, textvariable=self.time_text, font=time_font)
        time_label.pack(side=tk.TOP)

        next_interval_label = tk.Label(time_frame, textvariable=self.next_interval_name, font=text_font)
        next_interval_label.pack(side=tk.TOP)

    def new_timer(self):
        NewTimerWindow(master=self)

    def open_timer(self):
        data = (("Timer files", "*.tmr"), ("All files", "*.*"))
        filename = fd.askopenfilename(initialdir=".", filetypes=data)
        self.read_file(filename)
        self.stop()

    def read_file(self, filename):
        if filename == "":
            return

        self.intervals.clear()

        file = open(filename, "r", encoding="utf-8")

        for line in file:
            if ":" in line:
                split_line = line.split(":")
                if len(split_line) > 2:
                    name = split_line[0]
                    minutes = int(split_line[1])
                    seconds = int(split_line[2])

                    self.intervals.append((name, minutes, seconds))

        file.close()

    def set_interval(self, new_index):
        self.interval_index = new_index % len(self.intervals)
        next_index = (new_index + 1) % len(self.intervals)

        self.minutes = self.intervals[self.interval_index][1]
        self.seconds = self.intervals[self.interval_index][2]
        self.interval_name.set(self.intervals[self.interval_index][0] + ":")
        self.next_interval_name.set("Next: " + self.intervals[next_index][0])

    def update_time(self):
        self.time_text.set(f"{self.minutes:02d}:{self.seconds:02d}")

    def play(self):
        self.thread_paused = False

    def pause(self):
        self.thread_paused = True

    def stop(self):
        self.thread_paused = True
        time.sleep(0.01)
        self.duration = 0
        self.set_interval(0)
        self.update_time()

    def count_thread_function(self):
        while self.thread_running:
            while self.thread_paused and self.thread_running:
                time.sleep(0.01)

            start = time.time()
            while not self.thread_paused and self.thread_running:
                time.sleep(0.01)
                end = time.time()
                self.duration += end - start
                start = time.time()

                if self.duration > 1:
                    self.duration -= 1

                    self.seconds -= 1

                    if self.minutes == 0 and 0 < self.seconds < 4:
                        threading.Thread(target=playsound, args=(self.ready_sound,)).start()
                    elif self.minutes == 0 and self.seconds == 0:
                        threading.Thread(target=playsound, args=(self.go_sound,)).start()

                        new_index = self.interval_index + 1
                        if not self.loop.get() and new_index >= len(self.intervals):
                            self.thread_paused = True

                        self.set_interval(new_index)
                    elif self.seconds < 0:
                        self.minutes -= 1
                        self.seconds = 59

                    self.update_time()

    def exit_handler(self):
        self.thread_running = False
        self.thread.join()
        self.destroy()


if __name__ == "__main__":
    app = TimerApp()
    app.mainloop()
