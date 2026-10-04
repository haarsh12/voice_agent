ALTER TABLE sahayak_accounts ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE sahayak_accounts ADD COLUMN IF NOT EXISTS pin_code VARCHAR(6);
ALTER TABLE sahayak_accounts ADD COLUMN IF NOT EXISTS email VARCHAR(254);
CREATE INDEX IF NOT EXISTS idx_sahayak_accounts_dob ON sahayak_accounts(date_of_birth);
