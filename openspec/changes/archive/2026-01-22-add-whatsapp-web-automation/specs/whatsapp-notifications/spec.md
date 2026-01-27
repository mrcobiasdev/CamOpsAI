# whatsapp-notifications Specification

## Purpose
Send security alerts and notifications via WhatsApp with support for multiple sending methods: WhatsApp Web automation (for testing/development) and WhatsApp Business API (for production).

## ADDED Requirements

### Requirement: WhatsApp Send Mode Configuration
The system SHALL support multiple WhatsApp sending modes selectable via environment variable `WHATSAPP_SEND_MODE`.

#### Scenario: Default to Business API mode
- **GIVEN** no `WHATSAPP_SEND_MODE` is configured
- **WHEN** the application starts
- **THEN** send mode shall default to `api`
- **AND** WhatsApp Business API client shall be instantiated

#### Scenario: Configure Web automation mode
- **GIVEN** `WHATSAPP_SEND_MODE=web` is configured in environment
- **WHEN** the application starts
- **THEN** WhatsApp Web automation client shall be instantiated
- **AND** Playwright browser session shall be initialized

#### Scenario: Invalid send mode
- **GIVEN** `WHATSAPP_SEND_MODE=invalid` is configured
- **WHEN** the application attempts to create WhatsApp client
- **THEN** an error shall be logged
- **AND** the application shall fallback to default mode or fail gracefully

### Requirement: WhatsApp Web Authentication with QR Code
The system SHALL support QR code authentication for WhatsApp Web, with session persistence across restarts.

#### Scenario: First login requires QR code scan
- **GIVEN** no previous session file exists
- **WHEN** WhatsApp Web client is initialized
- **THEN** Playwright shall open browser to https://web.whatsapp.com
- **AND** the system shall wait for QR code to appear
- **AND** the system shall log "Scan the QR code with your WhatsApp mobile app to authenticate"
- **AND** the system shall wait for user to scan and authenticate

#### Scenario: Successful authentication saves session
- **GIVEN** user scans QR code and authenticates
- **WHEN** authentication completes successfully
- **THEN** session data shall be saved to configured session directory
- **AND** the system shall log "WhatsApp Web session saved successfully"
- **AND** subsequent restarts shall use saved session

#### Scenario: Restore session from file
- **GIVEN** a valid session file exists
- **WHEN** WhatsApp Web client is initialized
- **THEN** the system shall load session from file
- **AND** the system shall log "WhatsApp Web session restored from file"
- **AND** authentication shall be automatic without QR code

#### Scenario: Invalid session file
- **GIVEN** a corrupted or expired session file exists
- **WHEN** WhatsApp Web client attempts to load session
- **THEN** the system shall log "Session file invalid, requiring new authentication"
- **AND** the system shall fallback to QR code authentication
- **AND** a new session shall be created after successful scan

### Requirement: Session Persistence Configuration
The system SHALL allow configuration of WhatsApp Web session storage directory.

#### Scenario: Default session directory
- **GIVEN** no `WHATSAPP_SESSION_DIR` is configured
- **WHEN** WhatsApp Web client is initialized
- **THEN** session files shall be stored in `./sessions/whatsapp/` directory

#### Scenario: Custom session directory
- **GIVEN** `WHATSAPP_SESSION_DIR=/custom/path` is configured
- **WHEN** WhatsApp Web client is initialized
- **THEN** session files shall be stored in `/custom/path` directory
- **AND** the directory shall be created if it doesn't exist

### Requirement: WhatsApp Web Message Sending
The system SHALL send messages via WhatsApp Web automation using Playwright when in `web` mode.

#### Scenario: Send text message via WhatsApp Web
- **GIVEN** send mode is `web`
- **AND** WhatsApp Web is authenticated
- **WHEN** an alert is triggered
- **THEN** Playwright shall navigate to chat for recipient number
- **AND** the message shall be typed into input field
- **AND** the send button shall be clicked
- **AND** the system shall log "Message sent via WhatsApp Web to {number}"
- **AND** the function shall return success status

#### Scenario: Format alert message for WhatsApp Web
- **GIVEN** an alert needs to be sent
- **WHEN** the message is formatted
- **THEN** the message shall include camera name
- **AND** the message shall include event description
- **AND** the message shall include keywords matched
- **AND** the message shall include priority level with emoji
- **AND** the message shall be formatted with bold text where appropriate

#### Scenario: Handle message sending failure
- **GIVEN** send mode is `web`
- **AND** WhatsApp Web session is disconnected
- **WHEN** an alert is triggered
- **THEN** the system shall log an error
- **AND** the system shall attempt to re-authenticate
- **AND** the message shall be retried or marked as failed

### Requirement: WhatsApp Factory Pattern
The system SHALL use a factory pattern to create the appropriate WhatsApp client based on send mode.

#### Scenario: Create Business API client
- **GIVEN** `WHATSAPP_SEND_MODE=api`
- **AND** `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_ID` are configured
- **WHEN** factory creates WhatsApp client
- **THEN** WhatsAppClient (Business API) shall be instantiated
- **AND** the client shall be ready to send messages

#### Scenario: Create Web automation client
- **GIVEN** `WHATSAPP_SEND_MODE=web`
- **WHEN** factory creates WhatsApp client
- **THEN** WhatsAppWebClient shall be instantiated
- **AND** Playwright browser shall be launched
- **AND** authentication shall be initialized

#### Scenario: Factory validation
- **GIVEN** `WHATSAPP_SEND_MODE=web`
- **AND** Playwright is not installed
- **WHEN** factory attempts to create client
- **THEN** an informative error shall be raised
- **AND** the error shall indicate missing Playwright dependency

### Requirement: Health Check for WhatsApp Services
The system SHALL provide health check endpoints for both WhatsApp Business API and WhatsApp Web.

#### Scenario: Health check for Business API
- **GIVEN** send mode is `api`
- **WHEN** health check is called
- **THEN** the system shall verify connection to WhatsApp Business API
- **AND** return `true` if connection is successful
- **AND** return `false` if connection fails

#### Scenario: Health check for WhatsApp Web
- **GIVEN** send mode is `web`
- **WHEN** health check is called
- **THEN** the system shall verify Playwright browser is running
- **AND** the system shall verify WhatsApp Web session is authenticated
- **AND** return `true` if both conditions are met
- **AND** return `false` if either condition fails

#### Scenario: Health check returns diagnostic info
- **GIVEN** health check is called for WhatsApp
- **WHEN** check runs
- **THEN** the return value shall include mode (`web` or `api`)
- **AND** the return value shall include authentication status
- **AND** the return value shall include last successful send timestamp

### Requirement: WhatsApp Client Resource Management
The system SHALL properly manage resources for both WhatsApp Business API and WhatsApp Web clients.

#### Scenario: Close Business API client
- **GIVEN** Business API client is active
- **WHEN** application shuts down
- **THEN** HTTP client connections shall be closed
- **AND** resources shall be released properly

#### Scenario: Close WhatsApp Web client
- **GIVEN** WhatsApp Web client is active
- **WHEN** application shuts down
- **THEN** Playwright browser context shall be closed
- **AND** Playwright browser instance shall be closed
- **AND** session shall be saved to disk

#### Scenario: Graceful shutdown on error
- **GIVEN** an unhandled error occurs
- **WHEN** application terminates
- **THEN** WhatsApp clients shall attempt to close gracefully
- **AND** sessions shall be saved before shutdown
- **AND** errors during shutdown shall be logged without crashing

### Requirement: WhatsApp Configuration in Settings
The system SHALL include all necessary configuration options for both WhatsApp sending modes.

#### Scenario: Business API settings
- **GIVEN** application settings are loaded
- **THEN** settings shall include `whatsapp_api_url` (default: https://graph.facebook.com/v18.0)
- **AND** settings shall include `whatsapp_token` (optional)
- **AND** settings shall include `whatsapp_phone_id` (optional)

#### Scenario: Web automation settings
- **GIVEN** application settings are loaded
- **THEN** settings shall include `whatsapp_send_mode` (default: api)
- **AND** settings shall include `whatsapp_session_dir` (default: ./sessions/whatsapp/)
- **AND** settings shall include `whatsapp_headless` (default: true, for Playwright browser)

#### Scenario: Environment variable mapping
- **GIVEN** environment variables are set
- **THEN** `WHATSAPP_SEND_MODE` shall map to `whatsapp_send_mode`
- **AND** `WHATSAPP_SESSION_DIR` shall map to `whatsapp_session_dir`
- **AND** `WHATSAPP_HEADLESS` shall map to `whatsapp_headless`
