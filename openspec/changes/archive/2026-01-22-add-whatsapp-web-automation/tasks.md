## 1. Implementation

### 1.1 Configuration and Settings
- [x] Add WhatsApp Web configuration fields to src/config/settings.py:
  - `whatsapp_send_mode`: str (enum: "api" | "web", default: "api")
  - `whatsapp_session_dir`: str (default: "./sessions/whatsapp/")
  - `whatsapp_headless`: bool (default: true)
- [x] Update src/config/settings.py to map environment variables
- [x] Update .env.example with new WhatsApp configuration variables

### 1.2 WhatsApp Web Client
- [x] Create src/alerts/whatsapp_web.py with WhatsAppWebClient class
  - Initialize Playwright browser and context
  - Implement QR code authentication flow
  - Save and load session from configured directory
  - Implement send_message() method
  - Implement send_alert() method (format alerts like Business API client)
  - Implement health_check() method
  - Implement close() method for resource cleanup
- [x] Add logging for authentication status and session management
- [x] Handle session expiration and re-authentication

### 1.3 Factory Pattern for WhatsApp Clients
- [x] Create src/alerts/factory.py with create_whatsapp_client() function
  - Check whatsapp_send_mode setting
  - Return WhatsAppClient for "api" mode
  - Return WhatsAppWebClient for "web" mode
  - Handle invalid mode with appropriate error

### 1.4 Integration with Alert Detector
- [x] Update src/main.py to use factory pattern
- [x] Initialize WhatsApp client based on send mode
- [x] Ensure compatibility with existing alert detection logic
- [x] Test alert sending with both modes

### 1.5 Dependencies
- [x] Add playwright to requirements.txt
- [x] Update documentation to include Playwright installation:
  - Add pip install playwright
  - Add playwright install (for browser binaries)

### 1.6 Testing
- [ ] Add unit tests for WhatsAppWebClient
  - Test session loading/saving
  - Test message formatting
  - Test authentication flow (mocked)
- [ ] Add integration tests for factory pattern
  - Test client creation for both modes
  - Test error handling for invalid mode
- [ ] Manual testing for WhatsApp Web:
  - Test QR code scanning flow
  - Test session persistence across restarts
  - Test alert sending to personal number
  - Test health check endpoint

### 1.7 Documentation
- [x] Update README.md with WhatsApp Web configuration instructions
- [x] Document QR code authentication process
- [x] Add troubleshooting section for common WhatsApp Web issues
- [x] Document environment variable options
