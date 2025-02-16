# Diablo 2 Resurrected Loader

This is a simple Qt app which manages starting multiple Diablo 2 Resurrected instances.

Be warned, it's still got a couple of rough edges.

Its heavily inspired by <a href="https://github.com/shupershuff/Diablo2RLoader">shupershuff/Diablo2RLoader</a>. Check this repo out if you want to learn more about multiboxing D2R :-)

The basic stuff works for launching multiple instances but I have a couple of features in mind that I want to implement:

- A distributable exe/zip
- Linux/Wine Support (main reason to write this in Python; not sure how feasible this is due to the token generation with pywin32/Windows DBAPI
- TZ/DClone Tracker
- aaand maybe something like the settings switcher from Diablo2Loader (lets see how much spare time I have for gaming and coding after winter is over)


Running on Windows

![Screenshot](./screenshot.png "D2R Loader screenshot")


Running on Linux

![Screenshot](./screenshot_linux.png "D2R Loader screenshot")

# How To Run This

1. Make sure [Python](https://python.org) is installed
2. Make sure [uv](https://docs.astral.sh/uv/) is installed
3. Download handle64.exe (TODO: Lets automate this)
4. Open a terminal as Administrator (otherwise you can't kill those nasty handles)
5. ``uv run d2rloader``
6. Check it out and configure it properly via the GUI :)

# Linux Pre-requisites:

- Lutris
- Install Diablo 2 Resurrected via Lutris (Battle.Net). You can also point to a D2R installation in Battle.Net
- Unfortunately only Password Auth is supported for Linux due to the way token generation works by using the Windows DBAPI. I'd happliy make Token auth available if someone could point me in the right direction.
 - If you get "We couldn't verify your account with that information", try changing your password and retry again. This worked for me at least.
- Handle64.exe is not needed on Linux as we are working with different WINEPREFIXES to solve this problem :-)
- Select your prefered WINEPREFIX location otherwise a default one will be set to $XDG_CONFIG_DIRS/d2rloader/wineprefixes

# License

MIT License
