CREATE TYPE user_role AS ENUM ('super_admin', 'hostel_admin', 'student');
CREATE TYPE meal_type AS ENUM ('breakfast', 'lunch', 'dinner', 'tea');
CREATE TYPE booking_status AS ENUM ('active', 'cancelled', 'consumed');
CREATE TYPE payment_status AS ENUM ('pending', 'verified', 'rejected');

CREATE TABLE hostels(
    hostel_id SERIAL primary key,
    name varchar (30) NOT NULL,
    invite_code varchar (20) UNIQUE NOT NULL,
    admin_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc' :: text, now())
);

create table users(
    user_id SERIAL primary key,
    role
)
















-- ==========================================
-- 1. DEFINE CUSTOM TYPES (ENUMS)
-- ==========================================
CREATE TYPE user_role AS ENUM ('super_admin', 'hostel_admin', 'student');
CREATE TYPE meal_type AS ENUM ('breakfast', 'lunch', 'dinner', 'snack');
CREATE TYPE booking_status AS ENUM ('active', 'cancelled', 'consumed');
CREATE TYPE payment_status AS ENUM ('pending', 'verified', 'rejected');

-- ==========================================
-- 2. CREATE CORE TABLES
-- ==========================================

-- A. Hostels (Parent Container)
-- Note: admin_id is created but not linked yet to avoid circular dependency errors.
CREATE TABLE hostels (
    hostel_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    invite_code VARCHAR(20) UNIQUE NOT NULL,
    admin_id UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- B. Users (Linked to Supabase Auth & Hostels)
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'student',
    hostel_id INT REFERENCES hostels(hostel_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    current_balance DECIMAL(10, 2) DEFAULT 0.00,
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- C. Link Admin back to Hostel
ALTER TABLE hostels 
ADD CONSTRAINT fk_admin 
FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL;

-- D. Menus (Food Combos tied to Hostels)
CREATE TABLE menus (
    menu_id SERIAL PRIMARY KEY,
    hostel_id INT REFERENCES hostels(hostel_id) ON DELETE CASCADE,
    serve_date DATE NOT NULL,
    meal_time meal_type NOT NULL,
    combo_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    UNIQUE(hostel_id, serve_date, meal_time, combo_name) 
);

-- E. Bookings (The Food Ledger)
CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    menu_id INT REFERENCES menus(menu_id) ON DELETE CASCADE,
    booking_time TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    status booking_status DEFAULT 'active'
);

-- F. Payments (The OCR Ledger)
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_id VARCHAR(50) UNIQUE, -- Allowed to be null initially if OCR fails
    receipt_image_url TEXT NOT NULL,   -- Supabase Storage URL
    extracted_date DATE,
    status payment_status DEFAULT 'pending',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- ==========================================
-- 3. DEPLOY AUTOMATION LOGIC (TRIGGERS)
-- ==========================================

-- A. The Booking Deduction Trigger
CREATE OR REPLACE FUNCTION fn_deduct_balance_on_booking()
RETURNS TRIGGER AS $$
DECLARE
    meal_price DECIMAL(10,2);
BEGIN
    -- Fetch the price from the menus table
    SELECT price INTO meal_price 
    FROM menus 
    WHERE menu_id = NEW.menu_id;

    -- Deduct price from the user's balance
    UPDATE users 
    SET current_balance = current_balance - meal_price
    WHERE id = NEW.user_id;

    -- Enforce auto-ban if balance drops below 0
    UPDATE users
    SET is_banned = TRUE
    WHERE id = NEW.user_id AND current_balance < 0.00;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_booking_insert
AFTER INSERT ON bookings
FOR EACH ROW
EXECUTE FUNCTION fn_deduct_balance_on_booking();

-- B. The Payment Verification Trigger
CREATE OR REPLACE FUNCTION fn_credit_balance_on_verification()
RETURNS TRIGGER AS $$
BEGIN
    -- Act only when the Python OCR backend or Admin marks it verified
    IF NEW.status = 'verified' AND OLD.status = 'pending' THEN
        
        -- Add the approved amount
        UPDATE users 
        SET current_balance = current_balance + NEW.amount
        WHERE id = NEW.user_id;

        -- Lift the ban automatically if balance is positive
        UPDATE users
        SET is_banned = FALSE
        WHERE id = NEW.user_id AND current_balance >= 0.00;

    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_payment_update
AFTER UPDATE ON payments
FOR EACH ROW
EXECUTE FUNCTION fn_credit_balance_on_verification();