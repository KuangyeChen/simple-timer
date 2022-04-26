#!/usr/bin/env python3

import os
import rumps
import psutil
import sys
import socket
import time
import threading


HOURS_UNIT = ["HOURS", "HOUR", "H"]
MINS_UNIT = ["MINS", "MIN", "M"]
SECONDS_UNIT = ["SECONDS", "SECOND", "S"]
APP_NAME = "SimpleTimer"
ICON_FILE = "icon.png"
PAUSE_TITLE = "Pause"
RESUME_TITLE = "Resume"
LOCAL_HOST = "127.0.0.1"


class TimerApp(object):
    def __init__(self, timer_seconds, title=""):
        self.count = 0
        self.timer_seconds = timer_seconds
        self.title = title
        self.app = rumps.App(APP_NAME, title=title,
                             icon=ICON_FILE, quit_button="Stop")
        self.pause_resume_button = rumps.MenuItem(
            title=PAUSE_TITLE, callback=self.pause_and_resume)
        self.app.menu = [self.pause_resume_button]
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.2)
        self.command_thread = threading.Thread(target=self.listen_to_command)
        self.paused = True
        self.stopped = True
        self.stop_thread = threading.Thread(target=self.stop_loop)
        self.tick_thread = threading.Thread(target=self.on_tick)

    def stop_loop(self):
        while not self.stopped:
            time.sleep(0.2)

        self.command_thread.join(timeout=1)
        self.tick_thread.join(timeout=1)
        self.socket.close()
        rumps.notification(
            title=APP_NAME, subtitle="Timer {} is over.".format(self.title), message="")
        rumps.quit_application(self.app)

    def listen_to_command(self):
        while not self.stopped:
            try:
                conn, _ = self.socket.accept()
                command = conn.recv(32).decode()
                if not command.upper().endswith("#END"):
                    continue

                command = command[:-4]
                if command.upper() == "PAUSE":
                    if self.pause():
                        rumps.notification(
                            title=APP_NAME, subtitle="Timer {} is paused.".format(self.title), message="")
                elif command.upper() == "RESUME":
                    if self.resume():
                        rumps.notification(
                            title=APP_NAME, subtitle="Timer {} is resumed.".format(self.title), message="")
                elif command.upper() == "STOP":
                    self.stop()
                else:
                    print(f"Unrecognized command {command}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Connection error: {e}")

    def on_tick(self):
        while not self.stopped:
            if self.paused:
                time.sleep(1)
                continue
            time_left = self.timer_seconds - self.count
            if time_left <= 0:
                self.stop()
                return

            hours = time_left // 3600
            mins = (time_left % 3600) // 60
            secs = time_left % 60

            title_str = "" if self.title == "" else self.title + " "
            if hours > 0:
                self.app.title = "{}{:2d}:{:2d}:{:02d}".format(
                    title_str, hours, mins, secs)
            else:
                self.app.title = "{}{:2d}:{:02d}".format(title_str, mins, secs)
            self.count += 1
            time.sleep(1)

    def pause(self):
        print("pause")
        if self.paused:
            return False
        self.paused = True
        self.pause_resume_button.title = RESUME_TITLE
        return True

    def resume(self):
        print("resume")
        if not self.paused:
            return False
        print("start")
        self.paused = False
        self.pause_resume_button.title = PAUSE_TITLE
        return True

    def pause_and_resume(self, sender):
        if sender.title == PAUSE_TITLE:
            self.pause()
        else:
            self.resume()

    def stop(self):
        self.stopped = True

    def run(self):
        self.stopped = False
        self.paused = False
        try:
            self.socket.bind((LOCAL_HOST, 0))
            self.socket.listen()
            self.command_thread.start()
        except Exception as e:
            print(f"Start socket listen error: {e}")
            return

        self.tick_thread.start()
        self.stop_thread.start()
        self.app.run()


def get_seconds(time_str):
    number_str = time_str
    unit_str = None
    upper_time_str = time_str.upper()
    for unit in HOURS_UNIT + MINS_UNIT + SECONDS_UNIT:
        if upper_time_str.endswith(unit):
            unit_str = unit
            number_str = upper_time_str[:-len(unit)]
            break

    try:
        number = float(number_str)
    except ValueError:
        return None

    if unit_str in HOURS_UNIT:
        return int(number * 3600)
    if unit_str in MINS_UNIT:
        return int(number * 60)
    return int(number)


@rumps.notifications
def notification_center(info):
    print(info)


def main():
    if len(sys.argv) < 2:
        return

    # Check if there is a timer running
    self_pid = os.getpid()
    self_p = psutil.Process(self_pid)
    running_p = None
    for p in psutil.process_iter(["pid", "exe", "connections"]):
        if p.info["pid"] != self_pid and p.info["exe"] == self_p.exe():
            running_p = p
            break

    # Parse args
    query = sys.argv[1].strip()
    args = query.split(" ", maxsplit=1)
    timer_seconds = get_seconds(args[0])
    if len(args) == 1:
        if timer_seconds is not None and args[0][-1].isnumeric():
            timer_detail = args[0] + "s"
        else:
            timer_detail = args[0]
    else:
        timer_detail = args[1]

    if running_p is None:
        if query.upper() in ["PAUSE", "RESUME"]:
            rumps.notification(
                title=APP_NAME, subtitle="No running timer.", message="")
            return
        if timer_seconds is None:
            rumps.notification(
                title=APP_NAME, subtitle="Unrecognized time: {}.".format(args[0]), message="")
            return

        rumps.notification(
            title=APP_NAME, subtitle="Timer {} starts.".format(timer_detail), message="")
        timer_app = TimerApp(timer_seconds, timer_detail)
        timer_app.run()
    else:
        if timer_seconds is not None:
            rumps.notification(
                title=APP_NAME, subtitle="A timer is already running.", message="")
            return
        if query.upper() not in ["PAUSE", "RESUME", "STOP"]:
            rumps.notification(
                title=APP_NAME, subtitle="Unrecognized command: {}.".format(query), message="")
            return

        addr = running_p.info["connections"][0].laddr
        s = socket.socket()
        s.connect((addr.ip, addr.port))
        s.send(f"{query}#END".upper().encode())


if __name__ == "__main__":
    main()
