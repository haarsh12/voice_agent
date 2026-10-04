# Enhanced Profile Migration Instructions

## What This Adds:
1. ✅ **State dropdown** - All Indian states/UTs
2. ✅ **District dropdown** - Cascading based on selected state
3. ✅ **Date of birth selector** - Day/Month/Year dropdowns
4. ✅ **PIN code field** - 6-digit postal code (required)
5. ✅ **Email field** - Optional email address

## Step-by-Step Application:

### Step 1: Apply Database Migration
```powershell
cd backend
python apply_enhanced_profile_migration.py
```

**Expected output:**
```
🔄 Applying enhanced profile migration...
✅ Migration applied successfully!
   ✓ date_of_birth column added
   ✓ pin_code column added (VARCHAR(6))
   ✓ email column added (VARCHAR(254))
   ✓ Index created on date_of_birth
```

### Step 2: Restart Backend
Stop the backend (Ctrl+C) and restart it:
```powershell
uvicorn app.main:app --reload
```

### Step 3: Clear Frontend Cache
1. Stop frontend (Ctrl+C)
2. Delete build cache:
   ```powershell
   cd frontend
   Remove-Item -Recurse -Force .vite
   ```
3. Restart frontend:
   ```powershell
   npm run dev
   ```

### Step 4: Clear Browser Cache
**In Chrome/Edge:**
1. Open DevTools (F12)
2. Right-click refresh button
3. Click "Empty Cache and Hard Reload"

**Or use Incognito Mode:**
- Ctrl+Shift+N (Windows)
- Cmd+Shift+N (Mac)

### Step 5: Test Registration
1. Go to registration page
2. You should see:
   - ✅ State dropdown (all states)
   - ✅ District dropdown (updates when state changes)
   - ✅ Date of birth: Day/Month/Year dropdowns
   - ✅ Village/town text input
   - ✅ PIN code field (6 digits required)
   - ✅ Email field (optional)

## Troubleshooting:

### Backend still crashing?
- Check migration was applied: Look for success message
- Check database has columns: Run `\d sahayak_accounts` in psql

### Frontend still showing old form?
- Hard refresh: Ctrl+Shift+R
- Clear .vite folder
- Try incognito window
- Check browser console for errors

### Validation errors?
- Date of birth: Must be YYYY-MM-DD format (handled automatically)
- PIN code: Must be exactly 6 digits
- Email: Must be valid format (optional)

## Files Changed:
- `backend/app/auth/models.py` - Added date_of_birth, pin_code, email columns
- `backend/app/auth/schemas.py` - Updated validation
- `backend/app/auth/routes.py` - Handle new fields
- `frontend/src/components/Onboarding.tsx` - New form with dropdowns
- `frontend/src/data/indiaStatesDistricts.ts` - State/district data
- `frontend/src/types/api.ts` - Updated TypeScript types

## Database Schema:
```sql
ALTER TABLE sahayak_accounts ADD COLUMN date_of_birth DATE;
ALTER TABLE sahayak_accounts ADD COLUMN pin_code VARCHAR(6);
ALTER TABLE sahayak_accounts ADD COLUMN email VARCHAR(254);
CREATE INDEX idx_sahayak_accounts_dob ON sahayak_accounts(date_of_birth);
```
