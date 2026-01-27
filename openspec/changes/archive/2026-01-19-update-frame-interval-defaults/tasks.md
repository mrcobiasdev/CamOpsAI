## 1. Implementation
- [x] 1.1 Update `CameraConfig` in `src/capture/camera.py` to use `settings.frame_interval_seconds` as default
- [x] 1.2 Update database model `Camera.frame_interval` in `src/storage/models.py` to use settings default
- [x] 1.3 Update API schema `CameraCreate`/`CameraUpdate` in `src/api/schemas.py` to use settings default
- [x] 1.4 Update repository methods in `src/storage/repository.py` to use settings default
- [x] 1.5 Verify camera loading in `src/main.py` respects settings when cameras don't have explicit intervals

## 2. Testing
- [x] 2.1 Test creating new camera without specifying frame_interval - should use `FRAME_INTERVAL_SECONDS` from .env
- [x] 2.2 Test updating existing camera without changing frame_interval - should preserve existing value
- [x] 2.3 Test setting `FRAME_INTERVAL_SECONDS=120` in .env and creating camera - camera should use 120s interval
- [x] 2.4 Test loading cameras from database - should use stored interval, not settings
- [x] 2.5 Verify capture loop uses the camera-specific interval correctly

## 3. Documentation
- [x] 3.1 Update `.env.example` to document that `FRAME_INTERVAL_SECONDS` is the global default
- [x] 3.2 Add comment in `CameraConfig` explaining it uses settings as default
