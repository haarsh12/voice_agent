-- Enhanced profile fields: pincode, caste_category and delete all old users.
-- These new fields are required for personalized assistance and grievance routing.
-- Run with a database administrator connection or the Supabase SQL editor.

-- Delete all existing accounts (cascades to grievances via FK restrict; clear grievances first)
-- !! WARNING: This permanently removes all users and their data. Intended. !!
DELETE FROM public.sahayak_grievance_events;
DELETE FROM public.sahayak_grievances;
DELETE FROM public.sahayak_webauthn_credentials;
DELETE FROM public.sahayak_webauthn_ceremonies;
DELETE FROM public.sahayak_otp_codes;
DELETE FROM public.sahayak_accounts;

-- Reset sequences so IDs restart from 1
ALTER SEQUENCE public.sahayak_accounts_id_seq RESTART WITH 1;
ALTER SEQUENCE public.sahayak_otp_codes_id_seq RESTART WITH 1;
ALTER SEQUENCE public.sahayak_grievance_events_id_seq RESTART WITH 1;

-- Add pincode column
ALTER TABLE public.sahayak_accounts
  ADD COLUMN IF NOT EXISTS pincode varchar(10);

-- Add caste_category column with allowed values
ALTER TABLE public.sahayak_accounts
  ADD COLUMN IF NOT EXISTS caste_category varchar(32)
    CHECK (caste_category IS NULL OR caste_category IN (
      'general',
      'obc',
      'sc',
      'st',
      'ews',
      'other'
    ));
