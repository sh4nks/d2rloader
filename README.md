# Diablo 2 Resurrected Loader

This is a simple Qt app which manages starting multiple Diablo 2 Resurrected instances.

Its heavily inspired by <a href="https://github.com/shupershuff/Diablo2RLoader">shupershuff/Diablo2RLoader</a>. Check this repo out if you want to learn more about multiboxing D2R :-)


Running on Windows

![Screenshot](./screenshot_windows.png "D2R Loader Windows Screenshot")

Running on Linux

![Screenshot](./screenshot_linux.png "D2R Loader Linux Screenshot")


# Getting Started

D2RLoader supports Windows and Linux (via Wine/[Lutris](https://lutris.net)).
On Linux only password authentication is supported due to the way tokens are protected using the proprietary Windows DBAPI.
Aside from that, I have only tested my Linux environment (Arch Linux). So, if you find any issues with yours, please report them so I can get them fixed!

If you try to login using password authentication and get an error like  _"We couldn't verify your account with that information"_, try changing your password and try again. This worked for me at least.

The TZ Info and DClone Info require a working API key from [d2emu.com](https://d2emu.com).

All configuration files are stored in ``%APPDATA%/d2rloader`` on Windows or ``$XDG_CONFIG_DIRS/d2rloader`` on Linux


## Windows

- Download the latest "D2RLoader.windows.zip" from the releases page here and extract it.
- Download handle64.exe - You can use [this](https://download.sysinternals.com/files/Handle.zip) link.
- Create a desktop shortcut and configure it to run as **Administrator**. Admin rights are unfortunately needed to kill the handles.
- Start D2RLoader.exe and configure the handle.exe path and D2R game folder (File -> Settings)
- Create and configure a new account by pressing "Add".
- Start the game with the configured account.

## Linux

- Install Lutris (i.e. via your package manager ``pacman -S lutris``)
- Search for Diablo 2 Resurrected on Lutris and install it. This will install the Battle.NET app.
- Install Diablo 2 Resurrected from the Battle.NET app. Tipp: If you have D2R already installed on Windows you can just copy it to your preferred location and point to it from the Battle.NET app.
- Handle64.exe is not needed on Linux as we are working with different WINEPREFIXES to solve this problem :-)
- Select your prefered WINEPREFIX location otherwise a default one will be set to $XDG_CONFIG_DIRS/d2rloader/wineprefixes.


# Planned Features

- Minimize to system tray
- Settings switcher (per account game settings)
- Change Window Title on Linux (not easily done on Wayland, maybe we can change them in Wine?)
- Provide a package for Linux

# License

MIT License
