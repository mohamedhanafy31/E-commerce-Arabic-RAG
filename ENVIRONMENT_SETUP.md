# Environment Variables Setup Guide

## 🔐 Required Environment Variables

### For Local Development

Create a `.env` file in the project root with the following variables:

```bash
# Gemini API Key (for RAG system)
GEMINI_API_KEY=your_gemini_api_key_here

# Hugging Face Token (for embeddings)
HF_TOKEN=your_huggingface_token_here

# Google Cloud Credentials (for ASR and TTS)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# Optional: Service URLs (for local development)
ASR_SERVICE_URL=http://localhost:8001
RAG_SERVICE_URL=http://localhost:8002
TTS_SERVICE_URL=http://localhost:8003
ORCHESTRATOR_SERVICE_URL=http://localhost:8004
```

### For Google Cloud Platform Deployment

Set these as Cloud Build substitution variables:

```bash
_GEMINI_API_KEY=your_gemini_api_key_here
_HF_TOKEN=your_huggingface_token_here
```

### For GitHub Actions

Add these as repository secrets:

- `GEMINI_API_KEY`: Your Gemini API key
- `HF_TOKEN`: Your Hugging Face token
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_SA_KEY`: Your service account JSON key

## 🔑 How to Get API Keys

### 1. Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

### 2. Hugging Face Token
1. Go to [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Sign in to your account
3. Click "New token"
4. Select "Read" access
5. Copy the generated token

### 3. Google Cloud Service Account Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to IAM & Admin > Service Accounts
3. Create a new service account or use existing
4. Grant these roles:
   - Cloud Run Admin
   - Cloud Build Editor
   - Storage Admin
   - Service Account User
5. Create and download JSON key file

## 🚀 Setup Instructions

### Local Development
```bash
# 1. Copy the template
cp env.example .env

# 2. Edit the .env file with your actual values
nano .env

# 3. Copy service account key
cp tts-key-template.json ASR_API/tts-key.json
cp tts-key-template.json TTS_API/tts-key.json

# 4. Edit the key files with your actual service account JSON
nano ASR_API/tts-key.json
nano TTS_API/tts-key.json
```

### Google Cloud Platform
```bash
# Set up Cloud Build trigger with substitution variables
gcloud builds triggers create github \
  --repo-name="E-commerce-Arabic-RAG" \
  --repo-owner="your-username" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild-ci-cd.yaml" \
  --substitutions="_GEMINI_API_KEY=your_key,_HF_TOKEN=your_token"
```

### GitHub Actions
1. Go to your repository settings
2. Navigate to Secrets and variables > Actions
3. Add the required secrets:
   - `GEMINI_API_KEY`
   - `HF_TOKEN`
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY`

## ⚠️ Security Notes

- **Never commit API keys to version control**
- **Use environment variables or secret management**
- **Rotate keys regularly**
- **Use least privilege principle for service accounts**
- **Monitor API usage and costs**

## 🔧 Troubleshooting

### Common Issues

1. **"API key not found"**
   - Check if environment variable is set correctly
   - Verify the key is valid and has proper permissions

2. **"Authentication failed"**
   - Verify service account key is correct
   - Check if service account has required roles

3. **"Token expired"**
   - Generate new tokens
   - Update environment variables

### Testing Environment Variables
```bash
# Test if variables are set
echo $GEMINI_API_KEY
echo $HF_TOKEN
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test API connectivity
python -c "import os; print('Gemini key:', os.getenv('GEMINI_API_KEY', 'Not set')[:10] + '...')"
```

## 📚 Additional Resources

- [Google Cloud Authentication](https://cloud.google.com/docs/authentication)
- [Hugging Face Token Management](https://huggingface.co/docs/hub/security-tokens)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Environment Variables Best Practices](https://12factor.net/config)
