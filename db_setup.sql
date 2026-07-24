-- 1. สร้างตาราง time_slots เพื่อตรวจสอบสถานะและล็อกช่วงเวลาแยกตามแผนก
CREATE TABLE IF NOT EXISTS time_slots (
    id SERIAL PRIMARY KEY,
    department VARCHAR(50) NOT NULL DEFAULT 'dental', -- 'dental', 'thai_traditional', 'physical_therapy'
    slot_date DATE NOT NULL,
    slot_time TIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available', -- 'available', 'booked'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_dept_slot UNIQUE (department, slot_date, slot_time)
);

-- รองรับการ Migration ตารางเดิม (ถ้ามี)
ALTER TABLE time_slots DROP CONSTRAINT IF EXISTS unique_slot;
ALTER TABLE time_slots ADD COLUMN IF NOT EXISTS department VARCHAR(50) NOT NULL DEFAULT 'dental';
ALTER TABLE time_slots DROP CONSTRAINT IF EXISTS unique_dept_slot;
ALTER TABLE time_slots ADD CONSTRAINT unique_dept_slot UNIQUE (department, slot_date, slot_time);


-- 2. สร้างตาราง appointments เพื่อบันทึกข้อมูลนัดหมายผู้เข้าใช้บริการ
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    department VARCHAR(50) NOT NULL DEFAULT 'dental', -- 'dental', 'thai_traditional', 'physical_therapy'
    user_id VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    cid VARCHAR(13) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    note TEXT,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- รองรับการ Migration ตารางเดิม
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS department VARCHAR(50) NOT NULL DEFAULT 'dental';
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN DEFAULT FALSE;


-- 3. สร้างตารางเก็บรายการบริการ แยกตามแต่ละแผนก
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    department VARCHAR(50) NOT NULL DEFAULT 'dental', -- 'dental', 'thai_traditional', 'physical_therapy'
    title VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(20) DEFAULT '🦷',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_dept_service UNIQUE (department, title)
);

-- รองรับการ Migration ตารางเดิม
ALTER TABLE services DROP CONSTRAINT IF EXISTS services_title_key;
ALTER TABLE services ADD COLUMN IF NOT EXISTS department VARCHAR(50) NOT NULL DEFAULT 'dental';
ALTER TABLE services DROP CONSTRAINT IF EXISTS unique_dept_service;
ALTER TABLE services ADD CONSTRAINT unique_dept_service UNIQUE (department, title);


-- 4. ล้าง/ใส่ข้อมูลตั้งต้นของทั้ง 3 แผนก
INSERT INTO services (department, title, description, icon) VALUES
-- แผนกทันตกรรม (Dental)
('dental', 'ตรวจสุขภาพช่องปาก', 'ตรวจเช็กฟันผุ สุขภาพเหงือก และคำแนะนำในการดูแลฟัน', '🦷🔍'),
('dental', 'อุดฟัน', 'อุดช่องว่างฟันผุด้วยวัสดุอุดฟันมาตรฐาน', '🦷💎'),
('dental', 'ถอนฟัน', 'ถอนฟันที่มีปัญหา แตกหัก หรือผุมาก', '🦷🩹'),
('dental', 'ขูดหินปูน', 'ทำความสะอาดคราบหินปูนและคราบสกปรกบนผิวฟัน', '🦷✨'),
('dental', 'อื่นๆ (ระบุ)', 'บริการทันตกรรมอื่นๆ หรือตามที่แพทย์แนะนำ', '📝'),

-- แผนกแพทย์แผนไทย (Thai Traditional Medicine)
('thai_traditional', 'นวดแผนไทย', 'นวดฟื้นฟูอาการปวดเมื่อยล้าตามส่วนต่างๆ ของร่างกาย', '💆‍♂️'),
('thai_traditional', 'ประคบสมุนไพร', 'ประคบร้อนด้วยลูกประคบสมุนไพรเพื่อลดอาการอักเสบและกระจายโลหิต', '🍃'),
('thai_traditional', 'อบไอน้ำสมุนไพร', 'อบผิวอบตัวด้วยไอน้ำสมุนไพรบำบัดเพื่อสุขภาพและระบบหายใจ', '💨'),
('thai_traditional', 'พอกเข่าสมุนไพร', 'พอกสมุนไพรลดอาการเสื่อม ปวดข้อเข่า หรืออักเสบเรื้อรัง', '🩹'),
('thai_traditional', 'อื่นๆ (ระบุ)', 'บริการแพทย์แผนไทยอื่นๆ หรือตามที่เจ้าหน้าที่วิเคราะห์', '📝'),

-- แผนกกายภาพบำบัด (Physical Therapy)
('physical_therapy', 'กายภาพบำบัดฟื้นฟู', 'ฟื้นฟูกล้ามเนื้อและข้อต่อหลังการผ่าตัด หรืออุบัติเหตุ', '🚶‍♂️'),
('physical_therapy', 'บำบัดและลดอาการปวด', 'บรรเทาอาการออฟฟิศซินโดรม ปวดหลัง ปวดคอเรื้อรังด้วยเครื่องมือและนวดบำบัด', '🩹'),
('physical_therapy', 'กายภาพบำบัดผู้ป่วยอัมพาต', 'ฝึกการเคลื่อนไหวและการทรงตัวสำหรับผู้ป่วยหลอดเลือดสมอง อัมพฤกษ์/อัมพาต', '♿'),
('physical_therapy', 'อื่นๆ (ระบุ)', 'บริการกายภาพบำบัดอื่นๆ ตามใบนัดของแพทย์', '📝')
ON CONFLICT (department, title) DO NOTHING;


-- 5. ฟังก์ชันจองคิวแบบอะตอมมิกที่แยกตามแผนก ป้องกันคิวชนกัน (Atomic Booking)
CREATE OR REPLACE FUNCTION book_appointment(
    p_department TEXT,
    p_user_id TEXT,
    p_name TEXT,
    p_phone TEXT,
    p_cid TEXT,
    p_service_type TEXT,
    p_appointment_date DATE,
    p_appointment_time TIME,
    p_note TEXT
) RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
DECLARE
    v_slot_id INT;
    v_status VARCHAR(20);
BEGIN
    -- ค้นหาและบันทึกล็อกสล็อตเวลาแยกตามแผนก
    INSERT INTO time_slots (department, slot_date, slot_time, status)
    VALUES (p_department, p_appointment_date, p_appointment_time, 'booked')
    ON CONFLICT (department, slot_date, slot_time) DO UPDATE
    SET status = 'booked'
    WHERE time_slots.status = 'available'
    RETURNING id, status INTO v_slot_id, v_status;

    IF v_slot_id IS NULL THEN
        RETURN QUERY SELECT FALSE, 'ช่วงเวลานี้ถูกจองไปแล้ว กรุณาเลือกเวลาอื่น'::TEXT;
        RETURN;
    END IF;

    -- บันทึกนัดหมายในตาราง appointments
    INSERT INTO appointments (
        department, user_id, name, phone, cid, service_type, appointment_date, appointment_time, note
    ) VALUES (
        p_department, p_user_id, p_name, p_phone, p_cid, p_service_type, p_appointment_date, p_appointment_time, p_note
    );

    RETURN QUERY SELECT TRUE, 'จองคิวสำเร็จ'::TEXT;
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT FALSE, SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- 6. ฟังก์ชันยกเลิกนัดหมายและคืนสถานะสล็อตเวลาว่างแยกแผนก
CREATE OR REPLACE FUNCTION cancel_appointment(
    p_appointment_id INT
) RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
DECLARE
    v_dept VARCHAR(50);
    v_date DATE;
    v_time TIME;
BEGIN
    SELECT department, appointment_date, appointment_time INTO v_dept, v_date, v_time
    FROM appointments
    WHERE id = p_appointment_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'ไม่พบข้อมูลการนัดหมายนี้'::TEXT;
        RETURN;
    END IF;

    -- ลบนัดหมาย
    DELETE FROM appointments WHERE id = p_appointment_id;

    -- คืนสถานะสล็อตเวลาของแผนกนั้นให้กลับเป็น 'available'
    UPDATE time_slots
    SET status = 'available'
    WHERE department = v_dept AND slot_date = v_date AND slot_time = v_time;

    RETURN QUERY SELECT TRUE, 'ยกเลิกการนัดหมายสำเร็จ'::TEXT;
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT FALSE, SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- 7. ฟังก์ชัน Wrapper เพื่อไม่ให้โค้ดเก่าเกิดข้อผิดพลาดในการเรียกใช้ (Backward Compatibility Wrapper)
CREATE OR REPLACE FUNCTION book_dental_appointment(
    p_user_id TEXT,
    p_name TEXT,
    p_phone TEXT,
    p_cid TEXT,
    p_service_type TEXT,
    p_appointment_date DATE,
    p_appointment_time TIME,
    p_note TEXT
) RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
BEGIN
    RETURN QUERY SELECT * FROM book_appointment('dental', p_user_id, p_name, p_phone, p_cid, p_service_type, p_appointment_date, p_appointment_time, p_note);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cancel_dental_appointment(
    p_appointment_id INT
) RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
BEGIN
    RETURN QUERY SELECT * FROM cancel_appointment(p_appointment_id);
END;
$$ LANGUAGE plpgsql;
