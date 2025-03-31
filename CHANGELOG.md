# Changelog

Here you can see the full list of changes between each release.

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
