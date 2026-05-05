from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)

# --- HÀM KẾT NỐI DATABASE ---
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',         # Sếp nhớ đổi lại cho đúng máy sếp nhé
        password='@Poh12345', # Đổi pass chỗ này nữa
        database='final_project_dbms'
    )

# 1. TRANG CHỦ (Chính là cái sếp đang bị thiếu gây ra lỗi 404)
@app.route('/')
def home():
    return render_template('index.html')

# 2. XỬ LÝ LÚC BẤM NÚT ĐĂNG NHẬP
@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    if role == 'staff':
        return redirect(url_for('staff_dashboard'))
    elif role == 'guest':
        return redirect(url_for('guest_dashboard'))
    elif role == 'organizer':
        return redirect(url_for('organizer_dashboard'))
    return redirect(url_for('home'))

# --- TRANG GUEST (Đã thêm tính năng Phân trang) ---
@app.route('/guest')
def guest_dashboard():
    # 1. Lấy số trang hiện tại từ URL (Ví dụ: /guest?page=2), mặc định là trang 1
    page = request.args.get('page', 1, type=int)
    per_page = 15 # Hiển thị 15 sự kiện/trang (vừa vặn lưới 5x3)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 2. Đếm TỔNG SỐ sự kiện đang có để chia số trang
        cursor.execute("SELECT COUNT(*) FROM Events WHERE EventDate >= CURDATE()")
        total_events = cursor.fetchone()[0]
        
        # Công thức tính tổng số trang (làm tròn lên)
        total_pages = (total_events + per_page - 1) // per_page 
        if total_pages == 0: total_pages = 1 # Ít nhất phải có 1 trang

        # 3. Tính toán vị trí OFFSET và bốc dữ liệu của trang đó lên
        offset = (page - 1) * per_page
        
        sql = """
            SELECT e.EventID, e.EventName, v.VenueName 
            FROM Events e
            LEFT JOIN Venues v ON e.VenueID = v.VenueID
            WHERE e.EventDate >= CURDATE()
            ORDER BY e.EventDate ASC
            LIMIT %s OFFSET %s;
        """
        cursor.execute(sql, (per_page, offset))
        records = cursor.fetchall()
        
        real_events = []
        for row in records:
            real_events.append({
                "id": row[0],
                "name": row[1],
                "venue": row[2] if row[2] else "Chưa xếp rạp",
                "rate": "Hot 🔥"
            })

    except Exception as e:
        print(f"❌ Lỗi trang Guest: {e}")
        real_events, total_pages = [], 1
    finally:
        cursor.close()
        conn.close()

    # --- THUẬT TOÁN PHÂN TRANG KIỂU GOOGLE ---
    page_iter = []
    if total_pages <= 7:
        # Nếu ít hơn 7 trang, hiện hết không cần giấu
        page_iter = list(range(1, total_pages + 1))
    else:
        # Nếu đang ở những trang đầu (vd: 1, 2, 3, 4)
        if page <= 4:
            page_iter = [1, 2, 3, 4, 5, '...', total_pages]
        # Nếu đang ở những trang cuối (vd: 17, 18, 19, 20)
        elif page >= total_pages - 3:
            page_iter = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        # Nếu đang ở giữa (vd: trang 10)
        else:
            page_iter = [1, '...', page - 1, page, page + 1, '...', total_pages]

    # Bắn thêm biến page_iter sang cho HTML vẽ giao diện
    return render_template('guest.html', events=real_events, current_page=page, total_pages=total_pages, page_iter=page_iter)
   

# 4. TRANG STAFF
@app.route('/staff')
def staff_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Bốc toàn bộ khách đã đăng ký sự kiện lên
        sql = """
            SELECT g.GuestID, g.GuestName, r.AttendanceStatus, g.Email
            FROM Registrations r
            JOIN Guests g ON r.GuestID = g.GuestID
            ORDER BY r.RegistrationDate DESC
            LIMIT 50;
        """
        cursor.execute(sql)
        records = cursor.fetchall()
        
        real_guests = []
        for row in records:
            real_guests.append({
                "id": row[0],
                "name": row[1],
                "status": row[2], # Trả về 'Pending' hoặc 'Attended'
                "email": row[3]
            })
    except Exception as e:
        print(f"❌ Lỗi trang Staff: {e}")
        real_guests = []
    finally:
        cursor.close()
        conn.close()

    return render_template('staff.html', guests=real_guests)

# 5. TRANG ORGANIZER
@app.route('/organizer')
def organizer_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Lấy danh sách Địa điểm (để điền vào form Tạo mới)
        cursor.execute("SELECT VenueID, VenueName FROM Venues")
        venues = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        
        # 2. Lấy danh sách Sự kiện (để điền vào form Chỉnh sửa)
        cursor.execute("SELECT EventID, EventName FROM Events ORDER BY EventDate DESC")
        events = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Lỗi trang Organizer: {e}")
        venues, events = [], []
    finally:
        cursor.close()
        conn.close()

    return render_template('organizer.html', venues=venues, events=events)

# --- API TÌM KIẾM GỢI Ý (AUTOCOMPLETE) ---
@app.route('/api/search_events')
def search_events():
    keyword = request.args.get('q', '')
    
    # Nếu chưa gõ gì thì trả về danh sách rỗng luôn cho nhẹ server
    if len(keyword) < 1:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Lệnh SQL tìm kiếm gần đúng (LIKE) với từ khóa khách gõ, lấy max 5 kết quả
        sql = "SELECT EventID, EventName FROM Events WHERE EventName LIKE %s LIMIT 5;"
        cursor.execute(sql, (f"%{keyword}%",))
        records = cursor.fetchall()
        
        # Đóng gói thành dạng JSON (định dạng chuẩn để giao tiếp Frontend-Backend)
        results = [{"id": row[0], "name": row[1]} for row in records]
        return jsonify(results)
    except Exception as e:
        print(f"❌ Lỗi API tìm kiếm: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

# --- API XỬ LÝ ĐĂNG KÝ SỰ KIỆN ---
@app.route('/api/register_event', methods=['POST'])
def register_event():
    # 1. Lấy dữ liệu từ form HTML gửi lên
    event_id = request.form.get('event_id')
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 2. Tìm xem khách này từng đăng ký hệ thống chưa (dựa vào Email)
        cursor.execute("SELECT GuestID FROM Guests WHERE Email = %s", (email,))
        guest = cursor.fetchone()
        
        if guest:
            guest_id = guest[0] # Khách cũ
        else:
            # Khách mới -> Thêm vào bảng Guests
            cursor.execute("INSERT INTO Guests (GuestName, Email, PhoneNumber) VALUES (%s, %s, %s)", (name, email, phone))
            guest_id = cursor.lastrowid # Lấy ID vừa được tạo tự động

        # 3. Kiểm tra xem khách đã đăng ký sự kiện này trước đó chưa (Chống spam)
        cursor.execute("SELECT * FROM Registrations WHERE GuestID = %s AND EventID = %s", (guest_id, event_id))
        if cursor.fetchone():
            return jsonify({'status': 'warning', 'message': 'Bạn đã đăng ký sự kiện này rồi. Không cần đăng ký lại đâu!'})

        # 4. Ghi danh vào bảng Registrations (Trạng thái mặc định là Pending)
        cursor.execute("""
            INSERT INTO Registrations (GuestID, EventID, RegistrationDate, AttendanceStatus) 
            VALUES (%s, %s, CURDATE(), 'Pending')
        """, (guest_id, event_id))
        
        conn.commit() # CHỐT LƯU VÀO DATABASE!
        return jsonify({'status': 'success', 'message': '🚀 Đăng ký thành công! Vé đã được ghi nhận vào hệ thống.'})
        
    except Exception as e:
        conn.rollback() # Nếu có lỗi thì hủy bỏ thao tác
        print(f"❌ Lỗi khi đăng ký: {e}")
        return jsonify({'status': 'error', 'message': 'Hệ thống đang quá tải, vui lòng thử lại sau!'})
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)