import mysql.connector
from faker import Faker
import random

# Khởi tạo Faker với ngôn ngữ Tiếng Việt
fake = Faker('vi_VN')

# 1. Kết nối với MySQL (Em nhớ thay đổi mật khẩu và tên database của em)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@Poh12345",
    database="final_project_dbms"
)
cursor = db.cursor()

NUM_ROWS = 510

print("Bắt đầu tạo và Insert dữ liệu...")

venue_data = [(fake.company() + " Convention Center", fake.address()) for _ in range(NUM_ROWS)]
cursor.executemany("INSERT INTO venues (VenueName, Address) VALUES (%s, %s)", venue_data)
db.commit()

organizer_data = [(fake.company(), fake.address(), fake.phone_number()[:15]) for _ in range(NUM_ROWS)]
cursor.executemany("INSERT INTO organizers (OrganizerName, Address, PhoneNumber) VALUES (%s, %s, %s)", organizer_data)
db.commit()

guest_data = [(fake.name(), fake.email(), fake.phone_number()[:15]) for _ in range(NUM_ROWS)]
cursor.executemany("INSERT INTO guests (GuestName, Email, PhoneNumber) VALUES (%s, %s, %s)", guest_data)
db.commit()

cursor.execute("SELECT VenueID FROM venues")
venue_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT OrganizerID FROM organizers")
organizer_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT GuestID FROM guests")
guest_ids = [row[0] for row in cursor.fetchall()]

event_data = []
for _ in range(NUM_ROWS):
    event_name = fake.catch_phrase() + " Event"
    event_date = fake.future_date(end_date="+1y")
    v_id = random.choice(venue_ids)
    o_id = random.choice(organizer_ids)
    event_data.append((event_name, event_date, v_id, o_id))

cursor.executemany("INSERT INTO events (EventName, EventDate, VenueID, OrganizerID) VALUES (%s, %s, %s, %s)", event_data)
db.commit()

cursor.execute("SELECT EventID FROM events")
event_ids = [row[0] for row in cursor.fetchall()]

registration_pairs = set()
while len(registration_pairs) < NUM_ROWS:
    e_id = random.choice(event_ids)
    g_id = random.choice(guest_ids)
    registration_pairs.add((e_id, g_id))

registration_data = []
for e_id, g_id in registration_pairs:
    reg_date = fake.past_date()
    registration_data.append((e_id, g_id, reg_date))

cursor.executemany("INSERT INTO registrations (EventID, GuestID, RegistrationDate) VALUES (%s, %s, %s)", registration_data)
db.commit()

print(f"Đã insert thành công {NUM_ROWS} dòng cho mỗi bảng!")

cursor.close()
db.close()