## ADDED Requirements

### Requirement: Improved Outdoor Motion Detection
The system SHALL use enhanced motion detection parameters optimized for outdoor scenarios to reliably detect vehicles and people.

#### Scenario: Vehicle passing with lateral camera view
- **GIVEN** a camera with lateral view of a street
- **WHEN** a vehicle passes through the frame
- **THEN** motion_score shall be >= 20% for medium sensitivity
- **AND** motion_score shall be >= 15% for low sensitivity
- **AND** motion_score shall be >= 25% for high sensitivity
- **AND** the frame shall be sent to LLM with default threshold (10%)

#### Scenario: Person walking through outdoor scene
- **GIVEN** a camera monitoring outdoor area
- **WHEN** a person walks through the frame
- **THEN** motion_score shall be >= 15% for medium sensitivity
- **AND** the frame shall be sent to LLM with default threshold

#### Scenario: Static outdoor scene with no movement
- **GIVEN** a camera captures consecutive frames of static outdoor scene
- **WHEN** no movement occurs (parked cars, trees, buildings)
- **THEN** motion_score shall be < 5% after first frame
- **AND** frames shall be filtered (not sent to LLM)

#### Scenario: Gradual lighting changes do not trigger false positives
- **GIVEN** outdoor camera during sunrise or sunset
- **WHEN** lighting gradually changes over multiple frames
- **THEN** background subtraction shall adapt without triggering motion
- **AND** motion_score shall remain < 10% unless actual movement occurs

#### Scenario: Algorithm preprocessing preserves motion details
- **GIVEN** a frame with vehicle or person movement
- **WHEN** frame is preprocessed for motion detection
- **THEN** GaussianBlur kernel shall be (2,2) or smaller
- **AND** downsampling to 320x240 shall preserve edge information
- **AND** motion details shall not be smoothed away

#### Scenario: Pixel difference detects subtle changes
- **GIVEN** two consecutive frames with vehicle movement
- **WHEN** pixel difference is calculated
- **THEN** binary threshold shall be <= 10 to capture subtle changes
- **AND** scale factor shall be >= 15 to amplify outdoor motion
- **AND** changed pixels shall be accurately counted

#### Scenario: Background subtraction tuned for outdoor scenes
- **GIVEN** outdoor camera with variable lighting
- **WHEN** MOG2 background subtractor is initialized
- **THEN** varThreshold shall be <= 12 for better sensitivity
- **AND** history shall be >= 500 frames for outdoor adaptation
- **AND** shadows shall be detected and removed (detectShadows=True)

## ADDED Requirements

### Requirement: Motion Sensitivity Configuration
The system SHALL support configurable motion sensitivity levels to optimize detection for different scenarios without manual parameter tuning.

#### Scenario: Create camera with default sensitivity
- **GIVEN** a new camera is created without specifying sensitivity
- **WHEN** the camera is saved to the database
- **THEN** motion_sensitivity shall default to "medium"
- **AND** MotionDetector shall use medium sensitivity preset parameters

#### Scenario: Create camera with high sensitivity for outdoor monitoring
- **GIVEN** a new camera is created for outdoor vehicle detection
- **WHEN** motion_sensitivity is set to "high"
- **THEN** camera shall use aggressive motion detection parameters
- **AND** vehicles and people shall be reliably detected (score >= 25%)

#### Scenario: Create camera with low sensitivity for stable scenes
- **GIVEN** a new camera monitors mostly static indoor area
- **WHEN** motion_sensitivity is set to "low"
- **THEN** camera shall use conservative detection parameters
- **AND** only significant movements shall trigger detection

#### Scenario: Update camera sensitivity at runtime
- **GIVEN** an existing camera with motion_sensitivity = "medium"
- **WHEN** sensitivity is updated to "high" via hot-reload
- **THEN** MotionDetector shall be reinitialized with high sensitivity parameters
- **AND** next frame comparison shall use new parameters
- **AND** no application restart is required

#### Scenario: Sensitivity presets apply correct parameters
- **GIVEN** a camera with motion_sensitivity = "medium"
- **WHEN** MotionDetector is initialized
- **THEN** blur_kernel shall be (2, 2)
- **AND** pixel_threshold shall be 10
- **AND** pixel_scale shall be 15
- **AND** bg_var_threshold shall be 10
- **AND** bg_history shall be 500

#### Scenario: Custom sensitivity allows manual tuning
- **GIVEN** a camera with motion_sensitivity = "custom"
- **WHEN** MotionDetector is initialized
- **THEN** parameters shall be loaded from camera-specific config
- **AND** user-defined values shall override preset defaults
- **AND** system shall not auto-adjust parameters

#### Scenario: Sensitivity level persists across restarts
- **GIVEN** a camera with motion_sensitivity = "high"
- **WHEN** application is restarted
- **THEN** camera shall reload with "high" sensitivity from database
- **AND** motion detection shall use same parameters as before restart

#### Scenario: Sensitivity affects motion scores predictably
- **GIVEN** identical scene with vehicle passing
- **WHEN** tested with low, medium, and high sensitivity
- **THEN** high sensitivity shall produce score >= medium score >= low score
- **AND** relative ordering shall be consistent across different scenes

#### Scenario: Invalid sensitivity value is rejected
- **GIVEN** an attempt to set motion_sensitivity to invalid value
- **WHEN** camera configuration is validated
- **THEN** system shall reject values other than "low", "medium", "high", "custom"
- **AND** error message shall list valid options
- **AND** current sensitivity shall remain unchanged

### Requirement: Motion Detection Debugging
The system SHALL provide tools to visualize and troubleshoot motion detection issues.

#### Scenario: Enable debug mode to save motion analysis frames
- **GIVEN** a camera has motion detection issues
- **WHEN** debug mode is enabled in MotionDetector
- **THEN** system shall save preprocessed frames to debug directory
- **AND** system shall save pixel difference masks
- **AND** system shall save background subtraction masks
- **AND** files shall be timestamped and include camera ID

#### Scenario: Debug mode logs detailed algorithm steps
- **GIVEN** MotionDetector is in debug mode
- **WHEN** motion is detected on a frame
- **THEN** system shall log preprocessing parameters
- **AND** system shall log pixel_diff_score and bg_sub_score separately
- **AND** system shall log which components contribute most to final score
- **AND** logs shall include frame timestamp

#### Scenario: Debug mode does not impact performance significantly
- **GIVEN** MotionDetector is in debug mode
- **WHEN** frames are processed
- **THEN** performance overhead shall be < 10ms per frame
- **AND** debug file I/O shall not block frame processing

#### Scenario: Debug files are cleaned up automatically
- **GIVEN** debug mode has been running
- **WHEN** debug directory size exceeds 100MB or age > 24 hours
- **THEN** oldest debug files shall be automatically deleted
- **AND** system shall log cleanup operation

### Requirement: Motion Detection Calibration
The system SHALL provide interactive tools to test and tune motion detection parameters.

#### Scenario: Visualize motion detection on test video
- **GIVEN** a test video file with known motion events
- **WHEN** visualization tool is run with video path
- **THEN** tool shall output video with motion mask overlay
- **AND** tool shall display motion score on each frame
- **AND** tool shall generate histogram of score distribution
- **AND** output shall be saved to specified path

#### Scenario: Test different sensitivity presets on video
- **GIVEN** a test video file
- **WHEN** visualization tool is run with --all-sensitivities flag
- **THEN** tool shall generate output for low, medium, and high presets
- **AND** tool shall compare scores side-by-side
- **AND** tool shall report detection accuracy if ground truth provided

#### Scenario: Calibrate motion detection on live camera
- **GIVEN** a running camera with suboptimal detection
- **WHEN** calibration tool is launched with camera ID
- **THEN** tool shall display live camera feed
- **AND** tool shall overlay motion mask in real-time
- **AND** tool shall show current motion score
- **AND** tool shall provide sliders to adjust parameters
- **AND** tool shall allow saving tuned parameters to database

#### Scenario: Calibration tool validates parameter ranges
- **GIVEN** user adjusts parameters in calibration tool
- **WHEN** parameter value is out of valid range
- **THEN** tool shall clamp value to valid range
- **AND** tool shall display warning message
- **AND** tool shall show recommended values

#### Scenario: Calibration saves custom sensitivity profile
- **GIVEN** user has tuned parameters via calibration tool
- **WHEN** user clicks "Save"
- **THEN** system shall update camera with motion_sensitivity="custom"
- **AND** system shall save individual parameter values
- **AND** system shall call hot-reload to apply immediately
- **AND** system shall confirm save success to user

### Requirement: Motion Detection Benchmarking
The system SHALL validate motion detection accuracy against known test cases.

#### Scenario: Benchmark against vehicle detection dataset
- **GIVEN** test videos with vehicles passing at various speeds and angles
- **WHEN** motion detection is run with medium sensitivity
- **THEN** true positive rate shall be >= 90% for lateral views
- **AND** true positive rate shall be >= 80% for frontal views
- **AND** false positive rate shall be <= 10% for static frames

#### Scenario: Benchmark against person detection dataset
- **GIVEN** test videos with people walking at various speeds
- **WHEN** motion detection is run with medium sensitivity
- **THEN** true positive rate shall be >= 85% for normal walking speed
- **AND** true positive rate shall be >= 70% for slow walking speed
- **AND** detection shall work for people at various distances from camera

#### Scenario: Benchmark performance across sensitivity levels
- **GIVEN** benchmark test dataset
- **WHEN** tests are run with low, medium, and high sensitivity
- **THEN** high sensitivity shall have highest true positive rate
- **AND** low sensitivity shall have lowest false positive rate
- **AND** medium sensitivity shall balance true positives and false positives
- **AND** all levels shall process frames in < 50ms

#### Scenario: Benchmark reports detailed metrics
- **GIVEN** benchmark tests are complete
- **WHEN** results are generated
- **THEN** report shall include true positive / false positive / true negative / false negative counts
- **AND** report shall include precision, recall, and F1 score per sensitivity
- **AND** report shall include average motion scores per scenario type
- **AND** report shall highlight any failed test cases


