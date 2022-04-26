#!/usr/bin/env python3

import rumps
import sys


HOURS_UNIT = ["HOURS", "HOUR", "H"]
MINS_UNIT = ["MINS", "MIN", "M"]
SECONDS_UNIT = ["SECONDS", "SECOND", "S"]
APP_NAME = "SimpleTimer"
ICON_FILE = "icon.png"
PAUSE_TITLE = "Pause"
RESUME_TITLE = "Resume"


class TimerApp(object):
    def __init__(self, timer_seconds, title=""):
        self.count = 0
        self.timer_seconds = timer_seconds
        self.title = title
        self.app = rumps.App(APP_NAME, title=title,
                             icon=ICON_FILE, quit_button="Stop")
        self.timer = rumps.Timer(self.on_tick, 1)

        self.pause_resume_button = rumps.MenuItem(
            title=PAUSE_TITLE, callback=self.pause_and_resume)
        self.app.menu = [self.pause_resume_button]

    def on_tick(self, sender):
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

    def pause_and_resume(self, sender):
        if sender.title == PAUSE_TITLE:
            self.timer.stop()
            sender.title = RESUME_TITLE
        else:
            self.timer.start()
            sender.title = PAUSE_TITLE

    def stop(self):
        self.timer.stop()
        rumps.notification(
            title=APP_NAME, subtitle="Timer {} is over.".format(self.title), message="")
        rumps.quit_application(self.app)

    def run(self):
        self.timer.start()
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

    query = sys.argv[1]
    args = query.split(" ", maxsplit=1)
    timer_seconds = get_seconds(args[0])
    if len(args) == 1:
        if args[0][-1].isnumeric():
            timer_detail = args[0] + "s"
        else:
            timer_detail = args[0]
    else:
        timer_detail = args[1]

    if timer_seconds is None:
        rumps.notification(
            title=APP_NAME, subtitle="Unrecognized time: {}.".format(args[0]), message="")
        return

    rumps.notification(
        title=APP_NAME, subtitle="Timer {} starts.".format(timer_detail), message="")
    timer_app = TimerApp(timer_seconds, timer_detail)
    timer_app.run()


if __name__ == "__main__":
    main()
