# Changelog

Here you can see the full list of changes between each release.

## Version 1.4.0

Unreleased

### Added

- Linux: Switch from Lutris to [umu-launcher](github.com/Open-Wine-Components/umu-launcher).
  Lutris might still be useful to launch Battle.NET to keep D2R updated though
- Linux: Implemented Token Authentication


**Full Changelog**: [v1.3.6...v1.4.0](https://github.com/sh4nks/d2rloader/compare/v1.3.6...v1.4.0)

## Version 1.3.6

Released December 6th, 2025

### Fixed

- Fix crash in case 'wmctrl' doesn't work for some reason. See #6 for more information.
- Don't log sensitive account information (i.e. email address) when logging whole objects


**Full Changelog**: [v1.3.5...v1.3.6](https://github.com/sh4nks/d2rloader/compare/v1.3.5...v1.3.6)


## Version 1.3.5

Released September 30th, 2025

### Fixed

- Fix DC Info not working anymore due to "China" being added.
  Region China will be displayed as well now, but at the moment it is not possible to
  select this region as I don't know the battle.net server URI for it.


**Full Changelog**: [v1.3.4...v1.3.5](https://github.com/sh4nks/d2rloader/compare/v1.3.4...v1.3.5)


## Version 1.3.4

Released August 27th, 2025

### Added

- Cloned profiles will have a counted unique name (Cloned, Cloned1, Cloned2, ...)
- Ensure profile names are unique on input. If the profile name is not unique the
  WINEPREFIX cannot be reused and thus the profile not started


**Full Changelog**: [v1.3.3...v1.3.4](https://github.com/sh4nks/d2rloader/compare/v1.3.3...v1.3.4)


## Version 1.3.3

Released August 26th, 2025

### Added

- AppImage for Linux

### Fixed

- Fix canceling the "Load Account Settings" Dialog


**Full Changelog**: [v1.3.2...v1.3.3](https://github.com/sh4nks/d2rloader/compare/v1.3.2...v1.3.3)


## Version 1.3.2

Released April 14th, 2025

### Fixed

- Fix spacing of profile table
- linux: Fix error message for token-based authentication ([#3](https://github.com/sh4nks/d2rloader/issues/3))
- linux: Make 'gamemode' optional ([#4](https://github.com/sh4nks/d2rloader/issues/4))


**Full Changelog**: [v1.3.1...v1.3.2](https://github.com/sh4nks/d2rloader/compare/v1.3.1...v1.3.2)


## Version 1.3.1

Released April 1st, 2025

### Fixed

- Include the 'imptools' code to make packaging on (Arch) Linux easier


**Full Changelog**: [v1.3.0...v1.3.1](https://github.com/sh4nks/d2rloader/compare/v1.3.0...v1.3.1)


## Version 1.3.0

Released March 31st, 2025

### Added

- Plugin API - Its possible to hook into some parts of D2RLoader and extend it with plugins
- Refactored UI to have all relevant components/widgets inside its appropriate layouts


**Full Changelog**: [v1.2.1...v1.3.0](https://github.com/sh4nks/d2rloader/compare/v1.2.1...v1.3.0)


## Version 1.2.1

Released March 30th, 2025

### Added

- Linux: Window Titles are now renamed as well (this will only work as long as Proton/Wine uses X/XWayland)
- D2RLoader will look for running D2R instances at startup if the app was closed while some D2R instances where still running

### Fixed

- Fix initial startup in case 'settings.json' is not available
- Linux: Killing D2R instances now works correctly
- Linux: Add 'wmctrl' to dependencies


**Full Changelog**: [v1.2.0...v1.2.1](https://github.com/sh4nks/d2rloader/compare/v1.2.0...v1.2.1)


## Version 1.2.0

Released March 18th, 2025

### Added

- Linux: Add support for the Game Settings Switcher
- Linux: Add PKGBUILD to install D2RLoader directly from [AUR](https://aur.archlinux.org/packages/d2rloader-git)

### Fixed/Improved

- Improved the install and setup instructions


**Full Changelog**: [v1.1.0...v1.2.0](https://github.com/sh4nks/d2rloader/compare/v1.1.0...v1.2.0)


## Version 1.1.0

Released March 11th, 2025

### Added

- Windows: Game Settings Switcher - Custom game settings for each profile 
- Windows: Download and set up ``handle.exe`` via a button (Account Settings -> Download)
- Added Advanced Settings (File -> Settings) - Configure the D2Emu Token, Log Settings and the WINEPREFIX from within the App

### Fixed/Improved

- Windows: Suppress console window when running ``handle.exe``
- Remove password from logs when using authentication method ``Password``


**Full Changelog**: [v1.0.0...v1.0.0](https://github.com/sh4nks/d2rloader/compare/v1.0.0...v1.1.0)


## Version 1.0.0

Released February 21th, 2025

- Initial release
