# Change: Make FRAME_INTERVAL_SECONDS work as global default

## Why
The `FRAME_INTERVAL_SECONDS` environment variable is defined in settings but never used. Each camera has its own `frame_interval` that defaults to 10 seconds in multiple places (database, API, code), causing the global setting to be completely ignored.

## What Changes
- Use `settings.frame_interval_seconds` as the default for new cameras
- Update `CameraConfig.frame_interval` default to read from settings
- Update database model default to use settings value
- Update API schema default to use settings value
- Update repository method defaults to use settings value
- Ensure consistency across all layers: settings, config, database, API

## Impact
- Affected specs: `camera-config` (new capability)
- Affected code:
  - `src/config/settings.py:62` - Define and use the setting
  - `src/capture/camera.py:27` - CameraConfig default
  - `src/storage/models.py:25` - Database column default
  - `src/api/schemas.py:19` - API schema default
  - `src/storage/repository.py:24` - Repository default
  - `src/main.py:217-225` - Camera loading logic
