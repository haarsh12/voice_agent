-- Migration: Add pin_code and email fields to sahayak_accounts table
-- Date: 2026-10-02
-- Description: Add optional PIN code (6 digits) and email address fields for user profiles

-- Add pin_code column (6 digits)
ALTER TABLE sahayak_accounts 
ADD COLUMN IF NOT EXISTS pin_code VARCHAR(6);

-- Add email column
ALTER TABLE sahayak_accounts 
ADD COLUMN IF NOT EXISTS email VARCHAR(254);

-- Add comment for documentation
COMMENT ON COLUMN sahayak_accounts.pin_code IS 'Optional 6-digit postal PIN code';
COMMENT ON COLUMN sahayak_accounts.email IS 'Optional email address (normalized to lowercase)';
