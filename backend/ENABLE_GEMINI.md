# 🚀 Use Gemini API via Vertex AI (Paid Account)

## 📊 Current Verification Status

- ✅ **STT (Speech-to-Text)**: **WORKING** (using service account & ₹1000 GCP balance)
- ✅ **TTS (Text-to-Speech)**: **WORKING** (generated 27KB MP3 using service account & ₹1000 GCP balance)
- ✅ **Gemini AI (Vertex AI)**: verified with the supported `gemini-3.5-flash` model at the global Vertex endpoint.

---

## 🔍 Why the 404 Error Happened

Looking at your IAM roles screenshot, your Service Account `vyamitaigc@project-d8fe05cb-90bb-4815-aca.iam.gserviceaccount.com` currently has:
- `Agent Platform administrator`
- `Agent Platform user`
- `AI Platform Admin` *(Legacy ML Engine role)*
- `Gemini for Google Cloud User` *(This is ONLY for Duet AI / GCP Console IDE assistance!)*
- `Service Usage Consumer`

The old diagnostic used `vertexai.generative_models` with `gemini-1.5-pro` in `us-east1`. That SDK is retired and the 1.5 model is no longer a valid choice. The roles in the screenshot are for Cloud Assist / Agent Platform, which are distinct products from invoking Gemini through Vertex AI.

The codebase now uses the supported Google Gen AI SDK, `gemini-3.5-flash`, the stable `v1` API, and the `global` Vertex endpoint. `Vertex AI User` (`roles/aiplatform.user`) remains the least-privilege runtime role for the service account.

---

## 🔧 Runtime Configuration

### STEP 1: Add the "Vertex AI User" Role (if it is not already assigned)

1. Open GCP IAM Console:
   👉 **https://console.cloud.google.com/iam-admin/iam?project=project-d8fe05cb-90bb-4815-aca**
2. Find your Service Account:
   `vyamitaigc@project-d8fe05cb-90bb-4815-aca.iam.gserviceaccount.com`
3. Click the **Pencil / Edit icon** on the right side.
4. Click **+ ADD ANOTHER ROLE**.
5. Search for and select: **`Vertex AI User`**
6. Click **SAVE**.

---

### STEP 2: Set the supported model configuration

Add these values to `backend/.env` (the project ID is inferred from a service-account JSON key, so it is optional):

```dotenv
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-3.5-flash
GEMINI_TEMPERATURE=0.35
```

The Vertex AI API and billing must be enabled. Opening Vertex AI Studio is not required to provision a Gemini endpoint.

---

## 🧪 Test Your Setup

Once you complete the 2 steps above, run the test script:

```powershell
python -X utf8 test_gemini_vertex.py
```

Or run the full suite:

```powershell
python -X utf8 test_google_services.py
```

### Expected Output:
```
Gemini Vertex AI test
Project: your-google-cloud-project-id
Location: global
Model: gemini-3.5-flash
PASS: Vertex AI connectivity verified.
```

