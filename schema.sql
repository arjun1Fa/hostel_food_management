CREATE TYPE user_role AS ENUM ('super_admin', 'hostel_admin', 'student');
CREATE TYPE meal_type AS ENUM ('breakfast', 'lunch', 'dinner', 'tea');
CREATE TYPE booking_status AS ENUM ('active', 'cancelled', 'consumed');
CREATE TYPE payment_status AS ENUM ('pending', 'verified', 'rejected');

CREATE TABLE hostels(
    hostel_id SERIAL primary key,
    name varchar (30) NOT NULL,
    invite_code varchar (20), UNIQUE NOT NULL,
    admin_id UUID
    

)