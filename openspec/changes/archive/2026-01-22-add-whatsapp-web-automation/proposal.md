# Add WhatsApp Web Automation

## Why
The system currently only supports WhatsApp Business API, which requires account approval and may not be available during initial testing. Adding WhatsApp Web automation with Playwright allows testing the alert functionality with a personal WhatsApp number before setting up the official Business API.

## What Changes
- Add WhatsApp Web automation client using Python + Playwright
- Implement QR code authentication flow with session persistence
- Add environment variable `WHATSAPP_SEND_MODE` to switch between `web` and `api` modes
- Extend Settings with Playwright configuration options
- Create factory pattern to instantiate appropriate WhatsApp client based on mode
- Add health check for WhatsApp Web session status
- Store session files in configurable directory

## Impact
- **Affected specs**: New spec: `whatsapp-notifications`
- **Affected code**: src/config/settings.py (add web mode config), src/alerts/whatsapp.py (add web client), src/alerts/factory.py (new), requirements.txt (add playwright), .env.example (add new vars)
