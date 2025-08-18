-- Add skill_type column to setups table
-- Run this SQL in your Supabase SQL Editor

ALTER TABLE setups 
ADD COLUMN skill_type VARCHAR(20) DEFAULT '';

-- Add comment for documentation
COMMENT ON COLUMN setups.skill_type IS 'スキルタイプ: skill_1(Q), skill_2(E), skill_3(C), ult(X)';

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_setups_skill_type ON setups(skill_type);

-- Optional: Update existing records to have empty skill_type
-- UPDATE setups SET skill_type = '' WHERE skill_type IS NULL;