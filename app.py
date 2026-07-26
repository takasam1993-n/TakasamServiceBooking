import streamlit as st
import streamlit.components.v1 as components
import datetime
import requests
import json
import urllib.parse
import pandas as pd
from supabase import create_client, Client
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Set page config
st.set_page_config(
    page_title="ระบบลงทะเบียนนัดหมาย รพ.สต.ท่าเกษม",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom Styling (Theme colors matching the purple & clean flyer design)
st.markdown("""
<style>
    /* Main Layout */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Title and headers */
    .main-title {
        font-size: 2.2rem;
        color: #5A2A94;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #7B2CBF;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    /* Cards and Containers */
    .service-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #7B2CBF;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .service-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(123, 44, 191, 0.1);
    }
    
    /* Step Indicator styling */
    .step-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2.5rem;
        background-color: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .step-item {
        flex: 1;
        text-align: center;
        position: relative;
    }
    .step-item:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 20px;
        left: 50%;
        width: 100%;
        height: 3px;
        background-color: #E0E0E0;
        z-index: 1;
    }
    .step-item.active:not(:last-child)::after {
        background-color: #7B2CBF;
    }
    .step-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #E0E0E0;
        color: #6C757D;
        display: inline-flex;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        position: relative;
        z-index: 2;
        font-size: 1.1rem;
    }
    .step-item.active .step-icon {
        background-color: #7B2CBF;
        color: white;
        box-shadow: 0 0 12px rgba(123, 44, 191, 0.4);
    }
    .step-item.completed .step-icon {
        background-color: #2D6A4F;
        color: white;
    }
    .step-label {
        margin-top: 8px;
        font-size: 0.85rem;
        color: #6C757D;
        font-weight: 600;
    }
    .step-item.active .step-label {
        color: #7B2CBF;
    }
    .step-item.completed .step-label {
        color: #2D6A4F;
    }
    
    /* Custom buttons styling */
    div.stButton > button {
        background-color: #7B2CBF;
        color: white;
        border-radius: 10px;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #5A2A94;
        color: white;
        box-shadow: 0 4px 10px rgba(90, 42, 148, 0.3);
    }
    
    /* Success Box */
    .success-box {
        background-color: #D8F3DC;
        border-left: 6px solid #2D6A4F;
        color: #1B4332;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Dynamic CSS Theme Override -----------------
DEPT_THEMES = {
    "": {
        "primary": "#5A2A94",
        "primary_light": "#F3E8FF",
        "text_dark": "#240046",
        "gradient_bg": "linear-gradient(135deg, #F3E8FF 0%, #E9D8FD 100%)",
        "banner_img": "https://img.icons8.com/color/144/hospital.png",
        "title_thai": "ลงนัดออนไลน์",
        "footer_bg": "#5A2A94"
    },
    "dental": {
        "primary": "#7B2CBF",
        "primary_light": "#F3E8FF",
        "text_dark": "#240046",
        "gradient_bg": "linear-gradient(135deg, #F3E8FF 0%, #E9D8FD 100%)",
        "banner_img": "https://img.icons8.com/color/144/tooth.png",
        "title_thai": "ทันตกรรม",
        "footer_bg": "#5A2A94"
    },
    "thai_traditional": {
        "primary": "#2D6A4F",
        "primary_light": "#E8F5E9",
        "text_dark": "#1B4332",
        "gradient_bg": "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)",
        "banner_img": "https://img.icons8.com/color/144/mortar-and-pestle.png",
        "title_thai": "แพทย์แผนไทย",
        "footer_bg": "#1B4332"
    },
    "physical_therapy": {
        "primary": "#0077B6",
        "primary_light": "#E0F7FA",
        "text_dark": "#03045E",
        "gradient_bg": "linear-gradient(135deg, #E0F7FA 0%, #B2EBF2 100%)",
        "banner_img": "https://img.icons8.com/color/144/physical-therapy.png",
        "title_thai": "กายภาพบำบัด",
        "footer_bg": "#03045E"
    }
}



# ----------------- Supabase Connection & Configuration -----------------
# Check credentials in Streamlit secrets
supabase_url = st.secrets.get("SUPABASE_URL", "")
supabase_key = st.secrets.get("SUPABASE_KEY", "")
liff_id = st.secrets.get("LINE_LIFF_ID", "")
line_channel_access_token = st.secrets.get("LINE_CHANNEL_ACCESS_TOKEN", "")
google_calendar_id = st.secrets.get("GOOGLE_CALENDAR_ID", "")
google_calendar_id_dental = st.secrets.get("GOOGLE_CALENDAR_ID_DENTAL", "")
google_calendar_id_thai = st.secrets.get("GOOGLE_CALENDAR_ID_THAI", "")
google_calendar_id_physical = st.secrets.get("GOOGLE_CALENDAR_ID_PHYSICAL", "")

dept_cal_map = {
    "dental": google_calendar_id_dental,
    "thai_traditional": google_calendar_id_thai,
    "physical_therapy": google_calendar_id_physical
}

# Staff Portal Config
gcal_creds = st.secrets.get("google_calendar_credentials", {})
if isinstance(gcal_creds, dict):
    nested_pass = gcal_creds.get("STAFF_PASSWORD") or gcal_creds.get("staff_password")
else:
    nested_pass = getattr(gcal_creds, "STAFF_PASSWORD", None) or getattr(gcal_creds, "staff_password", None)
staff_password = str(st.secrets.get("STAFF_PASSWORD") or st.secrets.get("staff_password") or nested_pass or "1234").strip()

# LINE LIFF URL Config
liff_url = f"https://liff.line.me/{liff_id}" if (liff_id and "xxxxxxxx" not in liff_id) else "https://line.me"



is_demo = not (supabase_url and supabase_key and "xxxxxxxx" not in supabase_url)

@st.cache_resource
def get_supabase_client() -> Client:
    if is_demo:
        return None
    try:
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.sidebar.error(f"เชื่อมต่อฐานข้อมูลล้มเหลว: {e}")
        return None

supabase_client = get_supabase_client()

# ----------------- Mock Database for Demo Mode -----------------
if "mock_db" not in st.session_state:
    today_str = datetime.date.today().isoformat()
    tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    st.session_state.mock_db = {
        "appointments": [
            {
                "id": 1,
                "department": "dental",
                "user_id": "U1234567890",
                "name": "นายสมชาย เรียนดี",
                "phone": "0812345678",
                "cid": "1100702170369",
                "service_type": "ตรวจสุขภาพช่องปาก",
                "appointment_date": today_str,
                "appointment_time": "09:30",
                "note": "ตรวจฟันประจำปี",
                "reminder_sent": False
            },
            {
                "id": 2,
                "department": "dental",
                "user_id": "U0987654321",
                "name": "นางสาวสมศรี สมดี",
                "phone": "0898765432",
                "cid": "1200100234567",
                "service_type": "อุดฟัน",
                "appointment_date": today_str,
                "appointment_time": "14:00",
                "note": "วัสดุอุดเดิมหลุด",
                "reminder_sent": False
            },
            {
                "id": 3,
                "department": "thai_traditional",
                "user_id": "STAFF_MANUAL",
                "name": "นายขยัน หมั่นเพียร",
                "phone": "0855554444",
                "cid": "3200900123456",
                "service_type": "นวดแผนไทย",
                "appointment_date": tomorrow_str,
                "appointment_time": "10:00",
                "note": "โทรมาจองนวดตัว",
                "reminder_sent": False
            },
            {
                "id": 4,
                "department": "physical_therapy",
                "user_id": "U5555555555",
                "name": "นางกมลวรรณ รักเรียน",
                "phone": "0866667777",
                "cid": "1200500987654",
                "service_type": "กายภาพบำบัดฟื้นฟู",
                "appointment_date": tomorrow_str,
                "appointment_time": "15:30",
                "note": "ฟื้นฟูกล้ามเนื้อ",
                "reminder_sent": False
            }
        ],
        "services": [
            # Dental (ทันตกรรม)
            {"id": 1, "department": "dental", "title": "ตรวจสุขภาพช่องปาก", "description": "ตรวจเช็กฟันผุ สุขภาพเหงือก และคำแนะนำในการดูแลฟัน", "icon": "🦷🔍"},
            {"id": 2, "department": "dental", "title": "อุดฟัน", "description": "อุดช่องว่างฟันผุด้วยวัสดุอุดฟันมาตรฐาน", "icon": "🦷💎"},
            {"id": 3, "department": "dental", "title": "ถอนฟัน", "description": "ถอนฟันที่มีปัญหา แตกหัก หรือผุมาก", "icon": "🦷🩹"},
            {"id": 4, "department": "dental", "title": "ขูดหินปูน", "description": "ทำความสะอาดคราบหินปูนและคราบสกปรกบนผิวฟัน", "icon": "🦷✨"},
            {"id": 5, "department": "dental", "title": "อื่นๆ (ระบุ)", "description": "บริการทันตกรรมอื่นๆ หรือตามที่แพทย์แนะนำ", "icon": "📝"},
            
            # Thai Traditional Medicine (แพทย์แผนไทย)
            {"id": 6, "department": "thai_traditional", "title": "นวดแผนไทย", "description": "นวดฟื้นฟูอาการปวดเมื่อยล้าตามส่วนต่างๆ ของร่างกาย", "icon": "💆‍♂️"},
            {"id": 7, "department": "thai_traditional", "title": "ประคบสมุนไพร", "description": "ประคบร้อนด้วยลูกประคบสมุนไพรเพื่อลดอาการอักเสบและกระจายโลหิต", "icon": "🍃"},
            {"id": 8, "department": "thai_traditional", "title": "อบไอน้ำสมุนไพร", "description": "อบผิวอบตัวด้วยไอน้ำสมุนไพรบำบัดเพื่อสุขภาพและระบบหายใจ", "icon": "💨"},
            {"id": 9, "department": "thai_traditional", "title": "พอกเข่าสมุนไพร", "description": "พอกสมุนไพรลดอาการเสื่อม ปวดข้อเข่า หรืออักเสบเรื้อรัง", "icon": "🩹"},
            {"id": 10, "department": "thai_traditional", "title": "อื่นๆ (ระบุ)", "description": "บริการแพทย์แผนไทยอื่นๆ หรือตามที่เจ้าหน้าที่วิเคราะห์", "icon": "📝"},
            
            # Physical Therapy (กายภาพบำบัด)
            {"id": 11, "department": "physical_therapy", "title": "กายภาพบำบัดฟื้นฟู", "description": "ฟื้นฟูกล้ามเนื้อและข้อต่อหลังการผ่าตัด หรืออุบัติเหตุ", "icon": "🚶‍♂️"},
            {"id": 12, "department": "physical_therapy", "title": "บำบัดและลดอาการปวด", "description": "บรรเทาอาการออฟฟิศซินโดรม ปวดหลัง ปวดคอเรื้อรังด้วยเครื่องมือและนวดบำบัด", "icon": "🩹"},
            {"id": 13, "department": "physical_therapy", "title": "กายภาพบำบัดผู้ป่วยอัมพาต", "description": "ฝึกการเคลื่อนไหวและการทรงตัวสำหรับผู้ป่วยหลอดเลือดสมอง อัมพฤกษ์/อัมพาต", "icon": "♿"},
            {"id": 14, "department": "physical_therapy", "title": "อื่นๆ (ระบุ)", "description": "บริการกายภาพบำบัดอื่นๆ ตามใบนัดของแพทย์", "icon": "📝"}
        ],
        "time_slots": {
            "dental": {
                today_str: {
                    "09:30": "booked",
                    "14:00": "booked"
                },
                tomorrow_str: {
                    "10:00": "booked",
                    "15:30": "booked"
                }
            },
            "thai_traditional": {
                tomorrow_str: {
                    "10:00": "booked"
                }
            },
            "physical_therapy": {}
        }
    }

# ----------------- Session State Initialization -----------------
if "selected_dept" not in st.session_state:
    st.session_state.selected_dept = ""  # '', 'dental', 'thai_traditional', 'physical_therapy'
if "step" not in st.session_state:
    st.session_state.step = 1  # Step 1: Select Service
if "selected_service" not in st.session_state:
    st.session_state.selected_service = ""
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()
if "selected_time" not in st.session_state:
    st.session_state.selected_time = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_phone" not in st.session_state:
    st.session_state.user_phone = ""
if "user_cid" not in st.session_state:
    st.session_state.user_cid = ""
if "user_note" not in st.session_state:
    st.session_state.user_note = ""
if "line_user_id" not in st.session_state:
    st.session_state.line_user_id = "U999988887777666655554444"  # กำหนดสิทธิ์จำลองอัตโนมัติเพื่อความสะดวก
if "line_display_name" not in st.session_state:
    st.session_state.line_display_name = "คุณใจดี รักสุขภาพ"
if "line_picture_url" not in st.session_state:
    st.session_state.line_picture_url = ""
if "appointment_id" not in st.session_state:
    st.session_state.appointment_id = None

# Process URL parameters from LINE LIFF redirect
query_params = st.query_params
if "userId" in query_params:
    st.session_state.line_user_id = query_params["userId"]
    st.session_state.line_display_name = query_params.get("displayName", "ผู้ใช้งาน LINE")
    st.session_state.line_picture_url = query_params.get("pictureUrl", "")

# ตรวจสอบ Parameter เลือกแผนกอัตโนมัติจาก Rich Menu
if "dept" in query_params:
    dept_val = query_params["dept"].lower()
    if dept_val == "dental":
        st.session_state.selected_dept = "dental"
    elif dept_val in ("thai", "thai_traditional"):
        st.session_state.selected_dept = "thai_traditional"
    elif dept_val in ("physical", "physical_therapy"):
        st.session_state.selected_dept = "physical_therapy"

# ----------------- Helper Functions -----------------
def fetch_all_departments():
    """ดึงรายชื่อแผนกทั้งหมดที่มีการตั้งค่าในระบบ"""
    if "settings" not in st.session_state:
        get_settings("dental") # โหลดค่าตั้งต้นใส่ session_state.settings
        
    if is_demo:
        depts = []
        for key, val in st.session_state.settings.items():
            depts.append({
                "key": key,
                "display_name": val.get("display_name") or DEPT_THEMES.get(key, {}).get("title_thai", key),
                "theme_color": val.get("theme_color") or DEPT_THEMES.get(key, {}).get("primary", "#5A2A94"),
                "banner_img": val.get("banner_img") or DEPT_THEMES.get(key, {}).get("banner_img", "https://img.icons8.com/color/144/hospital.png")
            })
        return depts
        
    if not supabase_client:
        return []
        
    try:
        response = supabase_client.table("system_settings").select("*").execute()
        depts = []
        for row in response.data:
            key = row["department"]
            depts.append({
                "key": key,
                "display_name": row.get("display_name") or DEPT_THEMES.get(key, {}).get("title_thai", key),
                "theme_color": row.get("theme_color") or DEPT_THEMES.get(key, {}).get("primary", "#5A2A94"),
                "banner_img": row.get("banner_img") or DEPT_THEMES.get(key, {}).get("banner_img", "https://img.icons8.com/color/144/hospital.png")
            })
        return depts
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงข้อมูลแผนก: {e}")
        return []

def get_current_theme(selected_dept):
    """สร้างข้อมูลธีมของแผนกปัจจุบันแบบพลวัต โดยรวมจากฐานข้อมูลและค่าคอนฟิก"""
    base_theme = {
        "primary": "#5A2A94",
        "primary_light": "#F3E8FF",
        "text_dark": "#240046",
        "gradient_bg": "linear-gradient(135deg, #F3E8FF 0%, #E9D8FD 100%)",
        "banner_img": "https://img.icons8.com/color/144/hospital.png",
        "title_thai": "ลงนัดออนไลน์",
        "footer_bg": "#5A2A94"
    }
    
    if not selected_dept:
        return base_theme
        
    settings = get_settings(selected_dept)
    orig_theme = DEPT_THEMES.get(selected_dept, {})
    
    primary_color = settings.get("theme_color") or orig_theme.get("primary") or "#5A2A94"
    banner_img = settings.get("banner_img") or orig_theme.get("banner_img") or "https://img.icons8.com/color/144/hospital.png"
    display_name = settings.get("display_name") or orig_theme.get("title_thai") or selected_dept
    
    primary_light = orig_theme.get("primary_light") or "#F3E8FF"
    text_dark = orig_theme.get("text_dark") or "#240046"
    gradient_bg = orig_theme.get("gradient_bg") or f"linear-gradient(135deg, {primary_color}1A 0%, {primary_color}33 100%)"
    footer_bg = primary_color
    
    return {
        "primary": primary_color,
        "primary_light": primary_light,
        "text_dark": text_dark,
        "gradient_bg": gradient_bg,
        "banner_img": banner_img,
        "title_thai": display_name,
        "footer_bg": footer_bg
    }

def get_settings(dept):
    """ดึงข้อมูลการตั้งค่าสำหรับแผนกที่ระบุ (หรือแผนก Dental เป็นหลักถ้าไม่ระบุ)"""
    if "settings" not in st.session_state:
        # กำหนดค่าเริ่มต้นใน session_state
        st.session_state.settings = {
            "dental": {
                "booking_range_days": 30,
                "working_days": [0, 1, 2, 3, 4], # Mon-Fri
                "closed_dates": [],
                "time_slots": ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"],
                "max_bookings_per_slot": 1,
                "slot_configs": [],
                "display_name": "แผนกทันตกรรม (Dental Care)",
                "theme_color": "#7B2CBF",
                "banner_img": "https://img.icons8.com/color/144/tooth.png"
            },
            "thai_traditional": {
                "booking_range_days": 30,
                "working_days": [0, 1, 2, 3, 4],
                "closed_dates": [],
                "time_slots": ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"],
                "max_bookings_per_slot": 1,
                "slot_configs": [],
                "display_name": "แผนกแพทย์แผนไทย (Traditional Thai Medicine)",
                "theme_color": "#2D6A4F",
                "banner_img": "https://img.icons8.com/color/144/mortar-and-pestle.png"
            },
            "physical_therapy": {
                "booking_range_days": 30,
                "working_days": [0, 1, 2, 3, 4],
                "closed_dates": [],
                "time_slots": ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"],
                "max_bookings_per_slot": 1,
                "slot_configs": [],
                "display_name": "แผนกกายภาพบำบัด (Physical Therapy)",
                "theme_color": "#0077B6",
                "banner_img": "https://img.icons8.com/color/144/physical-therapy.png"
            }
        }
        
    if is_demo:
        return st.session_state.settings.get(dept, st.session_state.settings["dental"])
        
    if not supabase_client:
        return st.session_state.settings.get(dept, st.session_state.settings["dental"])
        
    try:
        # ดึงการตั้งค่าจาก Supabase
        response = supabase_client.table("system_settings").select("*").eq("department", dept).execute()
        if response.data:
            row = response.data[0]
            working_days = row.get("working_days", [0, 1, 2, 3, 4])
            closed_dates = row.get("closed_dates", [])
            time_slots = row.get("time_slots", ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"])
            time_slots = [":".join(s.split(":")[:2]) for s in time_slots]
            
            return {
                "booking_range_days": row.get("booking_range_days", 30),
                "working_days": working_days,
                "closed_dates": closed_dates,
                "time_slots": time_slots,
                "max_bookings_per_slot": row.get("max_bookings_per_slot", 1),
                "slot_configs": row.get("slot_configs", []),
                "display_name": row.get("display_name"),
                "theme_color": row.get("theme_color"),
                "banner_img": row.get("banner_img")
            }
        else:
            # หากไม่มีให้เพิ่มค่าตั้งต้นเข้าไป
            default_set = st.session_state.settings.get(dept, st.session_state.settings["dental"])
            supabase_client.table("system_settings").insert({
                "department": dept,
                "booking_range_days": default_set["booking_range_days"],
                "working_days": default_set["working_days"],
                "closed_dates": default_set["closed_dates"],
                "time_slots": default_set["time_slots"],
                "max_bookings_per_slot": default_set["max_bookings_per_slot"],
                "slot_configs": default_set.get("slot_configs", []),
                "display_name": default_set.get("display_name"),
                "theme_color": default_set.get("theme_color"),
                "banner_img": default_set.get("banner_img")
            }).execute()
            return default_set
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงการตั้งค่าจาก DB: {e}")
        return st.session_state.settings.get(dept, st.session_state.settings["dental"])

def update_settings_db(dept, booking_range_days, working_days, closed_dates, time_slots, max_bookings_per_slot, slot_configs=None, display_name=None, theme_color=None, banner_img=None):
    """อัปเดตการตั้งค่าของแผนก"""
    time_slots = [":".join(s.strip().split(":")[:2]) for s in time_slots if s.strip()]
    if slot_configs is None:
        slot_configs = []
    
    if is_demo:
        if "settings" not in st.session_state:
            get_settings(dept)
        
        curr = st.session_state.settings.get(dept, {})
        final_display_name = display_name if display_name is not None else curr.get("display_name", DEPT_THEMES.get(dept, {}).get("title_thai", dept))
        final_theme_color = theme_color if theme_color is not None else curr.get("theme_color", DEPT_THEMES.get(dept, {}).get("primary", "#5A2A94"))
        final_banner_img = banner_img if banner_img is not None else curr.get("banner_img", DEPT_THEMES.get(dept, {}).get("banner_img", "https://img.icons8.com/color/144/hospital.png"))

        st.session_state.settings[dept] = {
            "booking_range_days": int(booking_range_days),
            "working_days": [int(d) for d in working_days],
            "closed_dates": [str(d) for d in closed_dates],
            "time_slots": time_slots,
            "max_bookings_per_slot": int(max_bookings_per_slot),
            "slot_configs": slot_configs,
            "display_name": final_display_name,
            "theme_color": final_theme_color,
            "banner_img": final_banner_img
        }
        return True, "อัปเดตการตั้งค่าสำเร็จ (โหมดสาธิต)"
        
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
        
    try:
        response = supabase_client.table("system_settings").select("*").eq("department", dept).execute()
        
        if response.data:
            curr = response.data[0]
        else:
            curr = {}
            
        final_display_name = display_name if display_name is not None else curr.get("display_name", DEPT_THEMES.get(dept, {}).get("title_thai", dept))
        final_theme_color = theme_color if theme_color is not None else curr.get("theme_color", DEPT_THEMES.get(dept, {}).get("primary", "#5A2A94"))
        final_banner_img = banner_img if banner_img is not None else curr.get("banner_img", DEPT_THEMES.get(dept, {}).get("banner_img", "https://img.icons8.com/color/144/hospital.png"))

        data = {
            "department": dept,
            "booking_range_days": int(booking_range_days),
            "working_days": [int(d) for d in working_days],
            "closed_dates": [str(d) for d in closed_dates],
            "time_slots": time_slots,
            "max_bookings_per_slot": int(max_bookings_per_slot),
            "slot_configs": slot_configs,
            "display_name": final_display_name,
            "theme_color": final_theme_color,
            "banner_img": final_banner_img
        }
        if response.data:
            supabase_client.table("system_settings").update(data).eq("department", dept).execute()
        else:
            supabase_client.table("system_settings").insert(data).execute()
        return True, "อัปเดตการตั้งค่าเรียบร้อยแล้ว"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการบันทึกการตั้งค่า: {e}"

def create_department_db(key, display_name, theme_color, banner_img):
    key = key.strip().lower()
    display_name = display_name.strip()
    if not key or not display_name:
        return False, "กรุณากรอกรหัสแผนกและชื่อแผนกให้ครบถ้วน"
    
    if is_demo:
        if "settings" not in st.session_state:
            get_settings(key)
        if key in st.session_state.settings:
            return False, "มีรหัสแผนกนี้อยู่ในระบบแล้ว"
        st.session_state.settings[key] = {
            "booking_range_days": 30,
            "working_days": [0, 1, 2, 3, 4],
            "closed_dates": [],
            "time_slots": ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"],
            "max_bookings_per_slot": 1,
            "slot_configs": [],
            "display_name": display_name,
            "theme_color": theme_color,
            "banner_img": banner_img
        }
        return True, "เพิ่มแผนกใหม่ในระบบสาธิตสำเร็จ"
        
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
        
    try:
        res = supabase_client.table("system_settings").select("id").eq("department", key).execute()
        if res.data:
            return False, "มีรหัสแผนกนี้อยู่ในระบบแล้ว"
            
        supabase_client.table("system_settings").insert({
            "department": key,
            "display_name": display_name,
            "theme_color": theme_color,
            "banner_img": banner_img,
            "booking_range_days": 30,
            "working_days": [0, 1, 2, 3, 4],
            "closed_dates": [],
            "time_slots": ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"],
            "max_bookings_per_slot": 1,
            "slot_configs": []
        }).execute()
        return True, "เพิ่มแผนกใหม่ในระบบสำเร็จ"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาด: {e}"

def update_department_db(key, display_name, theme_color, banner_img):
    display_name = display_name.strip()
    if not display_name:
        return False, "กรุณากรอกชื่อแผนก"
        
    if is_demo:
        if "settings" not in st.session_state:
            get_settings(key)
        if key not in st.session_state.settings:
            return False, "ไม่พบข้อมูลแผนกนี้"
        st.session_state.settings[key]["display_name"] = display_name
        st.session_state.settings[key]["theme_color"] = theme_color
        st.session_state.settings[key]["banner_img"] = banner_img
        return True, "แก้ไขข้อมูลแผนกในระบบสาธิตสำเร็จ"
        
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
        
    try:
        supabase_client.table("system_settings").update({
            "display_name": display_name,
            "theme_color": theme_color,
            "banner_img": banner_img
        }).eq("department", key).execute()
        return True, "แก้ไขข้อมูลแผนกสำเร็จ"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาด: {e}"

def delete_department_db(key):
    if is_demo:
        if "settings" not in st.session_state:
            get_settings(key)
        if key in st.session_state.settings:
            del st.session_state.settings[key]
            if "services" in st.session_state.mock_db:
                st.session_state.mock_db["services"] = [s for s in st.session_state.mock_db["services"] if s.get("department") != key]
            return True, "ลบแผนกและข้อมูลบริการที่เกี่ยวข้องสำเร็จ (ระบบสาธิต)"
        return False, "ไม่พบแผนกที่ต้องการลบ"
        
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
        
    try:
        supabase_client.table("system_settings").delete().eq("department", key).execute()
        supabase_client.table("services").delete().eq("department", key).execute()
        supabase_client.table("time_slots").delete().eq("department", key).execute()
        return True, "ลบแผนกและข้อมูลการตั้งค่าทั้งหมดของแผนกนี้เรียบร้อยแล้ว"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการลบแผนก: {e}"

# Determine current selected department or fallback
selected_dept = st.session_state.get("selected_dept", "")
theme = get_current_theme(selected_dept)

# Override CSS properties based on current theme
st.markdown(f"""
<style>
    .main-title {{
        color: {theme['primary']} !important;
    }}
    .sub-title {{
        color: {theme['primary']} !important;
    }}
    .service-card {{
        border-left: 5px solid {theme['primary']} !important;
    }}
    .step-item.active::after {{
        background-color: {theme['primary']} !important;
    }}
    .step-item.active .step-icon {{
        background-color: {theme['primary']} !important;
        box-shadow: 0 0 12px {theme['primary']}80 !important;
    }}
    .step-item.active .step-label {{
        color: {theme['primary']} !important;
    }}
    div.stButton > button {{
        background-color: {theme['primary']} !important;
    }}
    div.stButton > button:hover {{
        background-color: {theme['text_dark']} !important;
        box-shadow: 0 4px 10px {theme['text_dark']}80 !important;
    }}
</style>
""", unsafe_allow_html=True)

def format_thai_date(date_obj):
    """แปลงวันที่แบบ Python ให้เป็นภาษาไทย เช่น 12 มิถุนายน 2567 (พุธ)"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.date.fromisoformat(date_obj)
        except Exception:
            return date_obj
            
    thai_months = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    thai_days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    
    day = date_obj.day
    month = thai_months[date_obj.month]
    year = date_obj.year + 543
    day_of_week = thai_days[date_obj.weekday()]
    
    return f"{day} {month} {year} ({day_of_week})"

def validate_thai_cid(cid):
    """ตรวจสอบเลขบัตรประจำตัวประชาชน 13 หลัก"""
    if not cid or len(cid) != 13 or not cid.isdigit():
        return False
    # สูตรคำนวณ Checksum บัตรประชาชนไทย
    sum_val = sum(int(cid[i]) * (13 - i) for i in range(12))
    check_digit = (11 - (sum_val % 11)) % 10
    return check_digit == int(cid[12])

def get_queue_number(app_time):
    """แปลงเวลาจองเป็นลำดับคิว โดยเริ่ม 08:30 เป็นคิวที่ 1"""
    t_clean = ":".join(str(app_time).split(":")[:2])
    slots = ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"]
    try:
        return slots.index(t_clean) + 1
    except ValueError:
        return 1

def get_calendar_service():
    """สร้าง Google Calendar API Service จากคีย์ลับใน secrets"""
    creds_info = st.secrets.get("google_calendar_credentials", None)
    if not creds_info:
        return None
    try:
        creds_dict = dict(creds_info)
        if "private_key" in creds_dict:
            pk_val = creds_dict["private_key"]
            if pk_val.startswith("-----BEGIN PRIVATE KEY-----\\nn"):
                pk_val = pk_val.replace("-----BEGIN PRIVATE KEY-----\\nn", "-----BEGIN PRIVATE KEY-----\\n", 1)
            elif pk_val.startswith("-----BEGIN PRIVATE KEY-----\nn"):
                pk_val = pk_val.replace("-----BEGIN PRIVATE KEY-----\nn", "-----BEGIN PRIVATE KEY-----\n", 1)
            creds_dict["private_key"] = pk_val.replace("\\n", "\n")
            
        scopes = ['https://www.googleapis.com/auth/calendar']
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ Google Calendar API: {e}")
        return None

def create_gcal_event(dept, title, appointment_date, appointment_time, description, location):
    """บันทึกนัดหมายลงใน Google Calendar อัตโนมัติในเบื้องหลัง"""
    service = get_calendar_service()
    if not service:
        print("คำเตือน: ยังไม่ได้ตั้งค่า google_calendar_credentials จึงข้ามการบันทึกลงปฏิทินกลาง รพ.สต.")
        return None
        
    calendar_id = dept_cal_map.get(dept, google_calendar_id)
    if not calendar_id:
        print(f"คำเตือน: ไม่พบ Calendar ID สำหรับแผนก {dept} หรือปฏิทินกลาง จึงข้ามการบันทึก")
        return None
        
    # แปลงเวลา
    date_str = appointment_date.isoformat() if hasattr(appointment_date, "isoformat") else str(appointment_date)
    time_only = ":".join(appointment_time.split(":")[:2])
    
    # คำนวณเวลาสิ้นสุดนัดหมาย
    hour_str, min_str = time_only.split(":")
    start_dt_str = f"{date_str}T{hour_str}:{min_str}:00"
    
    start_time = datetime.datetime.combine(
        datetime.date.fromisoformat(date_str) if isinstance(appointment_date, (datetime.date, datetime.datetime)) else datetime.datetime.strptime(date_str, "%Y-%m-%d").date(),
        datetime.time(int(hour_str), int(min_str))
    )
    end_time = start_time + datetime.timedelta(minutes=30)
    end_dt_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    event = {
        'summary': title,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_dt_str,
            'timeZone': 'Asia/Bangkok',
        },
        'end': {
            'dateTime': end_dt_str,
            'timeZone': 'Asia/Bangkok',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 30},
            ],
        },
    }
    
    try:
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"บันทึกคิวลง Google Calendar กลางเรียบร้อยแล้ว: {event_result.get('htmlLink')}")
        return event_result.get('htmlLink')
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการบันทึกคิวลง Google Calendar: {e}")
        return None

def get_booked_slots(date_obj, dept, selected_service=None):
    """ดึงเวลาที่ถูกจองไปแล้วในวันที่เลือกของแผนกที่ระบุโดยคำนวณตามจำนวนสูงสุดที่รับได้และกฎบริการรักษา"""
    date_str = date_obj.isoformat()
    dept_settings = get_settings(dept)
    slot_configs = dept_settings.get("slot_configs", [])
    
    slot_counts = {}
    if is_demo:
        appointments = st.session_state.mock_db.get("appointments", [])
        for app in appointments:
            if app.get("department") == dept and app.get("appointment_date") == date_str:
                t = app.get("appointment_time")
                t_formatted = ":".join(t.split(":")[:2])
                slot_counts[t_formatted] = slot_counts.get(t_formatted, 0) + 1
    else:
        if not supabase_client:
            return []
        try:
            response = supabase_client.table("appointments")\
                .select("appointment_time")\
                .eq("department", dept)\
                .eq("appointment_date", date_str)\
                .execute()
            for row in response.data:
                time_raw = row["appointment_time"]
                time_formatted = ":".join(time_raw.split(":")[:2])
                slot_counts[time_formatted] = slot_counts.get(time_formatted, 0) + 1
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลเวลา: {e}")
            return []

    booked = []
    if slot_configs:
        # ตรวจสอบตามกฎของรอบสล็อตเวลาเฉพาะ
        for config in slot_configs:
            time_str = config.get("time")
            capacity = config.get("capacity", 1)
            allowed_services = config.get("allowed_services", [])
            
            # ก. ตรวจสอบว่าจำนวนคิวเต็มหรือยัง
            count = slot_counts.get(time_str, 0)
            if count >= capacity:
                booked.append(time_str)
                continue
                
            # ข. ตรวจสอบว่าบริการที่เลือกได้รับอนุญาตในเวลานี้หรือไม่
            if selected_service and allowed_services:
                allowed_cleaned = [s.strip() for s in allowed_services if s.strip()]
                if allowed_cleaned and selected_service.strip() not in allowed_cleaned and "ทุกบริการ" not in allowed_cleaned:
                    booked.append(time_str)
    else:
        # Fallback กรณีใช้ระบบเก่า (ไม่มี slot_configs)
        max_bookings = dept_settings.get("max_bookings_per_slot", 1)
        for time_str, count in slot_counts.items():
            if count >= max_bookings:
                booked.append(time_str)
                
    return booked

def execute_booking(dept, user_id, name, phone, cid, service, app_date, app_time, note):
    """ส่งข้อมูลไปบันทึกด้วย RPC book_appointment ป้องกันคิวซ้ำแยกตามแผนก"""
    date_str = app_date.isoformat()
    time_str = f"{app_time}:00" # ส่งฟอร์แมต HH:MM:00
    
    if is_demo:
        # จำลองการตรวจสอบสล็อตโดยละเอียดตามกฎ slot_configs
        dept_settings = st.session_state.settings.get(dept, {})
        slot_configs = dept_settings.get("slot_configs", [])
        
        # 1. ค้นหาโควตาและเงื่อนไขเฉพาะของสล็อตนี้
        max_bookings = 1
        allowed_services = []
        found_slot = False
        for cfg in slot_configs:
            if cfg.get("time") == app_time:
                max_bookings = cfg.get("capacity", 1)
                allowed_services = cfg.get("allowed_services", [])
                found_slot = True
                break
        if not found_slot:
            max_bookings = dept_settings.get("max_bookings_per_slot", 1)

        # 2. ตรวจสอบความถูกต้องของประเภทบริการ
        if allowed_services:
            allowed_cleaned = [s.strip() for s in allowed_services if s.strip()]
            if allowed_cleaned and service.strip() not in allowed_cleaned and "ทุกบริการ" not in allowed_cleaned:
                return False, "รอบเวลานี้ไม่เปิดให้บริการสำหรับประเภทบริการที่เลือก"

        # 3. นับจำนวนการจองใน mock db
        current_bookings = 0
        appointments = st.session_state.mock_db.get("appointments", [])
        for app in appointments:
            if app.get("department") == dept and app.get("appointment_date") == date_str and ":".join(app.get("appointment_time").split(":")[:2]) == app_time:
                current_bookings += 1
                
        if current_bookings >= max_bookings:
            return False, "ช่วงเวลานี้ถูกจองเต็มโควตาแล้ว"

        if dept not in st.session_state.mock_db["time_slots"]:
            st.session_state.mock_db["time_slots"][dept] = {}
        if date_str not in st.session_state.mock_db["time_slots"][dept]:
            st.session_state.mock_db["time_slots"][dept][date_str] = {}
            
        # บันทึกจองเวลา
        st.session_state.mock_db["time_slots"][dept][date_str][app_time] = "booked"
        # บันทึกนัดหมาย
        app_id = len(st.session_state.mock_db["appointments"]) + 1
        st.session_state.mock_db["appointments"].append({
            "id": app_id,
            "department": dept,
            "user_id": user_id,
            "name": name,
            "phone": phone,
            "cid": cid,
            "service_type": service,
            "appointment_date": date_str,
            "appointment_time": app_time,
            "note": note,
            "reminder_sent": False
        })
        st.session_state.appointment_id = f"DEMO-{app_id:04d}"
        
        # ลองบันทึก Google Calendar ในโหมดเดโม (ถ้าตั้งค่า Service Account ไว้)
        try:
            q_num = get_queue_number(app_time)
            cal_desc = f"รหัสอ้างอิงการจองคิว: คิวที่ {q_num} (อ้างอิง: DEMO-{app_id:04d})\nผู้รับบริการ: {name}\nเบอร์โทรศัพท์: {phone}\nอาการ/หมายเหตุ: {note}\n\nจองคิวออนไลน์ผ่านระบบ รพ.สต.ท่าเกษม"
            dept_title = DEPT_THEMES.get(dept, {}).get("title_thai", "บริการทั่วไป")
            create_gcal_event(
                dept=dept,
                title=f"นัดหมาย{dept_title} [{name}]: {service}",
                appointment_date=app_date,
                appointment_time=app_time,
                description=cal_desc,
                location="รพ.สต.ท่าเกษม อ.เมืองสระแก้ว จ.สระแก้ว"
            )
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการบันทึกปฏิทินเดโม: {e}")
            
        return True, "จองคิวสำเร็จ (โหมดสาธิต)"

    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
        
    try:
        # เรียกใช้งาน RPC ฟังก์ชัน book_appointment ใน Supabase
        response = supabase_client.rpc(
            "book_appointment",
            {
                "p_department": dept,
                "p_user_id": user_id,
                "p_name": name,
                "p_phone": phone,
                "p_cid": cid,
                "p_service_type": service,
                "p_appointment_date": date_str,
                "p_appointment_time": time_str,
                "p_note": note
            }
        ).execute()
        
        result = response.data[0] if response.data else {"success": False, "message": "ไม่ได้รับการตอบกลับจากเซิร์ฟเวอร์"}
        success = result.get("success", False)
        if success:
            try:
                # ค้นหารหัสการนัดหมายล่าสุดที่เราเพิ่งจองเข้าไปจากฐานข้อมูล Supabase
                app_res = supabase_client.table("appointments")\
                    .select("id")\
                    .eq("department", dept)\
                    .eq("cid", cid)\
                    .eq("appointment_date", date_str)\
                    .eq("appointment_time", time_str)\
                    .order("id", desc=True)\
                    .limit(1)\
                    .execute()
                if app_res.data:
                    app_id_val = app_res.data[0]["id"]
                    st.session_state.appointment_id = app_id_val
                    
                    # บันทึกคิวลง Google Calendar กลางอัตโนมัติ
                    try:
                        q_num = get_queue_number(app_time)
                        cal_desc = f"รหัสอ้างอิงการจองคิว: คิวที่ {q_num} (อ้างอิง: #{app_id_val})\nผู้รับบริการ: {name}\nเบอร์โทรศัพท์: {phone}\nอาการ/หมายเหตุ: {note}\n\nจองคิวออนไลน์ผ่านระบบ รพ.สต.ท่าเกษม"
                        dept_title = DEPT_THEMES.get(dept, {}).get("title_thai", "บริการทั่วไป")
                        create_gcal_event(
                            dept=dept,
                            title=f"นัดหมาย{dept_title} [{name}]: {service}",
                            appointment_date=app_date,
                            appointment_time=app_time,
                            description=cal_desc,
                            location="รพ.สต.ท่าเกษม อ.เมืองสระแก้ว จ.สระแก้ว"
                        )
                    except Exception as cal_ex:
                        print(f"เกิดข้อผิดพลาดในการบันทึกปฏิทินกลาง: {cal_ex}")
            except Exception as query_ex:
                print(f"เกิดข้อผิดพลาดในการดึงรหัสการนัดหมาย / บันทึกปฏิทิน: {query_ex}")
        return success, result.get("message", "เกิดข้อผิดพลาดไม่ทราบสาเหตุ")
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการบันทึก: {e}"

def construct_dental_flex_payload(title, subtitle, service, app_date, app_time, name, dept):
    """สร้างโครงสร้าง JSON Flex Message ตามตัวอย่างใบประชาสัมพันธ์ของ รพ.สต.ท่าเกษม"""
    thai_date_str = format_thai_date(app_date)
    time_str = ":".join(str(app_time).split(":")[:2])
    q_num = get_queue_number(app_time)
    
    DEPT_CONFIGS = {
        "dental": {
            "title_en": "ทันตกรรม",
            "bg_color": "#F3E8FF",
            "primary": "#7B2CBF",
            "primary_dark": "#5A2A94",
            "icon_url": "https://img.icons8.com/color/144/tooth.png",
            "logo_icon": "https://img.icons8.com/color/96/tooth.png",
            "slogan": "ใส่ใจสุขภาพ เคียงข้างประชาชน 💜",
            "note_icon": "https://img.icons8.com/color/96/appointment-reminders--v1.png",
            "text_color": "#5A2A94",
            "calendar_icon": "https://img.icons8.com/color/96/calendar--v1.png",
            "clock_icon": "https://img.icons8.com/color/96/clock--v1.png",
            "user_icon": "https://img.icons8.com/color/96/user-male-circle--v1.png"
        },
        "thai_traditional": {
            "title_en": "แพทย์แผนไทย",
            "bg_color": "#E8F5E9",
            "primary": "#2D6A4F",
            "primary_dark": "#1B4332",
            "icon_url": "https://img.icons8.com/color/144/mortar-and-pestle.png",
            "logo_icon": "https://img.icons8.com/color/96/mortar-and-pestle.png",
            "slogan": "ใส่ใจสุขภาพ เคียงข้างประชาชน 💚",
            "note_icon": "https://img.icons8.com/color/96/appointment-reminders--v1.png",
            "text_color": "#1B4332",
            "calendar_icon": "https://img.icons8.com/color/96/calendar--v1.png",
            "clock_icon": "https://img.icons8.com/color/96/clock--v1.png",
            "user_icon": "https://img.icons8.com/color/96/user-male-circle--v1.png"
        },
        "physical_therapy": {
            "title_en": "กายภาพบำบัด",
            "bg_color": "#E0F7FA",
            "primary": "#0077B6",
            "primary_dark": "#03045E",
            "icon_url": "https://img.icons8.com/color/144/physical-therapy.png",
            "logo_icon": "https://img.icons8.com/color/96/physical-therapy.png",
            "slogan": "ใส่ใจสุขภาพ เคียงข้างประชาชน 💙",
            "note_icon": "https://img.icons8.com/color/96/appointment-reminders--v1.png",
            "text_color": "#03045E",
            "calendar_icon": "https://img.icons8.com/color/96/calendar--v1.png",
            "clock_icon": "https://img.icons8.com/color/96/clock--v1.png",
            "user_icon": "https://img.icons8.com/color/96/user-male-circle--v1.png"
        }
    }
    
    cfg = DEPT_CONFIGS.get(dept, DEPT_CONFIGS["dental"])
    
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "horizontal",
            "backgroundColor": cfg["bg_color"],
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 7,
                    "contents": [
                        {
                            "type": "text",
                            "text": title,
                            "weight": "bold",
                            "size": "lg",
                            "color": cfg["primary"]
                        },
                        {
                            "type": "text",
                            "text": cfg["title_en"],
                            "weight": "bold",
                            "size": "xxl",
                            "color": cfg["primary_dark"],
                            "margin": "none"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "backgroundColor": cfg["primary"],
                            "cornerRadius": "15px",
                            "paddingStart": "8px",
                            "paddingEnd": "8px",
                            "paddingTop": "2px",
                            "paddingBottom": "2px",
                            "width": "110px",
                            "margin": "xs",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "รพ.สต.ท่าเกษม",
                                    "color": "#ffffff",
                                    "size": "xs",
                                    "weight": "bold",
                                    "align": "center"
                                }
                            ]
                        },
                        {
                            "type": "text",
                            "text": cfg["slogan"],
                            "size": "xxs",
                            "color": cfg["primary_dark"],
                            "margin": "xs",
                            "weight": "bold"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 3,
                    "alignment": "center",
                    "justifyContent": "center",
                    "contents": [
                        {
                            "type": "image",
                            "url": cfg["icon_url"],
                            "size": "full",
                            "aspectMode": "fit"
                        }
                    ]
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#ffffff",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "text",
                            "text": subtitle,
                            "weight": "bold",
                            "size": "md",
                            "color": "#240046"
                        },
                        {
                            "type": "text",
                            "text": "— อย่าลืมมาพบแพทย์ตามนัดนะคะ —",
                            "size": "xs",
                            "color": cfg["primary"],
                            "margin": "xs"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "md",
                    "color": cfg["bg_color"]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "alignItems": "center",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": cfg["calendar_icon"],
                                    "size": "xxs",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": "วันที่นัด",
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 3,
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": thai_date_str,
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": "#240046",
                                    "flex": 6,
                                    "wrap": True
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "alignItems": "center",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": cfg["clock_icon"],
                                    "size": "xxs",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": "เวลานัด",
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 3,
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": f"{time_str} น.",
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": "#240046",
                                    "flex": 6
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "alignItems": "center",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": "https://img.icons8.com/color/96/numbered-list.png",
                                    "size": "xxs",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": "ลำดับคิว",
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 3,
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": f"คิวที่ {q_num}",
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": cfg["primary"],
                                    "flex": 6
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "alignItems": "center",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": cfg["logo_icon"],
                                    "size": "xxs",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": "บริการ",
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 3,
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": service,
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": "#240046",
                                    "flex": 6,
                                    "wrap": True
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "alignItems": "center",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": cfg["user_icon"],
                                    "size": "xxs",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": "ชื่อผู้รับบริการ",
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 3,
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": name,
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": "#240046",
                                    "flex": 6,
                                    "wrap": True
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "backgroundColor": cfg["bg_color"],
                    "cornerRadius": "10px",
                    "paddingAll": "12px",
                    "margin": "md",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "flex": 2,
                            "alignItems": "center",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": cfg["note_icon"],
                                    "size": "xs"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "flex": 8,
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "กรุณามาก่อนเวลานัด 15 นาที",
                                    "weight": "bold",
                                    "size": "xs",
                                    "color": cfg["primary"]
                                },
                                {
                                    "type": "text",
                                    "text": "หากไม่สามารถมาตามนัดได้ กรุณาแจ้งยกเลิกหรือเลื่อนนัดล่วงหน้า",
                                    "size": "xxs",
                                    "color": "#666666",
                                    "wrap": True,
                                    "margin": "xs"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": cfg["primary"],
                    "cornerRadius": "10px",
                    "paddingAll": "10px",
                    "margin": "md",
                    "action": {
                        "type": "uri",
                        "label": "ดูรายละเอียดการนัด",
                        "uri": liff_url
                    },
                    "contents": [
                        {
                            "type": "text",
                            "text": "ดูรายละเอียดการนัด   >",
                            "color": "#ffffff",
                            "weight": "bold",
                            "size": "sm",
                            "align": "center"
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "backgroundColor": cfg["primary_dark"],
            "paddingAll": "12px",
            "spacing": "sm",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 5,
                    "contents": [
                        {
                            "type": "text",
                            "text": "📍 รพ.สต.ท่าเกษม",
                            "color": "#ffffff",
                            "size": "xxs",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": "ต.ท่าเกษม อ.เมืองสระแก้ว จ.สระแก้ว",
                            "color": cfg["bg_color"],
                            "size": "xxs",
                            "wrap": True
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 5,
                    "contents": [
                        {
                            "type": "text",
                            "text": "📞 037-447-059",
                            "color": "#ffffff",
                            "size": "xxs",
                            "weight": "bold",
                            "align": "end"
                        },
                        {
                            "type": "text",
                            "text": "เวลาทำการ 08.30 - 16.30 น.",
                            "color": cfg["bg_color"],
                            "size": "xxs",
                            "align": "end"
                        }
                    ]
                }
            ]
        }
    }

def send_line_flex_message(user_id, service, app_date, app_time, name, dept):
    """ส่ง Flex Message ยืนยันการนัดหมายผ่าน LINE"""
    if not line_channel_access_token or "xxxxxxxx" in line_channel_access_token:
        st.info("💡 (โครงสร้าง Webhook) ระบบพร้อมเชื่อมต่อไปยัง LINE Messaging API เพื่อส่ง Flex Message คอนเฟิร์ม")
        return False
        
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_channel_access_token}"
    }
    
    flex_payload = construct_dental_flex_payload(
        title="ยืนยันการนัดหมาย",
        subtitle="ลงทะเบียนนัดหมายเรียบร้อยแล้วค่ะ",
        service=service,
        app_date=app_date,
        app_time=app_time,
        name=name,
        dept=dept
    )
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "flex",
                "altText": f"ยืนยันการนัดหมายนัดของแผนก รพ.สต.ท่าเกษม",
                "contents": flex_payload
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการส่ง LINE Flex Message: {e}")
        return False

def send_line_reminder_flex(user_id, service, app_date, app_time, name, dept):
    """ส่ง Flex Message แจ้งเตือนคนไข้ล่วงหน้า 1 ชั่วโมงผ่าน LINE"""
    if not line_channel_access_token or "xxxxxxxx" in line_channel_access_token:
        thai_date = format_thai_date(app_date)
        print(f"📡 [MOCK FLEX REMINDER] แผนก {dept} ส่งการ์ดแจ้งเตือนหา LINE ID: {user_id} | วันที่: {thai_date} | เวลา: {app_time} | คนไข้: {name}")
        return True
        
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_channel_access_token}"
    }
    
    flex_payload = construct_dental_flex_payload(
        title="แจ้งเตือนนัด",
        subtitle="ถึงเวลานัดของคุณแล้วค่ะ",
        service=service,
        app_date=app_date,
        app_time=app_time,
        name=name,
        dept=dept
    )
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "flex",
                "altText": f"แจ้งเตือนนัดนัดของแผนก รพ.สต.ท่าเกษม",
                "contents": flex_payload
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่ง LINE Flex Message แจ้งเตือน: {e}")
        return False

def fetch_services(dept=None):
    """ดึงรายการบริการตามแผนก เรียงตาม id"""
    if is_demo:
        services = st.session_state.mock_db.get("services", [])
        if dept:
            return [s for s in services if s.get("department") == dept]
        return services
    if not supabase_client:
        return []
    try:
        query = supabase_client.table("services").select("*")
        if dept:
            query = query.eq("department", dept)
        response = query.order("id", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงข้อมูลบริการ: {e}")
        return []

def add_service_db(dept, title, description, icon):
    """เพิ่มบริการใหม่แยกตามแผนก"""
    if is_demo:
        services = st.session_state.mock_db.get("services", [])
        new_id = max([s["id"] for s in services]) + 1 if services else 1
        services.append({
            "id": new_id,
            "department": dept,
            "title": title,
            "description": description,
            "icon": icon
        })
        return True, "เพิ่มบริการสำเร็จ (โหมดสาธิต)"
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
    try:
        response = supabase_client.table("services")\
            .insert({"department": dept, "title": title, "description": description, "icon": icon})\
            .execute()
        if response.data:
            return True, "เพิ่มบริการใหม่สำเร็จ"
        return False, "ไม่สามารถเพิ่มข้อมูลได้"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการเพิ่มบริการ: {e}"

def update_service_db(service_id, dept, title, description, icon):
    """แก้ไขบริการที่มีอยู่"""
    if is_demo:
        services = st.session_state.mock_db.get("services", [])
        for s in services:
            if str(s["id"]) == str(service_id):
                s["department"] = dept
                s["title"] = title
                s["description"] = description
                s["icon"] = icon
                return True, "แก้ไขบริการสำเร็จ (โหมดสาธิต)"
        return False, "ไม่พบบริการที่ต้องการแก้ไขในระบบจำลอง"
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
    try:
        response = supabase_client.table("services")\
            .update({"department": dept, "title": title, "description": description, "icon": icon})\
            .eq("id", int(service_id))\
            .execute()
        if response.data:
            return True, "แก้ไขข้อมูลบริการสำเร็จ"
        return False, "ไม่สามารถแก้ไขข้อมูลได้"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการแก้ไขบริการ: {e}"

def delete_service_db(service_id):
    """ลบบริการออกจากระบบ"""
    if is_demo:
        services = st.session_state.mock_db.get("services", [])
        service_to_delete = None
        for s in services:
            if str(s["id"]) == str(service_id):
                service_to_delete = s
                break
        if service_to_delete:
            services.remove(service_to_delete)
            return True, "ลบบริการสำเร็จ (โหมดสาธิต)"
        return False, "ไม่พบบริการที่ต้องการลบในระบบจำลอง"
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
    try:
        response = supabase_client.table("services")\
            .delete()\
            .eq("id", int(service_id))\
            .execute()
        if response.data:
            return True, "ลบข้อมูลบริการสำเร็จ"
        return False, "ไม่สามารถลบข้อมูลได้"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการลบบริการ: {e}"

def fetch_all_appointments():
    """ดึงรายการนัดหมายทั้งหมด เรียงตามวันและเวลา"""
    if is_demo:
        return st.session_state.mock_db["appointments"]
    if not supabase_client:
        return []
    try:
        response = supabase_client.table("appointments")\
            .select("*")\
            .order("appointment_date", desc=False)\
            .order("appointment_time", desc=False)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลนัดหมาย: {e}")
        return []

def cancel_appointment_db(app_id):
    """ยกเลิกนัดหมายและคืนสถานะสล็อตเวลา"""
    if is_demo:
        appointments = st.session_state.mock_db["appointments"]
        app_to_cancel = None
        for app in appointments:
            if str(app["id"]) == str(app_id):
                app_to_cancel = app
                break
        
        if not app_to_cancel:
            return False, "ไม่พบข้อมูลการนัดหมายที่เลือก"
        
        # ลบนัดหมายออก
        appointments.remove(app_to_cancel)
        
        # คืนค่าสล็อตเวลาตามแผนกที่ลงทะเบียน
        dept = app_to_cancel.get("department", "dental")
        date_str = app_to_cancel["appointment_date"]
        time_str = app_to_cancel["appointment_time"]
        if dept in st.session_state.mock_db["time_slots"]:
            if date_str in st.session_state.mock_db["time_slots"][dept]:
                if time_str in st.session_state.mock_db["time_slots"][dept][date_str]:
                    st.session_state.mock_db["time_slots"][dept][date_str].pop(time_str, None)
                
        return True, "ยกเลิกคิวนัดหมาย (โหมดสาธิต) สำเร็จ"
    
    if not supabase_client:
        return False, "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"
        
    try:
        response = supabase_client.rpc("cancel_appointment", {"p_appointment_id": int(app_id)}).execute()
        result = response.data[0] if response.data else {"success": False, "message": "ไม่มีการตอบสนองจากระบบ"}
        return result.get("success", False), result.get("message", "เกิดข้อผิดพลาด")
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการยกเลิก: {e}"

def send_line_push_message(user_id, message_text):
    """ส่ง Push Message คอนเฟิร์มหรือแจ้งเตือนไปยังผู้ใช้รายบุคคล"""
    if not line_channel_access_token or "xxxxxxxx" in line_channel_access_token:
        # บันทึก Log ในหน้าจอ Console
        print(f"📡 [MOCK PUSH] ส่งข้อความเตือนไปยัง LINE ID: {user_id} -> {message_text}")
        return True
        
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_channel_access_token}"
    }
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่ง LINE Push Message: {e}")
        return False

def run_reminder_check():
    """ตรวจสอบนัดหมายในอีก 1 ชั่วโมงข้างหน้า และส่ง LINE แจ้งเตือน"""
    now = datetime.datetime.now()
    today_str = now.date().isoformat()
    
    # คำนวณช่วงเวลาที่ต้องการเตือน (เริ่มจองระหว่าง 50 ถึง 70 นาทีข้างหน้า)
    time_min = (now + datetime.timedelta(minutes=50)).time()
    time_max = (now + datetime.timedelta(minutes=70)).time()
    
    if is_demo:
        # ตรวจสอบกับ Mock DB ใน st.session_state (รันปลอดภัยบน Main Thread เท่านั้น)
        appointments = st.session_state.mock_db.get("appointments", [])
        for app in appointments:
            if app.get("reminder_sent") == False and app.get("appointment_date") == today_str:
                try:
                    app_time_obj = datetime.datetime.strptime(app["appointment_time"], "%H:%M").time()
                    if time_min <= app_time_obj <= time_max:
                        user_id = app.get("user_id", "")
                        if user_id and user_id != "NON_LINE_USER":
                            send_line_reminder_flex(user_id, app["service_type"], app["appointment_date"], app["appointment_time"], app["name"], app.get("department", "dental"))
                            app["reminder_sent"] = True
                            st.sidebar.toast(f"🔔 แจ้งเตือนคิวล่วงหน้า: ส่งการ์ด LINE เตือนคุณ {app['name']} แล้ว")
                except Exception as e:
                    print(f"เกิดข้อผิดพลาดในการแปลงเวลาโหมดเดโม: {e}")
    else:
        # ตรวจสอบกับฐานข้อมูล Supabase จริง (รันได้บนทุก Thread)
        if not supabase_client:
            return
        try:
            response = supabase_client.table("appointments")\
                .select("*")\
                .eq("appointment_date", today_str)\
                .eq("reminder_sent", False)\
                .execute()
                
            for row in response.data:
                app_time_str = row["appointment_time"]
                try:
                    # แปลง "HH:MM:SS" หรือ "HH:MM"
                    app_time_obj = datetime.datetime.strptime(":".join(app_time_str.split(":")[:2]), "%H:%M").time()
                    
                    if time_min <= app_time_obj <= time_max:
                        user_id = row.get("user_id", "")
                        if user_id and user_id != "NON_LINE_USER":
                            if send_line_reminder_flex(user_id, row["service_type"], row["appointment_date"], row["appointment_time"], row["name"], row.get("department", "dental")):
                                # อัปเดตสถานะใน Supabase เพื่อไม่ให้ส่งเตือนซ้ำ
                                supabase_client.table("appointments")\
                                    .update({"reminder_sent": True})\
                                    .eq("id", row["id"])\
                                    .execute()
                except Exception as ex:
                    print(f"เกิดข้อผิดพลาดในการตรวจสอบนัดหมายรายคิว: {ex}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการตรวจสอบคิวแจ้งเตือน Supabase: {e}")

@st.cache_resource
def start_production_reminder_worker():
    """เปิดการทำ Background Thread ทำงานเบื้องหลังดึงข้อมูล Supabase ทุกๆ 5 นาที (เฉพาะการรันจริงไม่ใช่เดโม)"""
    if is_demo:
        return "Demo Mode - Checked via Main Thread"
        
    import threading
    import time as pytime
    
    def worker():
        while True:
            try:
                run_reminder_check()
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในเธรดแจ้งเตือนเบื้องหลัง: {e}")
            pytime.sleep(300) # หน่วงเวลาสแกนใหม่ทุก 5 นาที
            
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return "Production Background Worker Started"

# เรียกใช้เธรดเบื้องหลังในฝั่งโปรดักชัน
start_production_reminder_worker()

import time as main_time
# ตัวแปรควบคุมการรันแจ้งเตือนบนหน้าเว็บ
if "last_reminder_check" not in st.session_state:
    st.session_state.last_reminder_check = 0.0

# รันระบบสแกนคิวบนหน้าหลัก โดยจำกัดการตรวจสอบไม่บ่อยเกินครั้งละ 60 วินาที เพื่อถนอมการยิงคิว API
current_time_epoch = main_time.time()
if current_time_epoch - st.session_state.last_reminder_check > 60:
    st.session_state.last_reminder_check = current_time_epoch
    run_reminder_check()

# ----------------- Sidebar (LINE Profile & Config info) -----------------
with st.sidebar:
    st.image("moph_logo.png", width=80)
    st.markdown("### รพ.สต.ท่าเกษม")
    
    dept_sidebar_titles = {
        "": "🏥 **ระบบลงทะเบียนนัดหมาย**",
        "dental": "🦷 **แผนกทันตกรรม**",
        "thai_traditional": "🌿 **แผนกแพทย์แผนไทย**",
        "physical_therapy": "♿ **แผนกกายภาพบำบัด**"
    }
    sidebar_title = dept_sidebar_titles.get(st.session_state.selected_dept, "🏥 **ระบบลงทะเบียนนัดหมาย**")
    st.markdown(sidebar_title)
    st.divider()
    
    # สลับระบบงาน
    app_mode = st.selectbox(
        "เลือกระบบงาน (Role):",
        ["ผู้รับบริการ (LINE LIFF)", "เจ้าหน้าที่ (Back-Office & Dashboard)"]
    )
    st.divider()
    
    # LINE Profile Section
    if st.session_state.line_user_id:
        is_mock_user = (st.session_state.line_user_id == "U999988887777666655554444")
        if is_mock_user:
            st.info("🟢 เชื่อมต่อสิทธิ์จำลองอัตโนมัติ ✅")
        else:
            st.success("เชื่อมต่อ LINE สำเร็จ ✅")
            
        if st.session_state.line_picture_url:
            st.image(st.session_state.line_picture_url, width=70)
        st.write(f"**ชื่อ LINE:** {st.session_state.line_display_name}")
        st.caption(f"User ID: `{st.session_state.line_user_id[:10]}...`")
        
        # ส่วนควบคุมจำลองเพิ่มเติมแบบซ่อนได้
        with st.expander("⚙️ ตั้งค่าจำลอง LINE (สำหรับทดสอบ)"):
            new_mock_id = st.text_input("จำลอง User ID LINE ใหม่:", value=st.session_state.line_user_id)
            new_mock_name = st.text_input("จำลอง ชื่อ LINE ใหม่:", value=st.session_state.line_display_name)
            col_mock_save, col_mock_clear = st.columns(2)
            with col_mock_save:
                if st.button("บันทึกจำลอง 💾", use_container_width=True):
                    st.session_state.line_user_id = new_mock_id
                    st.session_state.line_display_name = new_mock_name
                    st.rerun()
            with col_mock_clear:
                if st.button("ล้างสิทธิ์ 🗑️", use_container_width=True):
                    st.session_state.line_user_id = ""
                    st.session_state.line_display_name = ""
                    st.session_state.line_picture_url = ""
                    st.rerun()
    else:
        st.warning("⚠️ ยังไม่เชื่อมต่อ LINE LIFF")
        st.info("💡 เนื่องจากคุณเข้าใช้งานผ่านเว็บเบราว์เซอร์ปกติภายนอกแอปพลิเคชัน LINE (เช่น บนคอมพิวเตอร์) คุณสามารถใช้การจำลองสิทธิ์ LINE ด้านล่างนี้เพื่อใช้ทดสอบการลงทะเบียนนัดหมายได้เลยครับ")
        mock_id = st.text_input("จำลอง User ID LINE", "U999988887777666655554444")
        mock_name = st.text_input("จำลอง ชื่อ LINE", "คุณใจดี รักสุขภาพ")
        if st.button("บันทึกสิทธิ์จำลอง 💾", use_container_width=True):
            st.session_state.line_user_id = mock_id
            st.session_state.line_display_name = mock_name
            st.rerun()
        
    st.divider()
    
    # System Status / Mode
    if is_demo:
        st.warning("🟢 โหมดสาธิต (Demo Mode)")
        st.caption("ระบบเก็บข้อมูลลงบนหน่วยความจำชั่วคราวและจำลองสล็อตเวลา คอนฟิก Supabase ใน Streamlit Secrets เพื่อใช้งานจริง")
    else:
        st.success("🔌 เชื่อมต่อ Supabase แล้ว")
        st.caption(f"URL: `{supabase_url[:25]}...`")

# ----------------- LINE LIFF Javascript integration -----------------
def render_liff_login(liff_id):
    if not liff_id or "xxxxxxxx" in liff_id:
        return
    
    liff_js = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>LINE LIFF Login</title>
        <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
    </head>
    <body>
        <script>
            liff.init({{ liffId: "{liff_id}" }}).then(() => {{
                const getParentUrl = () => {{
                    try {{
                        return new URL(window.parent.location.href);
                    }} catch (e) {{
                        if (document.referrer) {{
                            return new URL(document.referrer);
                        }}
                        return new URL(window.location.href);
                    }}
                }};
                
                const updateParentUrl = (profile) => {{
                    const parentUrl = getParentUrl();
                    if (parentUrl.searchParams.get("userId") !== profile.userId) {{
                        parentUrl.searchParams.set("userId", profile.userId);
                        parentUrl.searchParams.set("displayName", profile.displayName);
                        if (profile.pictureUrl) {{
                            parentUrl.searchParams.set("pictureUrl", profile.pictureUrl);
                        }}
                        try {{
                            window.parent.location.replace(parentUrl.toString());
                        }} catch (e) {{
                            window.parent.location.href = parentUrl.toString();
                        }}
                    }}
                }};

                if (liff.isInClient()) {{
                    if (!liff.isLoggedIn()) {{
                        liff.login();
                    }} else {{
                        liff.getProfile().then(updateParentUrl);
                    }}
                }} else {{
                    if (liff.isLoggedIn()) {{
                        liff.getProfile().then(updateParentUrl);
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(liff_js, height=0)

# ----------------- PATIENT PORTAL (LINE LIFF) -----------------
if app_mode == "ผู้รับบริการ (LINE LIFF)":
    # 1. LINE LIFF Login Integration
    render_liff_login(liff_id)
    
    # 2. Main title & banner
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2.5rem; background: {theme['gradient_bg']}; padding: 2rem; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
        <img src="{theme['banner_img']}" width="90" style="margin-bottom: 1rem;">
        <h1 class="main-title" style="margin: 0;">รพ.สต.ท่าเกษม</h1>
        <p class="sub-title" style="margin: 0.5rem 0 0 0;">ระบบลงทะเบียนนัดหมายออนไลน์ - แผนก{theme['title_thai'] or 'บริการทั่วไป'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Step Indicator
    step1_class = "active" if st.session_state.step == 1 else ("completed" if st.session_state.step > 1 else "")
    step2_class = "active" if st.session_state.step == 2 else ("completed" if st.session_state.step > 2 else "")
    step3_class = "active" if st.session_state.step == 3 else ("completed" if st.session_state.step > 3 else "")
    step4_class = "active" if st.session_state.step == 4 else ""
    
    st.markdown(f"""
    <div class="step-container">
        <div class="step-item {step1_class}">
            <div class="step-icon">1</div>
            <div class="step-label">เลือกบริการ</div>
        </div>
        <div class="step-item {step2_class}">
            <div class="step-icon">2</div>
            <div class="step-label">เลือกวัน/เวลา</div>
        </div>
        <div class="step-item {step3_class}">
            <div class="step-icon">3</div>
            <div class="step-label">กรอกข้อมูล</div>
        </div>
        <div class="step-item {step4_class}">
            <div class="step-icon">4</div>
            <div class="step-label">เสร็จสิ้น</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- STEP 1: เลือกแผนกและบริการ ---
    if st.session_state.step == 1:
        # หากยังไม่เลือกแผนก ให้เลือกแผนกก่อน
        if not st.session_state.selected_dept:
            depts_list = fetch_all_departments()
            if not depts_list:
                st.info("ℹ️ ขออภัยด้วยค่ะ ปัจจุบันยังไม่มีแผนกที่เปิดให้บริการออนไลน์ในระบบ")
            else:
                cols_per_row = 3
                for row_idx in range(0, len(depts_list), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for col_idx, dept_item in enumerate(depts_list[row_idx:row_idx+cols_per_row]):
                        col = cols[col_idx]
                        d_key = dept_item["key"]
                        d_name = dept_item["display_name"]
                        d_color = dept_item["theme_color"]
                        d_img = dept_item["banner_img"]
                        
                        # ดึงบริการแนะนำของแผนกนี้
                        dept_services = fetch_services(d_key)
                        services_preview = ", ".join([s.get("title", "") for s in dept_services[:4]])
                        if not services_preview:
                            services_preview = "จองคิวรับบริการทั่วไป"
                            
                        col.markdown(f"""
                        <div class="service-card" style="text-align: center; border-left: 5px solid {d_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <img src="{d_img}" width="60" style="margin: 10px auto;"><br>
                                <h4 style="margin-top: 10px; color: #240046; font-size: 1.1rem; font-weight: 700;">{d_name}</h4>
                                <p style="font-size: 0.8rem; color: #6C757D; line-height: 1.2;">{services_preview}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if col.button(f"เลือก {d_name} 👉", use_container_width=True, key=f"btn_select_{d_key}"):
                            st.session_state.selected_dept = d_key
                            st.rerun()
        else:
            # ปุ่มย้อนกลับไปหน้าเลือกแผนก
            if st.button("⬅️ เปลี่ยนแผนกบริการ"):
                st.session_state.selected_dept = ""
                st.session_state.selected_service = ""
                st.rerun()
                
            st.write(f"### 📌 ขั้นตอนที่ 1: เลือกประเภทบริการ ({theme['title_thai']})")
            
            # ดึงรายการบริการของแผนกนี้
            services_list = fetch_services(st.session_state.selected_dept)
            
            if not services_list:
                st.warning("⚠️ ไม่พบข้อมูลบริการของแผนกนี้ในระบบ")
            else:
                for service in services_list:
                    icon_str = service.get("icon", "😀")
                    title_str = service.get("title", "")
                    desc_str = service.get("description", "")
                    
                    st.markdown(f"""
                    <div class="service-card" style="border-left: 5px solid {theme['primary']};">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <span style="font-size: 2.2rem;">{icon_str}</span>
                            <div style="flex-grow: 1;">
                                <h4 style="margin: 0; color: {theme['text_dark']}; font-weight: 700;">{title_str}</h4>
                                <p style="margin: 5px 0 0 0; font-size: 0.88rem; color: #6C757D;">{desc_str}</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"เลือกบริการ: {title_str}", key=f"select_srv_{service['id']}", use_container_width=True):
                        st.session_state.selected_service = title_str
                        st.session_state.step = 2
                        st.session_state.selected_time = ""
                        st.rerun()
    
    elif st.session_state.step == 2:
        st.write(f"### 📌 ขั้นตอนที่ 2: เลือกวันและเวลาที่สะดวก")
        st.info(f"**บริการที่เลือก:** {st.session_state.selected_service}")
        
        # ดึงการตั้งค่าของแผนกที่เลือก
        dept_settings = get_settings(st.session_state.selected_dept)
        booking_range = dept_settings.get("booking_range_days", 30)
        working_days = dept_settings.get("working_days", [0, 1, 2, 3, 4])
        closed_dates = dept_settings.get("closed_dates", [])
        all_slots = dept_settings.get("time_slots", ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"])
        
        # 1. เลือกวัน
        min_date = datetime.date.today()
        max_date = min_date + datetime.timedelta(days=booking_range)
        
        thai_days_name = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
        working_days_text = ", ".join([thai_days_name[d] for d in working_days])
        
        selected_date = st.date_input(
            f"เลือกวันที่นัดหมาย (เปิดบริการวัน: {working_days_text}):", 
            min_value=min_date, 
            max_value=max_date, 
            value=st.session_state.selected_date
        )
        
        # ตรวจสอบวันหยุดและวันให้บริการ
        selected_weekday = selected_date.weekday()
        selected_date_str = selected_date.isoformat()
        
        if selected_weekday not in working_days:
            st.warning(f"⚠️ ขออภัยด้วยค่ะ รพ.สต.ท่าเกษม ปิดให้บริการแผนก{theme['title_thai']}ในวัน{thai_days_name[selected_weekday]} (เปิดให้บริการวัน: {working_days_text})")
        elif selected_date_str in closed_dates:
            st.warning(f"⚠️ ขออภัยด้วยค่ะ วันที่ {format_thai_date(selected_date)} เป็นวันหยุดพิเศษ/งดให้บริการของแผนก{theme['title_thai']} กรุณาเลือกวันอื่น")
        else:
            st.session_state.selected_date = selected_date
            
            # ดึงช่วงเวลาที่ถูกจองไปแล้ว
            booked_slots = get_booked_slots(selected_date, st.session_state.selected_dept, st.session_state.selected_service)
            
            st.write("#### ⏰ ช่วงเวลาให้บริการ")
            
            # แสดงผลตารางเวลา 3x3 Grid
            for i in range(0, len(all_slots), 3):
                cols = st.columns(3)
                for idx, slot_time in enumerate(all_slots[i:i+3]):
                    col = cols[idx]
                    is_booked = slot_time in booked_slots
                    
                    # ตรวจสอบเวลาที่จองแล้ว
                    if is_booked:
                        col.button(f"❌ {slot_time} (เต็ม)", key=f"slot_{slot_time}", disabled=True, use_container_width=True)
                    else:
                        # ตรวจสอบว่าเวลานี้ถูกเลือกอยู่หรือไม่
                        is_selected = st.session_state.selected_time == slot_time
                        btn_label = f"🟣 {slot_time}" if is_selected else f"⚪ {slot_time}"
                        
                        if col.button(btn_label, key=f"slot_{slot_time}", use_container_width=True):
                            st.session_state.selected_time = slot_time
                            st.rerun()
     
            # ควบคุมการเปลี่ยนหน้า
            st.divider()
            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("⬅️ ย้อนกลับ", use_container_width=True):
                    st.session_state.step = 1
                    st.rerun()
                    
            with col_next:
                if st.session_state.selected_time:
                    st.success(f"คุณเลือก: วันที่ {selected_date.strftime('%d/%m/%Y')} เวลา {st.session_state.selected_time} น.")
                    if st.button("ถัดไป ➡️", use_container_width=True):
                        st.session_state.step = 3
                        st.rerun()
                else:
                    st.button("กรุณาเลือกเวลานัดหมาย", disabled=True, use_container_width=True)
     
    # --- STEP 3: กรอกข้อมูลผู้รับบริการ (Enter Info) ---
    elif st.session_state.step == 3:
        st.write("### 📌 ขั้นตอนที่ 3: กรอกข้อมูลผู้รับบริการ")
        
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; border-left: 4px solid {theme['primary']}; margin-bottom: 1.5rem;">
            <b>รายละเอียดการจอง:</b> {st.session_state.selected_service}<br>
            <b>วันที่นัดหมาย:</b> {st.session_state.selected_date.strftime('%d/%m/%Y')} เวลา {st.session_state.selected_time} น.
        </div>
        """, unsafe_allow_html=True)
        
        # หากยังไม่เชื่อมต่อ LINE ให้แจ้งเตือนก่อนส่ง
        if not st.session_state.line_user_id:
            st.warning("⚠️ แนะนำให้เชื่อมต่อกับ LINE ในฝั่งเมนูด้านซ้าย เพื่อให้ได้รับข้อความแจ้งเตือนคอนเฟิร์มนัดหมายกลับทางแชท")
            
        with st.form("info_form"):
            name = st.text_input("ชื่อ - นามสกุล:", value=st.session_state.user_name, placeholder="นางสาว ใจดี รักสุขภาพ")
            phone = st.text_input("เบอร์โทรศัพท์มือถือ (10 หลัก):", value=st.session_state.user_phone, max_chars=10, placeholder="0812345678")
            cid = st.text_input("เลขบัตรประจำตัวประชาชน (13 หลัก):", value=st.session_state.user_cid, max_chars=13, placeholder="1234567890123")
            note = st.text_area("อาการเบื้องต้น / ความต้องการอื่นๆ เพิ่มเติม (ถ้ามี):", value=st.session_state.user_note, placeholder="มีอาการปวดข้อ / ต้องการพอกสมุนไพร...")
            
            st.caption("ℹ️ ระบบจะใช้เลขบัตรประจำตัวประชาชนในการค้นหาประวัติการรักษาเดิมที่ รพ.สต.ท่าเกษม")
            
            submitted = st.form_submit_button(f"🏥 ยืนยันข้อมูลการนัดหมาย{theme['title_thai']}", use_container_width=True)
            
            if submitted:
                # เก็บค่าลงใน session_state
                st.session_state.user_name = name
                st.session_state.user_phone = phone
                st.session_state.user_cid = cid
                st.session_state.user_note = note
                
                # ตรวจสอบความถูกต้องของข้อมูล
                errors = []
                if not name.strip():
                    errors.append("กรุณากรอก ชื่อ-นามสกุล")
                if not phone.strip() or len(phone.strip()) != 10 or not phone.isdigit():
                    errors.append("กรุณากรอก เบอร์โทรศัพท์ ให้ครบ 10 หลัก (เฉพาะตัวเลข)")
                if not validate_thai_cid(cid):
                    errors.append("เลขบัตรประจำตัวประชาชนไม่ถูกต้อง กรุณากรอกใหม่ให้ครบ 13 หลักตามรูปแบบมาตรฐาน")
                    
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    # บันทึกข้อมูลเข้าฐานข้อมูล
                    # ใช้ LINE User ID ถ้าไม่มีใช้ ID ทั่วไป/จำลอง
                    final_line_id = st.session_state.line_user_id if st.session_state.line_user_id else "NON_LINE_USER"
                    
                    with st.spinner("กำลังจองคิวและลงบันทึกในระบบ..."):
                        success, message = execute_booking(
                            dept=st.session_state.selected_dept,
                            user_id=final_line_id,
                            name=name,
                            phone=phone,
                            cid=cid,
                            service=st.session_state.selected_service,
                            app_date=st.session_state.selected_date,
                            app_time=st.session_state.selected_time,
                            note=note
                        )
                        
                        if success:
                            # ส่ง Flex Message ถ้ามี Token และ user_id
                            if final_line_id != "NON_LINE_USER":
                                send_line_flex_message(
                                    user_id=final_line_id,
                                    service=st.session_state.selected_service,
                                    app_date=st.session_state.selected_date,
                                    app_time=st.session_state.selected_time,
                                    name=name,
                                    dept=st.session_state.selected_dept
                                )
                            st.session_state.step = 4
                            st.rerun()
                        else:
                            st.error(f"❌ จองคิวล้มเหลว: {message}")
     
        # ย้อนกลับ
        if st.button("⬅️ ย้อนกลับไปเลือกเวลา"):
            st.session_state.step = 2
            st.rerun()
     
    # --- STEP 4: แสดงผลสิทธิ์สำเร็จ (Success Screen) ---
    elif st.session_state.step == 4:
        q_num = get_queue_number(st.session_state.selected_time)
        st.markdown(f"""
        <div class="success-box" style="text-align: center; padding: 1.5rem; background-color: #E8F5E9; border-radius: 12px; margin-bottom: 1.5rem;">
            <h2 style="margin: 0; color: #1B4332;">🎉 นัดหมายสำเร็จเรียบร้อยแล้วค่ะ</h2>
            <p style="margin-top: 0.5rem; margin-bottom: 0.2rem; font-size: 1.4rem; color: {theme['primary']};"><b>ลำดับคิวของคุณคือ: คิวที่ {q_num}</b></p>
            <p style="margin-top: 0rem; margin-bottom: 0; color: #666; font-size: 0.9rem;">รหัสอ้างอิงการจองคิว: #{st.session_state.appointment_id}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("#### 📑 สรุปรายละเอียดการนัดหมาย")
        
        st.markdown(f"""
        <div style="background-color: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 1.5rem;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 0.5rem 0; color: #888;"><b>ประเภทบริการ:</b></td>
                    <td style="padding: 0.5rem 0; text-align: right; font-weight: bold; color: {theme['primary']};">{st.session_state.selected_service}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 0.5rem 0; color: #888;"><b>ชื่อผู้รับบริการ:</b></td>
                    <td style="padding: 0.5rem 0; text-align: right;">{st.session_state.user_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 0.5rem 0; color: #888;"><b>เบอร์โทรติดต่อ:</b></td>
                    <td style="padding: 0.5rem 0; text-align: right;">{st.session_state.user_phone}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 0.5rem 0; color: #888;"><b>วันที่นัดหมาย:</b></td>
                    <td style="padding: 0.5rem 0; text-align: right; font-weight: bold;">{st.session_state.selected_date.strftime('%d/%m/%Y')}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 0.5rem 0; color: #888;"><b>เวลานัดหมาย:</b></td>
                    <td style="padding: 0.5rem 0; text-align: right; font-weight: bold; color: {theme['primary']};">{st.session_state.selected_time} น.</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 0.5rem 0; color: #888;"><b>ลำดับคิว:</b></td>
                    <td style="padding: 0.5rem 0; text-align: right; font-weight: bold; color: {theme['primary']};">คิวที่ {q_num}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem 0; color: #888;"><b>สถานที่:</b></td>
                    <td style="padding: 0.5rem 0; text-align: right;">แผนก{theme['title_thai']} รพ.สต.ท่าเกษม</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background-color: #E8F1F2; padding: 1rem; border-radius: 8px; font-size: 0.9rem; color: #1D3557; margin-bottom: 1.5rem;">
            <b>💡 ข้อแนะนำในการเข้ารับบริการ:</b>
            <ul style="margin: 0.5rem 0 0 1rem; padding: 0;">
                <li>กรุณาเดินทางมาถึง รพ.สต.ท่าเกษม ก่อนเวลานัดหมายอย่างน้อย 15 นาที</li>
                <li>กรุณานำ<b>บัตรประจำตัวประชาชนตัวจริง</b>มาด้วยในวันนัดหมาย</li>
                <li>หากต้องการยกเลิกหรือเลื่อนนัดหมาย กรุณาติดต่อล่วงหน้าอย่างน้อย 1 วัน</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 1. ลิงก์บันทึกลง Google Calendar
        # แปลงข้อมูลเวลา
        date_formatted = st.session_state.selected_date.strftime("%Y%m%d")
        hour_str, min_str = st.session_state.selected_time.split(":")
        
        start_dt = f"{date_formatted}T{hour_str}{min_str}00"
        # สมมติใช้เวลาตรวจ 30 นาที
        end_time_min = int(min_str) + 30
        end_time_hour = int(hour_str)
        if end_time_min >= 60:
            end_time_min -= 60
            end_time_hour += 1
        end_dt = f"{date_formatted}T{end_time_hour:02d}{end_time_min:02d}00"
        
        app_id_str = st.session_state.appointment_id if st.session_state.appointment_id else f"{st.session_state.selected_dept.upper()}-CONFIRM"
        title = f"นัดหมาย{theme['title_thai']} [{app_id_str}]: {st.session_state.selected_service}"
        details = f"รหัสอ้างอิงการจองคิว: {app_id_str}\nแผนก: {theme['title_thai']}\nประเภทบริการ: {st.session_state.selected_service}\nผู้เข้ารับบริการ: {st.session_state.user_name}\nเบอร์โทรศัพท์ติดต่อ: {st.session_state.user_phone}\n\nรพ.สต.ท่าเกษม ใส่ใจสุขภาพ เคียงข้างประชาชน"
        location = "รพ.สต.ท่าเกษม อ.เมืองสระแก้ว จ.สระแก้ว"
        
        # เลือก Google Calendar ID แยกตามแผนกบริการ (ใช้ค่าเฉพาะของแผนก หรือค่าเริ่มต้นส่วนกลาง)
        active_calendar_id = dept_cal_map.get(st.session_state.selected_dept, "")
        if not active_calendar_id:
            active_calendar_id = google_calendar_id
            
        gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(title)}&dates={start_dt}/{end_dt}&details={urllib.parse.quote(details)}&location={urllib.parse.quote(location)}"
        if active_calendar_id:
            gcal_url += f"&src={urllib.parse.quote(active_calendar_id)}"
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<a href="{gcal_url}" target="_blank" style="text-decoration: none;"><button style="width:100%; height:45px; background-color:#4285F4; color:white; border-radius:10px; font-weight:600; border:none;">📅 บันทึกในปฏิทิน Google</button></a>', unsafe_allow_html=True)
        with col2:
            if st.button("ทำนัดหมายใหม่ 🔄", use_container_width=True):
                # รีเซ็ตสเตจจองใหม่
                st.session_state.step = 1
                st.session_state.selected_service = ""
                st.session_state.selected_time = ""
                st.session_state.appointment_id = None

else:
    # ----------------- STAFF PORTAL -----------------
    st.markdown("<h2 style='text-align: center; color: #5A2A94; font-weight: 800;'>🔒 ระบบหลังบ้านและรายงานสถิติ</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7B2CBF; font-size: 0.95rem; font-weight: 500; margin-bottom: 2rem;'>เจ้าหน้าที่ รพ.สต.ท่าเกษม</p>", unsafe_allow_html=True)
    
    # ตรวจสอบล็อกอิน
    if "staff_logged_in" not in st.session_state:
        st.session_state.staff_logged_in = False
        
    if not st.session_state.staff_logged_in:
        col_sec_left, col_sec_mid, col_sec_right = st.columns([1, 2, 1])
        with col_sec_mid:
            st.markdown("""
            <div style="background-color: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 5px solid #7B2CBF; text-align: center;">
                <h4 style="color: #240046; margin-bottom: 1rem;">ยืนยันตนเข้าใช้หลังบ้าน</h4>
            </div>
            """, unsafe_allow_html=True)
            
            passcode_label = "รหัสผ่านเจ้าหน้าที่ (รหัสผ่านคือ 1234 ในโหมดจำลอง):" if is_demo else "รหัสผ่านเจ้าหน้าที่:"
            passcode = st.text_input(passcode_label, type="password")
            if st.button("ยืนยันรหัสผ่าน 🔑", use_container_width=True):
                if passcode.strip() == staff_password:
                    st.session_state.staff_logged_in = True
                    st.success("สิทธิ์การเข้าใช้งานถูกต้อง กำลังโหลดระบบหลังบ้าน...")
                    st.rerun()
                else:
                    secrets_keys = list(st.secrets.keys()) if hasattr(st, "secrets") else []
                    st.error(f"รหัสผ่านผู้ใช้งานไม่ถูกต้อง กรุณากรอกอีกครั้ง (ดึงจากระบบ: '{staff_password}', คีย์ทั้งหมดที่เจอใน Secrets: {secrets_keys})")
    else:
        # แถบข้างเพิ่มปุ่มออกจากระบบ
        if st.sidebar.button("🚪 ออกจากระบบหลังบ้าน"):
            st.session_state.staff_logged_in = False
            st.rerun()
            
        # สร้างแท็บควบคุม
        tab_dash, tab_book, tab_manage, tab_services, tab_depts = st.tabs([
            "📊 แดชบอร์ด & รายงาน", 
            "📅 เจ้าหน้าที่ลงนัดเอง", 
            "📋 จัดการสิทธิ์การนัดหมาย",
            "⚙️ ตั้งค่าและบริการ",
            "🏥 จัดการแผนกบริการ"
        ])
        
        # ดึงข้อมูลการนัดหมายทั้งหมด
        all_apps = fetch_all_appointments()
        
        # --- TAB 1: DASHBOARD ---
        with tab_dash:
            st.write("### สรุปตัวเลขและการวิเคราะห์ข้อมูล")
            
            depts_list = fetch_all_departments()
            dash_choices = ["รวมทุกแผนก (All Departments)"] + [f"{d['display_name']} ({d['key']})" for d in depts_list]
            
            dash_dept_filter = st.selectbox(
                "กรองตามแผนกบริการ:",
                dash_choices,
                key="dash_dept_select"
            )
            
            if dash_dept_filter == "รวมทุกแผนก (All Departments)":
                selected_dash_dept = "all"
            else:
                selected_dash_dept = depts_list[dash_choices.index(dash_dept_filter) - 1]["key"]
            
            if not all_apps:
                st.info("ไม่มีรายการนัดหมายในระบบในขณะนี้")
            else:
                df_all = pd.DataFrame(all_apps)
                # กรองตามแผนกที่เลือก
                if selected_dash_dept != "all":
                    df = df_all[df_all['department'] == selected_dash_dept]
                else:
                    df = df_all
                
                if df.empty:
                    st.info("ไม่มีข้อมูลการนัดหมายตามแผนกที่เลือก")
                else:
                    # คำนวณยอด
                    total_count = len(df)
                    today_str = datetime.date.today().isoformat()
                    today_count = len(df[df['appointment_date'] == today_str])
                    
                    # ยอดสัปดาห์นี้
                    df['date_parsed'] = pd.to_datetime(df['appointment_date'])
                    today_dt = datetime.datetime.now()
                    start_of_week = today_dt - datetime.timedelta(days=today_dt.weekday())
                    end_of_week = start_of_week + datetime.timedelta(days=6)
                    week_count = len(df[(df['date_parsed'] >= pd.to_datetime(start_of_week.date())) & (df['date_parsed'] <= pd.to_datetime(end_of_week.date()))])
                    
                    # แสดงตัวเลข KPI Metrics
                    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                    with kpi_col1:
                        st.metric("จำนวนนัดสะสมทั้งหมด", f"{total_count} คิว")
                    with kpi_col2:
                        st.metric("นัดหมายเข้ารับบริการวันนี้", f"{today_count} คิว")
                    with kpi_col3:
                        st.metric("นัดหมายสัปดาห์นี้", f"{week_count} คิว")
                        
                    st.divider()
                    
                    # กำหนดสีชาร์ตตามแผนก
                    chart_color = "#7B2CBF"
                    if selected_dash_dept == "thai_traditional":
                        chart_color = "#2D6A4F"
                    elif selected_dash_dept == "physical_therapy":
                        chart_color = "#0077B6"
                    
                    # กราฟแยกตามบริการ
                    st.write("#### 📊 สัดส่วนจำแนกตามประเภทบริการรักษา")
                    service_counts = df['service_type'].value_counts()
                    st.bar_chart(service_counts, color=chart_color)
                    
                    chart_col1, chart_col2 = st.columns(2)
                    
                    # กราฟสถิติตามเวลา (Peak Hours)
                    with chart_col1:
                        st.write("#### ⏰ ช่วงเวลาที่มีผู้ลงนัดสูงสุด (Peak Hours)")
                        time_counts = df['appointment_time'].value_counts().sort_index()
                        st.bar_chart(time_counts, color="#FFB703")
                        
                    # กราฟจำนวนจองรายวัน
                    with chart_col2:
                        st.write("#### 📈 แนวโน้มคนไข้รายวัน")
                        daily_counts = df.groupby('appointment_date').size().reset_index(name='จำนวนคนไข้')
                        daily_counts = daily_counts.sort_values('appointment_date').set_index('appointment_date')
                        st.line_chart(daily_counts, color=chart_color)
 
        # --- TAB 2: STAFF MANUAL BOOKING ---
        with tab_book:
            st.write("### 📅 บันทึกข้อมูลนัดหมายผู้รับบริการ (กรณีโทรมาจอง)")
            
            depts_list = fetch_all_departments()
            staff_dept_choices = [f"{d['display_name']} ({d['key']})" for d in depts_list]
            
            if not depts_list:
                st.warning("⚠️ ไม่มีแผนกเปิดให้บริการในระบบ")
                selected_staff_dept = "dental"
            else:
                staff_dept = st.selectbox(
                    "เลือกแผนกบริการที่ต้องการบันทึกนัดหมาย:",
                    staff_dept_choices,
                    key="staff_manual_dept"
                )
                selected_staff_dept = depts_list[staff_dept_choices.index(staff_dept)]["key"]
            
            with st.form("staff_manual_form"):
                # ดึงบริการสำหรับแผนกนี้
                staff_db_services = fetch_services(selected_staff_dept)
                staff_service_choices = [s.get("title", "") for s in staff_db_services]
                if not staff_service_choices:
                    staff_service_choices = ["อื่นๆ (ระบุ)"]
                elif "อื่นๆ (ระบุ)" not in staff_service_choices:
                    staff_service_choices.append("อื่นๆ (ระบุ)")
                    
                staff_service = st.selectbox(
                    "ประเภทบริการรักษา:",
                    staff_service_choices
                )
                custom_staff_service = st.text_input("กรณีเลือกบริการอื่นๆ กรุณาระบุรายละเอียด:")
                
                # ดึงค่าการตั้งค่าจากระบบของแผนกที่เลือก
                dept_settings = get_settings(selected_staff_dept)
                booking_range = dept_settings.get("booking_range_days", 30)
                working_days = dept_settings.get("working_days", [0, 1, 2, 3, 4])
                closed_dates = dept_settings.get("closed_dates", [])
                all_slots = dept_settings.get("time_slots", ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"])
                
                thai_days_name = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
                working_days_text = ", ".join([thai_days_name[d] for d in working_days])
                
                staff_date = st.date_input(
                    f"เลือกวันที่นัดหมาย (เปิดบริการวัน: {working_days_text}):",
                    min_value=datetime.date.today(),
                    max_value=datetime.date.today() + datetime.timedelta(days=booking_range)
                )
                
                # ตรวจสอบวันหยุดและวันให้บริการ
                selected_weekday = staff_date.weekday()
                selected_date_str = staff_date.isoformat()
                
                is_valid_date = True
                if selected_weekday not in working_days:
                    st.warning(f"⚠️ แผนกที่เลือกปิดให้บริการในวัน{thai_days_name[selected_weekday]} (วันเปิดบริการ: {working_days_text})")
                    is_valid_date = False
                elif selected_date_str in closed_dates:
                    st.warning(f"⚠️ วันที่ {format_thai_date(staff_date)} เป็นวันหยุดพิเศษ/งดให้บริการ")
                    is_valid_date = False
                
                # ดึงช่วงเวลาที่ว่าง
                booked_slots = get_booked_slots(staff_date, selected_staff_dept, staff_service)
                available_slots = [s for s in all_slots if s not in booked_slots]
                
                if not is_valid_date:
                    staff_time = None
                elif not available_slots:
                    st.warning("⚠️ ไม่มีช่วงเวลาว่างให้สามารถจองคิวเพิ่มได้ในวันนี้ กรุณาเปลี่ยนวันที่ต้องการจอง")
                    staff_time = None
                else:
                    staff_time = st.selectbox("เลือกช่วงเวลานัดหมาย:", available_slots)
                    
                st.divider()
                st.write("**👤 ข้อมูลผู้รับบริการ**")
                p_name = st.text_input("ชื่อ-นามสกุล:")
                p_phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก):", max_chars=10)
                p_cid = st.text_input("เลขบัตรประจำตัวประชาชน (13 หลัก):", max_chars=13)
                p_note = st.text_area("หมายเหตุ/อาการเพิ่มเติม:")
                
                staff_submitted = st.form_submit_button("💾 บันทึกนัดหมายในระบบทันที", use_container_width=True)
                
                if staff_submitted:
                    # ตรวจสอบการเลือกบริการ
                    final_service = staff_service
                    if staff_service == "อื่นๆ (ระบุ)":
                        if custom_staff_service.strip():
                            final_service = f"อื่นๆ: {custom_staff_service}"
                        else:
                            st.error("กรุณาระบุรายละเอียดเพิ่มเติมในช่องบริการอื่นๆ")
                            final_service = None
                            
                    # ตรวจสอบความถูกต้องของข้อมูล
                    errors = []
                    if not p_name.strip():
                        errors.append("กรุณาระบุชื่อ-นามสกุลผู้ป่วย")
                    if not p_phone.strip() or len(p_phone.strip()) != 10 or not p_phone.isdigit():
                        errors.append("กรุณาระบุเบอร์โทรศัพท์ให้ครบ 10 หลัก")
                    if not validate_thai_cid(p_cid):
                        errors.append("เลขบัตรประจำตัวประชาชนไม่ถูกต้องตามมาตรฐาน 13 หลัก")
                    if not staff_time:
                        errors.append("ไม่มีช่วงเวลาใดที่จองได้")
                        
                    if errors:
                        for err in errors:
                            st.error(err)
                    elif final_service:
                        success, message = execute_booking(
                            dept=selected_staff_dept,
                            user_id="STAFF_MANUAL",
                            name=p_name,
                            phone=p_phone,
                            cid=p_cid,
                            service=final_service,
                            app_date=staff_date,
                            app_time=staff_time,
                            note=p_note
                        )
                        if success:
                            st.success("บันทึกข้อมูลและจองเวลานัดหมายให้ผู้ป่วยเรียบร้อยแล้วค่ะ")
                            st.rerun()
                        else:
                            st.error(f"เกิดข้อผิดพลาด: {message}")
 
        # --- TAB 3: MANAGE APPOINTMENTS ---
        with tab_manage:
            st.write("### 🔍 ตารางรายชื่อผู้ลงทะเบียนนัดหมาย")
            
            manage_dept_filter = st.selectbox(
                "กรองแผนกนัดหมายที่ต้องการตรวจสอบ:",
                ["รวมทุกแผนก (All Departments)", "แผนกทันตกรรม (Dental)", "แผนกแพทย์แผนไทย (Traditional Thai)", "แผนกกายภาพบำบัด (Physical Therapy)"],
                key="manage_dept_select"
            )
            manage_dept_map = {
                "รวมทุกแผนก (All Departments)": "all",
                "แผนกทันตกรรม (Dental)": "dental",
                "แผนกแพทย์แผนไทย (Traditional Thai)": "thai_traditional",
                "แผนกกายภาพบำบัด (Physical Therapy)": "physical_therapy"
            }
            selected_manage_dept_tab3 = manage_dept_map[manage_dept_filter]
            
            if not all_apps:
                st.info("ไม่มีรายการคิวนัดหมายในขณะนี้")
            else:
                df_all = pd.DataFrame(all_apps)
                # กรองตามแผนก
                if selected_manage_dept_tab3 != "all":
                    df = df_all[df_all['department'] == selected_manage_dept_tab3]
                else:
                    df = df_all
                
                if df.empty:
                    st.info("ไม่มีรายการคิวนัดหมายตามแผนกที่เลือก")
                else:
                    # ค้นหา
                    search_query = st.text_input("ค้นหาด่วน (ชื่อผู้รับบริการ, เบอร์โทร, หรือเลขบัตรประชาชน):")
                    if search_query.strip():
                        df_show = df[
                            df['name'].str.contains(search_query, case=False, na=False) |
                            df['phone'].str.contains(search_query, case=False, na=False) |
                            df['cid'].str.contains(search_query, case=False, na=False)
                        ]
                    else:
                        df_show = df
                        
                    if df_show.empty:
                        st.info("ไม่พบข้อมูลการจองคิวตามที่ค้นหา")
                    else:
                        # ฟอร์แมตหัวตารางแสดงสิทธิ์
                        df_show_display = df_show[[
                            "id", "department", "name", "phone", "cid", "service_type", 
                            "appointment_date", "appointment_time", "note"
                        ]].copy()
                        
                        # แปลงแผนกให้อ่านง่าย
                        dept_display_map = {
                            "dental": "ทันตกรรม 🦷",
                            "thai_traditional": "แพทย์แผนไทย 🍃",
                            "physical_therapy": "กายภาพบำบัด ♿"
                        }
                        df_show_display['department'] = df_show_display['department'].map(dept_display_map)
                        
                        df_show_display.columns = [
                            "รหัสนัด", "แผนก", "ชื่อ-นามสกุล", "เบอร์โทร", "เลขบัตรประชาชน", 
                            "ประเภทบริการ", "วันที่นัดหมาย", "เวลานัด", "หมายเหตุ"
                        ]
                        
                        st.dataframe(df_show_display, use_container_width=True, hide_index=True)
                        
                        # ส่วนยกเลิกคิวนัดหมาย
                        st.divider()
                        st.write("#### 🗑️ ยกเลิกคิวนัดหมายผู้เข้าบริการ")
                        
                        # ตัวเลือกสำหรับการยกเลิก
                        cancel_options = {
                            f"รหัส #{row['id']} - คุณ{row['name']} (วันที่ {row['appointment_date']} เวลา {row['appointment_time']})": row['id']
                            for _, row in df_show.iterrows()
                        }
                        
                        if cancel_options:
                            selected_cancel_label = st.selectbox(
                                "เลือกนัดหมายที่ต้องการลบออกจากระบบ:",
                                list(cancel_options.keys())
                            )
                            selected_cancel_id = cancel_options[selected_cancel_label]
                            
                            if st.button("ยืนยันยกเลิกและเปิดเวลากลับคืนระบบ 🗑️", type="primary", use_container_width=True):
                                success, message = cancel_appointment_db(selected_cancel_id)
                                if success:
                                    st.success(f"ดำเนินการเรียบร้อยแล้ว: {message}")
                                    st.rerun()
                                else:
                                    st.error(f"ไม่สามารถดำเนินการลบได้เนื่องจาก: {message}")
                        else:
                            st.caption("ไม่มีรายการให้ยกเลิก")
 
        # --- TAB 4: MANAGE SERVICES ---
        with tab_services:
            st.write("### ⚙️ จัดการรายการบริการ (เพิ่ม/แก้ไข/ลบ)")
            
            depts_list = fetch_all_departments()
            manage_dept_choices = [f"{d['display_name']} ({d['key']})" for d in depts_list]
            
            if not depts_list:
                st.warning("⚠️ ไม่มีแผนกเปิดให้บริการในระบบ")
                selected_manage_dept = "dental"
            else:
                manage_dept = st.selectbox(
                    "เลือกแผนกบริการที่ต้องการจัดการ:",
                    manage_dept_choices,
                    key="staff_manage_services_dept"
                )
                selected_manage_dept = depts_list[manage_dept_choices.index(manage_dept)]["key"]
            
            # โหลดบริการของแผนกที่เลือก
            current_services = fetch_services(selected_manage_dept)
            
            # แบ่งส่วน Add, Edit, Delete, ตั้งค่าคิว และตั้งค่าปฏิทินด้วย subtabs
            subtab_list, subtab_add, subtab_edit, subtab_delete, subtab_schedule, subtab_gcal = st.tabs([
                "📋 รายการบริการปัจจุบัน",
                "➕ เพิ่มบริการใหม่",
                "✏️ แก้ไขบริการที่มีอยู่",
                "❌ ลบบริการ",
                "📅 จัดการวันและเวลาให้บริการ",
                "📅 ตั้งค่า Google Calendar"
            ])
            
            with subtab_list:
                st.write(f"#### รายการบริการของ{manage_dept}ทั้งหมดในระบบ")
                if not current_services:
                    st.info("ไม่มีรายการบริการในระบบในขณะนี้")
                else:
                    for s in current_services:
                        with st.container():
                            st.markdown(f"""
                            <div class="service-card" style="margin-bottom: 10px;">
                                <h5>{s.get('icon', '🦷')} {s.get('title', '')} (รหัส: {s.get('id', '')})</h5>
                                <p style="margin: 0; color: #666; font-size: 0.9rem;">{s.get('description', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
            with subtab_add:
                st.write(f"#### เพิ่มบริการใหม่ของ{manage_dept}")
                with st.form("add_service_form"):
                    new_title = st.text_input("ชื่อบริการ (เช่น ขูดหินปูน, นวดแผนไทย):")
                    new_desc = st.text_area("คำอธิบายบริการ:")
                    
                    default_icon_map = {
                        "dental": "🦷",
                        "thai_traditional": "💆‍♂️",
                        "physical_therapy": "🚶‍♂️"
                    }
                    new_icon = st.text_input("อีโมจิไอคอน:", value=default_icon_map[selected_manage_dept])
                    
                    add_submitted = st.form_submit_button("➕ บันทึกบริการใหม่", use_container_width=True)
                    if add_submitted:
                        if not new_title.strip():
                            st.error("กรุณาระบุชื่อบริการ")
                        else:
                            success, message = add_service_db(selected_manage_dept, new_title.strip(), new_desc.strip(), new_icon.strip())
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                                
            with subtab_edit:
                st.write(f"#### แก้ไขบริการของ{manage_dept}")
                if not current_services:
                    st.info("ไม่มีรายการบริการให้แก้ไข")
                else:
                    service_edit_options = {
                        f"{s.get('icon', '🦷')} {s.get('title', '')}": s
                        for s in current_services
                    }
                    selected_edit_label = st.selectbox(
                        "เลือกบริการที่ต้องการแก้ไข:",
                        list(service_edit_options.keys()),
                        key="sb_edit_service"
                    )
                    selected_service_obj = service_edit_options[selected_edit_label]
                    
                    with st.form("edit_service_form"):
                        edit_title = st.text_input("ชื่อบริการ:", value=selected_service_obj.get("title", ""))
                        edit_desc = st.text_area("คำอธิบายบริการ:", value=selected_service_obj.get("description", ""))
                        edit_icon = st.text_input("อีโมจิไอคอน:", value=selected_service_obj.get("icon", "🦷"))
                        
                        edit_submitted = st.form_submit_button("✏️ บันทึกการแก้ไข", use_container_width=True)
                        if edit_submitted:
                            if not edit_title.strip():
                                st.error("กรุณาระบุชื่อบริการ")
                            else:
                                success, message = update_service_db(
                                    selected_service_obj["id"],
                                    selected_manage_dept,
                                    edit_title.strip(),
                                    edit_desc.strip(),
                                    edit_icon.strip()
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                                    
            with subtab_delete:
                st.write(f"#### ลบบริการออกจากระบบ")
                if not current_services:
                    st.info("ไม่มีรายการบริการให้ลบ")
                else:
                    service_del_options = {
                        f"{s.get('icon', '🦷')} {s.get('title', '')}": s
                        for s in current_services
                    }
                    selected_del_label = st.selectbox(
                        "เลือกบริการที่ต้องการลบ:",
                        list(service_del_options.keys()),
                        key="sb_del_service"
                    )
                    selected_del_obj = service_del_options[selected_del_label]
                    
                    st.warning(f"⚠️ คำเตือน: คุณแน่ใจหรือไม่ว่าต้องการลบบริการ '{selected_del_obj.get('title')}' ออกจากระบบ?")
                    
                    if st.button("❌ ยืนยันการลบบริการ", type="primary", use_container_width=True):
                        success, message = delete_service_db(selected_del_obj["id"])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            
            with subtab_schedule:
                st.write(f"#### ⚙️ จัดการเวลาและวันให้บริการของ {manage_dept}")
                
                # ดึงการตั้งค่าปัจจุบัน
                dept_settings = get_settings(selected_manage_dept)
                
                # 1. ระยะเวลาเปิดให้จองล่วงหน้า
                cfg_range = st.number_input(
                    "ระยะจำนวนวันเปิดให้จองล่วงหน้า (วัน):",
                    min_value=1,
                    max_value=365,
                    value=dept_settings.get("booking_range_days", 30),
                    help="กำหนดว่าคนไข้สามารถทำนัดหมายล่วงหน้าได้กี่วันนับจากวันนี้",
                    key=f"cfg_range_{selected_manage_dept}"
                )
                
                # 2. จำนวนคิวสูงสุดต่อสล็อตเวลา
                cfg_capacity = st.number_input(
                    "จำนวนผู้รับบริการสูงสุดต่อช่วงเวลา (คิวต่อสล็อต):",
                    min_value=1,
                    max_value=20,
                    value=dept_settings.get("max_bookings_per_slot", 1),
                    help="กำหนดว่าในหนึ่งช่วงเวลา (เช่น 09:00 น.) สามารถรองรับคนไข้ได้พร้อมกันกี่คน",
                    key=f"cfg_capacity_{selected_manage_dept}"
                )
                
                st.divider()
                
                # 3. วันให้บริการประจำสัปดาห์
                st.write("**📅 วันเปิดให้บริการประจำสัปดาห์**")
                days_options = {
                    "วันจันทร์": 0,
                    "วันอังคาร": 1,
                    "วันพุธ": 2,
                    "วันพฤหัสบดี": 3,
                    "วันศุกร์": 4,
                    "วันเสาร์": 5,
                    "วันอาทิตย์": 6
                }
                current_working_days = dept_settings.get("working_days", [0, 1, 2, 3, 4])
                
                # แสดง checkbox 7 วันแยกเป็นแถวแนวนอน
                cols_days = st.columns(7)
                selected_working_days = []
                for label, val in days_options.items():
                    col_idx = val
                    with cols_days[col_idx]:
                        checked = val in current_working_days
                        if st.checkbox(label[3:], value=checked, key=f"wd_{selected_manage_dept}_{val}"):
                            selected_working_days.append(val)
                
                st.divider()
                
                # 4. ตารางเวลาให้บริการ (แบบ Slot Builder)
                st.write("**⏰ ตารางเวลาและกฎให้บริการรายสล็อต (Time Slots & Capacity Rules)**")
                st.info("💡 สามารถกำหนดเวลา จำนวนคิวที่รับ และบริการที่รับจองในสล็อตเวลานั้นๆ ได้ หากต้องการให้รับจองได้ทุกบริการ ให้ปล่อยช่อง 'บริการที่เปิดรับ' เป็นค่าว่าง")

                # ดึงบริการทั้งหมดของแผนกนี้มาให้เลือก
                dept_services = fetch_services(selected_manage_dept)
                service_choices = [s.get("title", "") for s in dept_services if s.get("title")]
                
                # โหลดการตั้งค่าสล็อตในปัจจุบัน
                current_slot_configs = dept_settings.get("slot_configs", [])
                
                # หากยังไม่มี slot_configs ในระบบ (พึ่งอัปเกรดจากระบบเดิม) ให้จำลองแปลงข้อมูลจาก time_slots และ max_bookings_per_slot ของเก่า
                if not current_slot_configs:
                    old_slots = dept_settings.get("time_slots", ["08:30", "09:00", "09:30", "10:00", "13:30", "14:00", "14:30", "15:30", "16:00"])
                    old_cap = dept_settings.get("max_bookings_per_slot", 1)
                    current_slot_configs = [{"time": t, "capacity": old_cap, "allowed_services": []} for t in old_slots]

                # สร้าง Session State สำหรับเก็บข้อมูลการอีดิตรายสล็อตแยกตามแผนกชั่วคราว
                state_slots_key = f"editing_slots_config_{selected_manage_dept}"
                if state_slots_key not in st.session_state:
                    st.session_state[state_slots_key] = current_slot_configs

                # หัวตารางจำลอง
                col_header_t, col_header_c, col_header_s, col_header_del = st.columns([2, 2, 5, 1])
                with col_header_t:
                    st.write("**รอบเวลา**")
                with col_header_c:
                    st.write("**จำนวนคิว**")
                with col_header_s:
                    st.write("**บริการที่เปิดรับ**")
                with col_header_del:
                    st.write("**ลบ**")

                updated_slot_configs = []
                for idx, slot_item in enumerate(st.session_state[state_slots_key]):
                    col_t, col_c, col_s, col_del = st.columns([2, 2, 5, 1])
                    
                    with col_t:
                        # ช่องกรอกเวลา (HH:MM)
                        s_time = st.text_input(
                            "เวลา",
                            value=slot_item.get("time", ""),
                            key=f"item_time_{selected_manage_dept}_{idx}",
                            label_visibility="collapsed",
                            placeholder="เช่น 09:00"
                        ).strip()
                    
                    with col_c:
                        # จำนวนคิวสูงสุด
                        s_cap = st.number_input(
                            "จำนวนคิว",
                            min_value=1,
                            max_value=50,
                            value=int(slot_item.get("capacity", 1)),
                            key=f"item_cap_{selected_manage_dept}_{idx}",
                            label_visibility="collapsed"
                        )
                        
                    with col_s:
                        # มัลติซีเล็กเลือกบริการที่ต้องการจำกัด
                        # ดึงบริการที่มีอยู่ใน choices เท่านั้น
                        default_allowed = [s for s in slot_item.get("allowed_services", []) if s in service_choices]
                        s_services = st.multiselect(
                            "บริการ",
                            options=service_choices,
                            default=default_allowed,
                            key=f"item_services_{selected_manage_dept}_{idx}",
                            label_visibility="collapsed",
                            placeholder="เปิดรับทุกบริการ (คลิกเพื่อระบุเฉพาะเจาะจง)"
                        )
                        
                    with col_del:
                        # ปุ่มลบสล็อต
                        if st.button("🗑️", key=f"btn_del_item_{selected_manage_dept}_{idx}", use_container_width=True):
                            st.session_state[state_slots_key].pop(idx)
                            st.rerun()
                            
                    updated_slot_configs.append({
                        "time": s_time,
                        "capacity": s_cap,
                        "allowed_services": s_services
                    })
                    
                # ปุ่มเพิ่มรอบเวลาใหม่
                col_add_btn, _ = st.columns([1, 2])
                with col_add_btn:
                    if st.button("➕ เพิ่มรอบเวลาใหม่", key=f"btn_add_slot_item_{selected_manage_dept}", use_container_width=True):
                        # ใช้เวลาเริ่มต้นเป็นเวลาเที่ยง
                        st.session_state[state_slots_key].append({
                            "time": "12:00",
                            "capacity": 1,
                            "allowed_services": []
                        })
                        st.rerun()

                # เรียงลำดับตามรอบเวลาเพื่อความเป็นระเบียบเรียบร้อยก่อนบันทึก
                # กรองค่าว่างและจัดรูปแบบให้ถูกต้องก่อนนำไปแปลงเป็น time_slots รายการใหญ่
                final_slot_configs = []
                for s in updated_slot_configs:
                    if s["time"] and ":" in s["time"]:
                        # ทำความสะอาดรูปแบบเวลา (เช่น 9:00 -> 09:00)
                        parts = s["time"].split(":")
                        try:
                            h = int(parts[0])
                            m = int(parts[1])
                            time_cleaned = f"{h:02d}:{m:02d}"
                            s["time"] = time_cleaned
                            final_slot_configs.append(s)
                        except ValueError:
                            pass
                            
                # จัดเรียงตามเวลา
                final_slot_configs = sorted(final_slot_configs, key=lambda x: x["time"])
                
                # รายชื่อ time_slots แบบข้อความ เพื่อ Backward Compatibility ในฟิลด์เดิมของ DB
                parsed_slots = [s["time"] for s in final_slot_configs]
                
                st.divider()
                
                # 5. วันปิดทำการพิเศษ (Closed Dates)
                st.write("**🚫 วันปิดทำการพิเศษ / วันหยุดแผนก**")
                current_closed_dates = dept_settings.get("closed_dates", [])
                
                col_add_closed, col_list_closed = st.columns([1, 1])
                
                with col_add_closed:
                    st.write("เพิ่มวันหยุดพิเศษ:")
                    new_closed_date = st.date_input(
                        "เลือกวันที่ต้องการหยุดให้บริการ:",
                        min_value=datetime.date.today(),
                        key=f"add_closed_date_{selected_manage_dept}"
                    )
                    new_closed_str = new_closed_date.isoformat()
                    
                    if st.button("➕ เพิ่มเป็นวันหยุดพิเศษ", key=f"btn_add_closed_{selected_manage_dept}", use_container_width=True):
                        if new_closed_str not in current_closed_dates:
                            current_closed_dates.append(new_closed_str)
                            # อัปเดต DB ทันทีเพื่อให้แสดงผลในลิสต์โดยไม่ต้องกดเซฟหลัก
                            update_settings_db(
                                selected_manage_dept,
                                cfg_range,
                                selected_working_days,
                                current_closed_dates,
                                parsed_slots,
                                cfg_capacity,
                                final_slot_configs
                            )
                            st.success(f"เพิ่มวันที่ {format_thai_date(new_closed_date)} เป็นวันหยุดเรียบร้อยแล้ว")
                            st.rerun()
                        else:
                            st.warning("วันนี้อยู่ในรายการวันหยุดพิเศษอยู่แล้ว")
                
                with col_list_closed:
                    st.write("รายการวันหยุดพิเศษปัจจุบัน:")
                    if not current_closed_dates:
                        st.caption("ไม่มีวันหยุดพิเศษ")
                    else:
                        for c_date_str in sorted(current_closed_dates):
                            c_date = datetime.date.fromisoformat(c_date_str)
                            col_c_text, col_c_btn = st.columns([3, 1])
                            with col_c_text:
                                st.write(f"🛑 {format_thai_date(c_date)}")
                            with col_c_btn:
                                if st.button("🗑️", key=f"del_closed_{selected_manage_dept}_{c_date_str}"):
                                    current_closed_dates.remove(c_date_str)
                                    # อัปเดต DB ทันที
                                    update_settings_db(
                                        selected_manage_dept,
                                        cfg_range,
                                        selected_working_days,
                                        current_closed_dates,
                                        parsed_slots,
                                        cfg_capacity,
                                        final_slot_configs
                                    )
                                    st.success("นำวันหยุดออกแล้ว")
                                    st.rerun()
                                    
                st.divider()
                
                # ปุ่มบันทึกข้อมูลหลัก
                if st.button("💾 บันทึกการตั้งค่าตารางและวันให้บริการของแผนก", key=f"btn_save_settings_{selected_manage_dept}", type="primary", use_container_width=True):
                    if not selected_working_days:
                        st.error("❌ ต้องเลือกวันเปิดทำการประจำสัปดาห์อย่างน้อย 1 วัน")
                    elif not parsed_slots:
                        st.error("❌ ต้องมีช่วงเวลาเปิดให้บริการอย่างน้อย 1 สล็อตเวลา")
                    else:
                        success, message = update_settings_db(
                            selected_manage_dept,
                            cfg_range,
                            selected_working_days,
                            current_closed_dates,
                            parsed_slots,
                            cfg_capacity,
                            final_slot_configs
                        )
                        if success:
                            if state_slots_key in st.session_state:
                                del st.session_state[state_slots_key]
                            st.success(f"🟢 {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            
            with subtab_gcal:
                st.write(f"#### 📅 ตั้งค่าการเชื่อมโยง Google Calendar ของ {manage_dept}")
                
                dept_cal_id = dept_cal_map.get(selected_manage_dept, "")
                
                if dept_cal_id and "xxxxxxxx" not in dept_cal_id:
                    st.success(f"🟢 เชื่อมโยงกับ Google Calendar ID ของแผนกนี้แล้ว")
                    st.code(dept_cal_id, language="text")
                    st.caption("💡 คนไข้ที่ลงนัดหมายในแผนกนี้ จะสามารถบันทึกนัดหมายลงในปฏิทินกลางของแผนกนี้โดยอัตโนมัติ")
                else:
                    st.warning("⚠️ แผนกนี้ยังไม่ได้ตั้งค่า Google Calendar ID เฉพาะ หรือใช้ค่าสาธิตเริ่มต้น (จะใช้ปฏิทินเริ่มต้นของผู้ใช้)")
                    
                st.markdown("""
                ---
                **⚙️ วิธีการตั้งค่าปฏิทินแยกตามแผนก:**
                1. ล็อกอินเข้าสู่บัญชี Google ของแผนก หรือใช้บัญชี รพ.สต.
                2. ไปที่ **Google Calendar** และกด **"สร้างปฏิทินใหม่"** (Create new calendar) ตั้งชื่อให้สอดคล้องกับแผนก เช่น *ทันตกรรม รพ.สต.ท่าเกษม*
                3. ไปที่การตั้งค่าปฏิทินนั้น และทำเครื่องหมายถูกที่ **"แชร์แบบสาธิต/เปิดเผยต่อสาธารณะ"** (Make available to public) เพื่อให้ผู้รับบริการภายนอกสามารถเปิดเข้าถึงได้
                4. เลื่อนลงมาที่หัวข้อ **"รวมปฏิทิน"** (Integrate calendar) คัดลอก **รหัสปฏิทิน (Calendar ID)** เช่น:
                   `xxxxxxxxxxxxxxxx@group.calendar.google.com`
                5. นำรหัสปฏิทินไปใส่ในไฟล์คอนฟิก `.streamlit/secrets.toml` ของคุณดังนี้:
                ```toml
                GOOGLE_CALENDAR_ID_DENTAL = "รหัสปฏิทินทันตกรรม"
                GOOGLE_CALENDAR_ID_THAI = "รหัสปฏิทินแพทย์แผนไทย"
                GOOGLE_CALENDAR_ID_PHYSICAL = "รหัสปฏิทินกายภาพบำบัด"
                ```
                """)

        # --- TAB 5: MANAGE DEPARTMENTS ---
        with tab_depts:
            st.write("### 🏥 จัดการแผนกบริการ (เพิ่ม / แก้ไข / ลบ)")
            
            depts_in_db = fetch_all_departments()
            
            sub_dept_list, sub_dept_add, sub_dept_edit, sub_dept_delete = st.tabs([
                "📋 รายการแผนกบริการในปัจจุบัน",
                "➕ เพิ่มแผนกใหม่",
                "✏️ แก้ไขแผนกที่มีอยู่",
                "🗑️ ลบแผนกออกจากระบบ"
            ])
            
            with sub_dept_list:
                st.write("#### รายชื่อแผนกที่เปิดให้บริการผ่านไลน์")
                if not depts_in_db:
                    st.info("ไม่มีแผนกในระบบในขณะนี้")
                else:
                    for d in depts_in_db:
                        st.markdown(f"""
                        <div style="padding: 1rem; border-left: 5px solid {d['theme_color']}; background-color: #F8F9FA; border-radius: 8px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 15px;">
                                <img src="{d['banner_img']}" width="40">
                                <div>
                                    <strong style="font-size: 1.1rem; color: #240046;">{d['display_name']}</strong><br>
                                    <span style="font-size: 0.85rem; color: #6C757D;">รหัสอ้างอิง: <code>{d['key']}</code> | รหัสสี: <span style="color: {d['theme_color']}; font-weight: bold;">{d['theme_color']}</span></span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            with sub_dept_add:
                st.write("#### ➕ เพิ่มแผนกบริการใหม่")
                with st.form("add_dept_form"):
                    new_dept_key = st.text_input(
                        "รหัสแผนกภาษาอังกฤษ (เช่น pediatrics, general_medicine):", 
                        placeholder="ห้ามมีช่องว่าง ใช้ภาษาอังกฤษตัวเล็กเท่านั้น"
                    ).strip().lower()
                    
                    new_dept_name = st.text_input(
                        "ชื่อแผนกบริการภาษาไทย (เช่น แผนกกุมารเวชกรรม, คลินิกโรคทั่วไป):", 
                        placeholder="ระบุชื่อภาษาไทยที่แสดงให้คนไข้เห็น"
                    )
                    
                    new_dept_color = st.color_picker("เลือกสีหลักของแผนก (Theme Color):", value="#7B2CBF")
                    
                    icon_options = {
                        "🏥 โรงพยาบาล/บริการทั่วไป": "https://img.icons8.com/color/144/hospital.png",
                        "🦷 ทันตกรรม (ฟัน)": "https://img.icons8.com/color/144/tooth.png",
                        "🍃 แพทย์แผนไทย (ครกสมุนไพร)": "https://img.icons8.com/color/144/mortar-and-pestle.png",
                        "♿ กายภาพบำบัด (วีลแชร์)": "https://img.icons8.com/color/144/physical-therapy.png",
                        "💉 วัคซีน (เข็มฉีดยา)": "https://img.icons8.com/color/144/syringe.png",
                        "💊 ร้านขายยา/เภสัช": "https://img.icons8.com/color/144/pill.png",
                        "❤️ หัวใจ/ตรวจสุขภาพ": "https://img.icons8.com/color/144/heart-monitor.png"
                    }
                    
                    selected_preset = st.selectbox("เลือกไอคอนแผนกจากรายการแนะนำ:", list(icon_options.keys()))
                    custom_dept_img = st.text_input(
                        "หรือระบุ URL รูปภาพไอคอนอื่นๆ (เว้นว่างไว้จะใช้ไอคอนแนะนำที่เลือกด้านบน):",
                        placeholder="https://..."
                    ).strip()
                    
                    add_dept_submitted = st.form_submit_button("➕ บันทึกแผนกใหม่", use_container_width=True)
                    if add_dept_submitted:
                        final_img = custom_dept_img if custom_dept_img else icon_options[selected_preset]
                        if not new_dept_key or not new_dept_name:
                            st.error("❌ กรุณากรอกรหัสแผนกและชื่อแผนกบริการให้ครบถ้วน")
                        elif not new_dept_key.isalnum() and "_" not in new_dept_key:
                            st.error("❌ รหัสแผนกต้องประกอบด้วยตัวอักษรภาษาอังกฤษหรือตัวเลข และเครื่องหมาย _ เท่านั้น")
                        else:
                            success, message = create_department_db(new_dept_key, new_dept_name, new_dept_color, final_img)
                            if success:
                                st.success(f"🟢 {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                                
            with sub_dept_edit:
                st.write("#### ✏️ แก้ไขแผนกบริการที่มีอยู่")
                if not depts_in_db:
                    st.info("ไม่มีแผนกให้แก้ไขในระบบ")
                else:
                    edit_dept_options = {f"{d['display_name']} ({d['key']})": d for d in depts_in_db}
                    selected_edit_label = st.selectbox(
                        "เลือกแผนกที่ต้องการแก้ไข:",
                        list(edit_dept_options.keys()),
                        key="sb_edit_dept_select"
                    )
                    selected_edit_dept = edit_dept_options[selected_edit_label]
                    
                    with st.form("edit_dept_form"):
                        edit_dept_name = st.text_input(
                            "ชื่อแผนกบริการภาษาไทย:", 
                            value=selected_edit_dept.get("display_name", "")
                        )
                        edit_dept_color = st.color_picker(
                            "สีธีมหลักของแผนก:", 
                            value=selected_edit_dept.get("theme_color", "#7B2CBF")
                        )
                        edit_dept_img = st.text_input(
                            "ลิงก์ URL รูปภาพไอคอนแผนก:", 
                            value=selected_edit_dept.get("banner_img", "")
                        )
                        
                        edit_dept_submitted = st.form_submit_button("✏️ บันทึกการแก้ไขแผนก", use_container_width=True)
                        if edit_dept_submitted:
                            if not edit_dept_name.strip():
                                st.error("❌ กรุณากรอกชื่อแผนกบริการ")
                            else:
                                success, message = update_department_db(
                                    selected_edit_dept["key"],
                                    edit_dept_name.strip(),
                                    edit_dept_color,
                                    edit_dept_img.strip()
                                )
                                if success:
                                    st.success(f"🟢 {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                                    
            with sub_dept_delete:
                st.write("#### 🗑️ ลบแผนกออกจากระบบ")
                if not depts_in_db:
                    st.info("ไม่มีแผนกให้ลบในขณะนี้")
                else:
                    del_dept_options = {f"{d['display_name']} ({d['key']})": d for d in depts_in_db}
                    selected_del_label = st.selectbox(
                        "เลือกแผนกที่ต้องการลบ:",
                        list(del_dept_options.keys()),
                        key="sb_del_dept_select"
                    )
                    selected_del_dept = del_dept_options[selected_del_label]
                    
                    st.warning(f"⚠️ การดำเนินการนี้จะลบแผนก '{selected_del_dept['display_name']}' ออกจากตารางตั้งค่า และจะลบข้อมูลบริการรักษาทั้งหมดที่เกี่ยวข้องกับแผนกนี้! โปรดตรวจสอบให้แน่ใจก่อนทำการลบ")
                    
                    confirm_del_text = st.text_input(
                        f"พิมพ์คำว่า `{selected_del_dept['key']}` ในช่องด้านล่างเพื่อยืนยันสิทธิ์การลบ:",
                        placeholder="พิมพ์เพื่อยืนยัน"
                    ).strip().lower()
                    
                    if st.button("🗑️ ยืนยันการลบแผนกบริการ", type="primary", use_container_width=True):
                        if confirm_del_text != selected_del_dept['key']:
                            st.error("❌ คำยืนยันไม่ถูกต้อง กรุณากรอกรหัสแผนกบริการให้ตรงกัน")
                        else:
                            success, message = delete_department_db(selected_del_dept['key'])
                            if success:
                                st.success(f"🟢 {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

# ----------------- Footer -----------------
st.divider()
st.caption("ระบบลงทะเบียนนัดหมายออนไลน์ รพ.สต.ท่าเกษม © 2026. พัฒนาร่วมกับ LINE Official Account")
