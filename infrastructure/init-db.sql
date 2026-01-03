-- Initialize database schema for PearlFlow
-- This script will be run automatically when PostgreSQL starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create tables (equivalent to SQLAlchemy models)
CREATE TABLE IF NOT EXISTS clinics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Australia/Sydney',
    settings JSONB DEFAULT '{}',
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    risk_profile JSONB DEFAULT '{}',
    ltv_score DECIMAL(10,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dentists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    specializations JSONB DEFAULT '[]',
    schedule JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS procedures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    default_duration_mins INTEGER DEFAULT 30,
    base_value DECIMAL(10,2) DEFAULT 0.0,
    priority_weight DECIMAL(5,2) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    dentist_id UUID REFERENCES dentists(id) ON DELETE SET NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_mins INTEGER NOT NULL,
    procedure_code VARCHAR(50) REFERENCES procedures(code),
    procedure_name VARCHAR(255),
    estimated_value DECIMAL(10,2) DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'BOOKED',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    state_snapshot JSONB DEFAULT '{}',
    current_node VARCHAR(100),
    messages JSONB DEFAULT '[]',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS move_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
    target_appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    incentive_type VARCHAR(50),
    incentive_value DECIMAL(10,2),
    move_score INTEGER,
    status VARCHAR(50) DEFAULT 'PENDING',
    offered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    content TEXT,
    is_approved BOOLEAN DEFAULT false,
    approved_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_appointments_clinic_date ON appointments(clinic_id, start_time);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_dentist ON appointments(dentist_id);
CREATE INDEX IF NOT EXISTS idx_sessions_clinic ON agent_sessions(clinic_id);
CREATE INDEX IF NOT EXISTS idx_sessions_patient ON agent_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_move_offers_original ON move_offers(original_appointment_id);
CREATE INDEX IF NOT EXISTS idx_move_offers_target ON move_offers(target_appointment_id);

-- Create a clinic for testing
INSERT INTO clinics (name, timezone, api_key, settings)
VALUES ('Test Dental Clinic', 'Australia/Sydney', 'test-api-key-123', '{"operating_hours": {"start": "09:00", "end": "17:00"}, "slot_duration": 30}')
ON CONFLICT (api_key) DO NOTHING;

-- Create a dentist for testing
INSERT INTO dentists (clinic_id, name, specializations, schedule)
SELECT id, 'Dr. Test Dentist', '["General", "Cosmetic"]', '{"monday": "09:00-17:00", "tuesday": "09:00-17:00", "wednesday": "09:00-17:00", "thursday": "09:00-17:00", "friday": "09:00-17:00"}'
FROM clinics WHERE api_key = 'test-api-key-123'
ON CONFLICT DO NOTHING;

-- Create some test procedures
INSERT INTO procedures (code, name, category, default_duration_mins, base_value, priority_weight) VALUES
('D1110', 'Prophylaxis (Cleaning)', 'Preventive', 30, 150.00, 0.5),
('D2140', 'Amalgam Filling (1 surface)', 'Restorative', 45, 200.00, 0.7),
('D2740', 'Crown (Porcelain)', 'Restorative', 90, 1200.00, 2.0),
('D6057', 'Dental Implant', 'Surgical', 120, 3000.00, 3.0)
ON CONFLICT (code) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_clinics_updated_at ON clinics;
CREATE TRIGGER update_clinics_updated_at BEFORE UPDATE ON clinics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_patients_updated_at ON patients;
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dentists_updated_at ON dentists;
CREATE TRIGGER update_dentists_updated_at BEFORE UPDATE ON dentists FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_appointments_updated_at ON appointments;
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_sessions_updated_at ON agent_sessions;
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON agent_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();