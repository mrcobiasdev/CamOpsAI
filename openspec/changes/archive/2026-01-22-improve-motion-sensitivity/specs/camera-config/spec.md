## ADDED Requirements

### Requirement: Motion Sensitivity Configuration Storage
The system SHALL persist motion sensitivity settings per camera in the database and load them at runtime.

#### Scenario: New camera without explicit sensitivity uses global default
- **GIVEN** a new camera is created without specifying motion_sensitivity
- **WHEN** the camera is saved to the database
- **THEN** motion_sensitivity shall default to "medium"
- **AND** the database shall store motion_sensitivity as "medium"

#### Scenario: Camera created with explicit sensitivity stores value
- **GIVEN** a new camera is created with motion_sensitivity = "high"
- **WHEN** the camera is saved to the database
- **THEN** the database shall store motion_sensitivity as "high"
- **AND** MotionDetector shall use high sensitivity parameters

#### Scenario: Camera loaded from database uses stored sensitivity
- **GIVEN** a camera in the database has motion_sensitivity = "low"
- **WHEN** the camera is loaded at application startup
- **THEN** CameraConfig shall include motion_sensitivity = "low"
- **AND** MotionDetector shall be initialized with low sensitivity preset

#### Scenario: Update camera sensitivity persists to database
- **GIVEN** an existing camera with motion_sensitivity = "medium"
- **WHEN** sensitivity is updated to "high" via API or CLI
- **THEN** database shall be updated with new value
- **AND** hot-reload shall apply changes immediately
- **AND** value shall persist across application restarts

#### Scenario: Sensitivity field allows only valid values
- **GIVEN** an attempt to set motion_sensitivity
- **WHEN** value is not in ["low", "medium", "high", "custom"]
- **THEN** database constraint shall reject the value
- **AND** error message shall indicate valid options
- **AND** camera configuration shall remain unchanged

#### Scenario: Migration adds sensitivity field to existing cameras
- **GIVEN** existing cameras in database without motion_sensitivity field
- **WHEN** database migration is applied
- **THEN** all cameras shall have motion_sensitivity = "medium" added
- **AND** existing cameras shall maintain all other settings unchanged
- **AND** motion detection behavior shall improve with new default parameters
