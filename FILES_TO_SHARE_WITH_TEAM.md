# Files to Share with Team Members

When a team member clones the GitHub repository, they will NOT have access to secret/sensitive files. You need to share these files separately (via secure channels like encrypted email, password-protected zip, or secure file sharing).

## 🔴 CRITICAL: Files NOT in GitHub (Must Share Separately)

### 1. Backend Environment File
**File**: `backend/.env`
**Share via**: Secure channel (encrypted email/1Password/LastPass)
**Contains**:
- LiveKit credentials (URL, API Key, Secret)
- Google Cloud project configuration
- Gemini API key
- Qdrant database credentials
- Admin credentials
- OTP configuration

### 2. Google Cloud Service Account Key
**File**: `backend/project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json`
**Share via**: Secure channel (encrypted email/1Password/LastPass)
**Contains**:
- Google Cloud service account private key
- Project ID
- Authentication credentials

**⚠️ IMPORTANT**: This file has full access to your Google Cloud project!

### 3. Frontend Environment File
**File**: `frontend/.env`
**Share via**: Secure channel
**Contains**:
- API base URL (for production)
- Agent name configuration

## ✅ Files Already in GitHub (No Need to Share)

These files are safe to commit and are already in the repository:
- All source code files
- `.env.example` files (templates without real credentials)
- `package.json`, `requirements.txt`, etc.
- Documentation files
- Configuration templates

## 📋 Sharing Checklist

When onboarding a new developer:

### Step 1: Share Repository Access
- [ ] Add them to GitHub repository
- [ ] They clone: `git clone <repo-url>`

### Step 2: Share Secret Files Securely

**Option A: Via Secure File Sharing**
- [ ] Create a password-protected zip file with:
  - `backend/.env`
  - `backend/project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json`
  - `frontend/.env`
- [ ] Share zip file via email/drive
- [ ] Share password via different channel (SMS/WhatsApp)

**Option B: Via Password Manager** (Recommended)
- [ ] Share via 1Password/LastPass shared vault
- [ ] Include all three files

**Option C: Via Secure Messaging**
- [ ] Send files via Signal/Telegram secret chat
- [ ] Verify they received and saved securely

### Step 3: Share Documentation
- [ ] Point them to `SETUP_FOR_NEW_DEVELOPERS.md`
- [ ] Confirm they have all prerequisites installed
- [ ] Be available for setup support

### Step 4: Verify Their Setup
- [ ] They can run backend: `http://localhost:8000/docs` works
- [ ] They can run frontend: `http://localhost:5173` works
- [ ] They can login with OTP: 624251
- [ ] Voice features are working

## 🔐 Security Best Practices

### For File Sharing:
1. **Use encrypted channels** - Don't send secrets via plain email
2. **Use password protection** - Always protect zip files
3. **Separate password delivery** - Send password via different channel
4. **Verify recipient** - Confirm you're sending to correct person
5. **Delete after confirmation** - Remove files from shared locations once received

### For Team Members:
1. **Never commit secrets** - Double-check before `git add`
2. **Use environment variables** - Never hardcode credentials
3. **Rotate keys if leaked** - Immediately rotate any exposed credentials
4. **Keep `.env` local** - These files should NEVER be in version control
5. **Use `.env.example`** - Update template files when adding new config

## 📄 Sample Secure Sharing Email Template

```
Subject: Sahayak AI - Development Setup Files

Hi [Name],

Welcome to the Sahayak AI team!

I'm sharing the required configuration files for local development. These files contain sensitive credentials and should be kept secure.

Attached: password-protected zip file with:
- backend/.env
- backend/project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json
- frontend/.env

Password: [send via SMS/WhatsApp/separate channel]

Setup instructions:
1. Clone the repository: git clone [repo-url]
2. Extract the zip file
3. Place files in the correct locations (see SETUP_FOR_NEW_DEVELOPERS.md)
4. Follow setup guide in SETUP_FOR_NEW_DEVELOPERS.md

⚠️ IMPORTANT:
- Do NOT commit these files to Git
- Do NOT share with others without permission
- Store securely on your local machine

If you face any issues during setup, let me know!

Best regards,
[Your Name]
```

## 🚨 What to Do If Credentials Are Leaked

If any of these files are accidentally committed to Git or shared publicly:

### Immediate Actions:
1. **Rotate all credentials immediately**:
   - [ ] Generate new LiveKit API key/secret
   - [ ] Generate new Gemini API key
   - [ ] Create new Google Cloud service account
   - [ ] Change Qdrant API key
   - [ ] Update JWT secret
   - [ ] Change admin password

2. **Remove from Git history**:
   ```bash
   # If accidentally committed
   git filter-branch --force --index-filter \
   "git rm --cached --ignore-unmatch backend/.env" \
   --prune-empty --tag-name-filter cat -- --all
   ```

3. **Update all team members** with new credentials

4. **Review access logs** for unauthorized access

## 📞 Support

If team member has issues:
1. Check `SETUP_FOR_NEW_DEVELOPERS.md`
2. Verify they have all secret files
3. Check file locations are correct
4. Verify file contents (no copy-paste errors)
5. Check prerequisites are installed

---

**Remember**: Security is everyone's responsibility. When in doubt, ask before sharing!

**Document Version**: 1.0
**Last Updated**: 2026-09-27
