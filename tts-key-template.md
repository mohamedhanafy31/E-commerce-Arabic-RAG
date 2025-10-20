# Google Cloud Service Account Credentials Template

This file should contain your Google Cloud Service Account credentials in JSON format.

## Setup Instructions

1. **Create a Google Cloud Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON key file

2. **Rename the file:**
   - Rename your downloaded JSON file to `tts-key.json`
   - Place it in the root directory of this project

3. **Required Permissions:**
   - Speech-to-Text API access
   - Text-to-Speech API access

## File Structure
The JSON file should contain:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
```

## Security Note
⚠️ **NEVER commit this file to version control!**
- This file contains sensitive credentials
- It's already added to .gitignore
- Keep it secure and private

## Environment Variable Alternative
You can also set the credentials using an environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/tts-key.json"
```
