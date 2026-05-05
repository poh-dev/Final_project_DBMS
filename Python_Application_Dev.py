import mysql.connector
from mysql.connector import Error
import getpass  

def connect_as_guest():
    print("\n Connecting to public server...")
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',          
            password='@Poh12345',
            database="final_project_dbms"  
        )
        if connection.is_connected():
            print("✅ Connected successfully as: Guest")
            return connection, "Guest"
    except Error as e:
        print(f" Connection error: {e}")
    return None, None

def connect_as_staff():
    print("\n--- STAFF / COORDINATOR LOGIN ---")
    username = input(" Username (DB Account): ").strip()
    password = getpass.getpass(" Password: ") 
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user=username,
            password=password,
            database="final_project_dbms"
        )
        if connection.is_connected():
            print(f"✅ Login successful! Welcome, {username}.")
            return connection, username
    except Error as e:
        print(f" Access Denied: {e.msg}")
        print(" Please check your credentials and try again.")
    return None, None

def view_upcoming_events(connection):
    print("\n--- Upcoming Events ---")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT EventName, EventDate FROM View_Upcoming_Events LIMIT 10;")
        records = cursor.fetchall()
        
        if not records:
            print("There are currently no upcoming events.")
        else:
            for row in records:
                print(f" Event: {row[0]} | Date: {row[1]}")
    except Error as e:
        print(f" Error: {e}")
    finally:
        cursor.close()

def register_guest(connection):
    print("\n--- REGISTER TO PARTICIPATE IN THE EVENT ---")
    try:
    
        cursor = connection.cursor()
        
        email = input (" Please in put guests' email: ")
        cursor.execute ("SELECT GuestID, GuestName FROM Guests WHERE Email = %s", (email,))
        guest = cursor.fetchone()
        if guest:
            guest_id = guest[0]
            print(f"welcome: {guest[1]}")
        else:
            print("Hi, please inform more information")
            name = input("Please input your name: ")
            phone = input("Please input your phone number: ")
            sql_insert_guest = "INSERT INTO Guests (GuestName, Email, PhoneNumber) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert_guest, (name, email, phone))
            guest_id = cursor.lastrowid
            print(f"Successfully inserted {name} profile")
        
        print("\n List of events are available: ")
        cursor.execute ("SELECT EventID, EventName, EventDate FROM View_Upcoming_Events LIMIT 20;")
        events = cursor.fetchall()
        for ev in events:
            print(f"  [Code: {ev[0]}] - {ev[1]} (Date: {ev[2]})")

        event_id = input("\n Please input the code that you want to attend: ")
        
        sql_register = "INSERT INTO Registrations (EventID, GuestID, RegistrationDate) VALUES (%s, %s, CURDATE())"
        cursor.execute(sql_register, (event_id, guest_id))
        connection.commit()
        print(" Congratulation your registration had been made successfully!")

    except Error as e:
        print(f" Failed to assign: {e}")
    finally:
        cursor.close()

def generate_comprehensive_report(connection):
    print("        COMPREHENSIVE EVENT REPORT        ")
    cursor = None
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT EventID, EventName, EventDate FROM Events ORDER BY EventDate DESC LIMIT 15;")
        events = cursor.fetchall()
        
        if not events:
            print(" There are currently no events in the system.")
            return
            
        print("\n Available Events:")
        for ev in events:
            print(f"  [Code: {ev[0]}] - {ev[1]} (Date: {ev[2]})")
            
        event_id = input("\n  Please input the EventCode to generate report (or '0' to cancel): ").strip()
        
        if event_id == '0':
            return

        cursor.execute("""
            SELECT e.EventName, e.EventDate, v.Capacity 
            FROM Events e JOIN Venues v ON e.VenueID = v.VenueID 
            WHERE e.EventID = %s
        """, (event_id,))
        event_info = cursor.fetchone()
        
        if not event_info:
            print("  Error: Event not found or invalid EventCode!")
            return
            
        event_name, event_date, capacity = event_info

        cursor.execute("SELECT TotalRegistered, TotalAttended FROM view_guest_statistics WHERE EventName = %s", (event_name,))
        stats = cursor.fetchone()

        total_registered = int(stats[0]) if stats else 0
        total_attended = int(stats[1]) if stats else 0
        
        occupancy_rate = (total_registered / capacity * 100) if capacity > 0 else 0
        checkin_rate = (total_attended / total_registered * 100) if total_registered > 0 else 0

        cursor.execute("SELECT Event_2, VenueName FROM view_scheduling_conflicts WHERE Event_1 = %s", (event_name,))
        conflicts = cursor.fetchall()           

        print("\n" + "*"*50)
        print(f" REPORT FOR: {event_name.upper()}")
        print(f" Date: {event_date}")
        print("*"*50)
        
        print(f"\n 1️  PARTICIPATION RATE (Occupancy)")
        print(f"    - Venue Capacity: {capacity} seats")
        print(f"    - Registered Guests: {total_registered}")
        print(f"    - Occupancy Rate: {occupancy_rate:.1f}% ({total_registered}/{capacity})")
        
        print(f"\n 2️  GUEST STATISTICS (Check-in)")
        print(f"    - Expected Guests: {total_registered}")
        print(f"    - Actually Attended: {total_attended}")
        print(f"    - Check-in Rate: {checkin_rate:.1f}% ({total_attended}/{total_registered})")
        
        print(f"\n 3️  SCHEDULING CONFLICTS")
        if not conflicts:
            print("     No conflicts detected. Venue is safely booked.")
        else:
            print("      WARNING: Venue double-booked with the following event(s):")
            for c in conflicts:
                print(f"       -> [ID: {c[0]}] {c[1]}")
        
        print("*"*50 + "\n")
        
    except Error as e:
        print(f" System Error: {e}")
    finally:
        if cursor:
            cursor.close()

def check_in_guest(connection):
    print("\n--- EVENT CHECK-IN CONFIRMATION ---")
    cursor = None
    try:
        cursor = connection.cursor()
        event_id = input("Please enter the EventCode: ").strip()
        sql_get_guests = """
            SELECT r.GuestID, g.GuestName, r.AttendanceStatus 
            FROM Registrations r
            JOIN Guests g ON r.GuestID = g.GuestID
            WHERE r.EventID = %s
        """
        cursor.execute(sql_get_guests, (event_id,))
        guests = cursor.fetchall()

        if not guests:
            print("The event doesnot receive any registration or wrong EventCode:")
            return           
        print(f"\nList of guest (Event {event_id}):")

        for row in guests:
            status = "🟢 Checked-in" if row[2] == 'Attended' else "🟡 Pending"
            print(f"  [GuestID: {row[0]}] - Name: {row[1]} | Status: {status}")            
        guest_id = input("\n👉 Please input GuestID to confirm the attendance, otherwise, '0' for cancelation: ").strip()
        
        if guest_id == '0':
            print(" Cancelled successfully.")
            return
            
        sql_checkin = "UPDATE Registrations SET AttendanceStatus = 'Attended' WHERE EventID = %s AND GuestID = %s"
        cursor.execute(sql_checkin, (event_id, guest_id))
        
        if cursor.rowcount > 0:
            connection.commit()
            print(f" Check-in for {guest_id} had committed successfully!")
        else:
            print("Error: This guest does not heve information in the database!")
            
    except Error as e:
        print(f"\n System Error: {e}")
    finally:
        if cursor:
            cursor.close()


def edit_event(connection):
    print("\n--- Edit Events ---")
    cursor = None
    try:
        cursor = connection.cursor()    
        cursor.execute("SELECT EventID, EventName, EventDate FROM Events ORDER BY EventDate DESC LIMIT 10;")
        events = cursor.fetchall()
        
        if not events:
            print("There is no event in the system.")
            return
            
        print("\nList of events:")
        for ev in events:
            print(f"  [EventID: {ev[0]}] - {ev[1]} (Date: {ev[2]})")
            
        event_id = input("\n Please input Event_ID to modify or '0' to cancel the step: ").strip()
        
        if event_id == '0':
            print("Cancelled successfully.")
            return
            
        cursor.execute("SELECT EventName, EventDate FROM Events WHERE EventID = %s", (event_id,))
        current_event = cursor.fetchone()
        
        if not current_event:
            print("Error: Event_ID not found!")
            return
            
        print(f"\nEditting: {current_event[0]} (Current date: {current_event[1]})")
        print("Instruction: Input new description. If you want to stay the same, let it blank and push Enter.")
        
        new_name = input(f"New name [{current_event[0]}]: ").strip()
        new_date = input(f"New date (YYYY-MM-DD) [{current_event[1]}]: ").strip()        
        final_name = new_name if new_name != "" else current_event[0]
        final_date = new_date if new_date != "" else current_event[1]        
        sql_update = "UPDATE Events SET EventName = %s, EventDate = %s WHERE EventID = %s"
        cursor.execute(sql_update, (final_name, final_date, event_id))

        connection.commit()       
        print(" Updating Successfully!")
       
    except Error as e:
        print(f"\n System Error: {e}")
    finally:
        if cursor:
            cursor.close()

def main():
    connection = None
    current_user = None

    while True:
        print("\n" + "="*40)
        print("   WELCOME TO SEAT SYNC SYSTEM   ")
        print("="*40)
        print(" Please select your role to continue:")
        print(" 1. Guest (Public Access - Auto Connect)")
        print(" 2. Staff / Event Coordinator (Secure Login)")
        print(" 0. Exit System")
        print("="*40)
        
        role_choice = input(" Your choice (0-2): ")
        
        if role_choice == '1':
            connection, current_user = connect_as_guest()
            if connection: break
            
        elif role_choice == '2':
            connection, current_user = connect_as_staff()
            if connection: break
            
        elif role_choice == '0':
            print(" Goodbye!")
            return
        else:
            print(" Invalid choice. Please try again.")


    while True:
        print("\n" + "="*40)
        print(f" Seat Sync Dashboard | Current User: {current_user}")
        print("="*40)
        print("1. Guest: Register for Event")
        print("2. Staff: Check-in confirmation for participation")
        print("3. Coordinator: Update / Edit Event")
        print("4. View Upcoming Event")
        print("5. Report: Comprehensive Event Analysis")
        print("0. Logout & Exit")
        print("="*40)
        
        choice = input("Choose a function (0-5): ")

        if choice == '1':
            register_guest(connection)            
        elif choice == '2':
            check_in_guest(connection)
        elif choice == '3':
            cursor = connection.cursor()
            cursor.execute("SELECT CURRENT_ROLE();")
            current_role = cursor.fetchone()[0]
            if current_role and 'RegistrationStaff' in current_role:
                print("\n  Access Denied: You are logged in as Registration Staff.")
                print("Only Event Coordinators can access this function!")
            else:
                edit_event(connection)
            cursor.close()
        elif choice == '4':
            view_upcoming_events(connection)
        elif choice == '5':
            generate_comprehensive_report(connection)
        elif choice == '0':
            print("\n Logging out. See you later!")
            break
        else:
            print("\n Insufficient choice, please try again!")

    if connection and connection.is_connected():
        connection.close()

if __name__ == '__main__':
    main()