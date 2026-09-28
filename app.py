import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="Hotel Management System",
    page_icon="🏨",
    layout="wide"
)

st.image("VT.jpg", use_container_width=True)

# ==========================
# MYSQL AIVEN
# ==========================
DB_USER = "avnadmin"
DB_PASSWORD = "AVNS_OL4tfzDCvAVBsOWWRXK"
DB_HOST = "mysql-6ab5bcf-trandinhphuc1702-e8a7.e.aivencloud.com"
DB_PORT = "20874"
DB_NAME = "hotel_db"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True
)

# ==========================
# CREATE TABLE
# ==========================
with engine.begin() as conn:

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS rooms(
        room VARCHAR(10) PRIMARY KEY,
        type VARCHAR(30),
        price INT,
        status VARCHAR(20)
    )
    """))

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS bookings(
        id INT AUTO_INCREMENT PRIMARY KEY,
        guest VARCHAR(100),
        phone VARCHAR(30),
        room VARCHAR(10),
        checkin DATE,
        checkout DATE,
        nights INT,
        total INT,
        status VARCHAR(30)
    )
    """))

    count = conn.execute(text("SELECT COUNT(*) FROM rooms")).scalar()

    if count == 0:

        conn.execute(text("""
        INSERT INTO rooms VALUES
        ('101','Standard',500000,'Available'),
        ('102','Standard',500000,'Available'),
        ('201','Deluxe',800000,'Available'),
        ('202','Deluxe',800000,'Available'),
        ('301','Suite',1500000,'Available')
        """))

# ==========================
# FUNCTIONS
# ==========================
def money(x):
    return f"{int(x):,} VNĐ".replace(",", ".")

def load_rooms():
    return pd.read_sql("SELECT * FROM rooms ORDER BY room", engine)

def load_bookings():
    return pd.read_sql("SELECT * FROM bookings ORDER BY id DESC", engine)

rooms = load_rooms()
bookings = load_bookings()

# ==========================
# SIDEBAR
# ==========================
st.sidebar.title("🏨 Hotel Manager")

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Rooms",
        "Check In",
        "Check Out",
        "Guests",
        "History"
    ]
)

# ==========================
# DASHBOARD
# ==========================
if menu == "Dashboard":

    total_rooms = len(rooms)
    available = len(rooms[rooms.status=="Available"])
    occupied = len(rooms[rooms.status=="Occupied"])

    revenue = bookings[bookings.status=="Checked Out"]["total"].sum()

    st.title("🏨 Hotel Management Dashboard")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Total Rooms", total_rooms)
    c2.metric("Available", available)
    c3.metric("Occupied", occupied)
    c4.metric("Revenue", money(revenue if pd.notna(revenue) else 0))

    st.divider()

    left,right = st.columns([2,1])

    with left:

        st.subheader("Room Status")

        show = rooms.rename(columns={
            "room":"Room",
            "type":"Type",
            "price":"Price",
            "status":"Status"
        })

        st.dataframe(show, use_container_width=True)

    with right:

        st.subheader("Room Type")

        chart = rooms.groupby("type").size()

        st.bar_chart(chart)

# ==========================
# ROOMS
# ==========================
elif menu == "Rooms":

    st.title("🛏 Room Management")

    st.subheader("Current Rooms")

    st.dataframe(
        rooms.rename(columns={
            "room":"Room",
            "type":"Type",
            "price":"Price",
            "status":"Status"
        }),
        use_container_width=True
    )

    st.divider()

    st.subheader("Add New Room")

    with st.form("room"):

        c1,c2 = st.columns(2)

        room = c1.text_input("Room Number")

        room_type = c2.selectbox(
            "Room Type",
            ["Standard","Deluxe","Suite","Family"]
        )

        price = st.number_input(
            "Price",
            min_value=100000,
            step=50000
        )

        submit = st.form_submit_button("Add Room")

        if submit:

            if room == "":
                st.warning("Enter room number")

            elif room in rooms.room.values:
                st.error("Room already exists")

            else:

                with engine.begin() as conn:

                    conn.execute(
                        text("""
                        INSERT INTO rooms
                        VALUES(:r,:t,:p,'Available')
                        """),
                        {"r":room,"t":room_type,"p":price}
                    )

                st.success("Room added")
                st.rerun()

# ==========================
# CHECK IN
# ==========================
elif menu == "Check In":

    st.title("📝 Guest Check In")

    available_rooms = rooms[rooms.status=="Available"]

    if len(available_rooms)==0:

        st.warning("No available rooms")

    else:

        with st.form("checkin"):

            guest = st.text_input("Guest Name")

            phone = st.text_input("Phone")

            room = st.selectbox(
                "Select Room",
                available_rooms.room.tolist()
            )

            checkin = st.date_input(
                "Check In",
                value=date.today()
            )

            checkout = st.date_input(
                "Check Out",
                value=date.today()
            )

            submit = st.form_submit_button("Check In")

            if submit:

                if guest=="":

                    st.error("Enter guest name")

                else:

                    nights = (checkout-checkin).days

                    if nights<=0:
                        nights=1

                    price = int(
                        rooms[rooms.room==room]["price"].iloc[0]
                    )

                    total = price*nights

                    with engine.begin() as conn:

                        conn.execute(
                            text("""
                            INSERT INTO bookings
                            (guest,phone,room,checkin,checkout,nights,total,status)
                            VALUES
                            (:g,:ph,:r,:ci,:co,:n,:t,'Staying')
                            """),
                            {
                                "g":guest,
                                "ph":phone,
                                "r":room,
                                "ci":checkin,
                                "co":checkout,
                                "n":nights,
                                "t":total
                            }
                        )

                        conn.execute(
                            text("""
                            UPDATE rooms
                            SET status='Occupied'
                            WHERE room=:r
                            """),
                            {"r":room}
                        )

                    st.success(f"Check in successful ({money(total)})")
                    st.rerun()

# ==========================
# CHECK OUT
# ==========================
elif menu == "Check Out":

    st.title("💳 Guest Check Out")

    staying = bookings[bookings.status=="Staying"]

    if len(staying)==0:

        st.info("No guests staying")

    else:

        room = st.selectbox(
            "Select Room",
            staying.room.tolist()
        )

        b = staying[staying.room==room].iloc[0]

        st.write("### Guest Information")
        st.write("**Name:**", b.guest)
        st.write("**Phone:**", b.phone)
        st.write("**Nights:**", b.nights)
        st.write("**Amount:**", money(b.total))

        if st.button("Confirm Check Out"):

            with engine.begin() as conn:

                conn.execute(
                    text("""
                    UPDATE bookings
                    SET status='Checked Out'
                    WHERE id=:id
                    """),
                    {"id":int(b.id)}
                )

                conn.execute(
                    text("""
                    UPDATE rooms
                    SET status='Available'
                    WHERE room=:r
                    """),
                    {"r":room}
                )

            st.success("Check Out Completed")
            st.rerun()

# ==========================
# GUESTS
# ==========================
elif menu == "Guests":

    st.title("👨‍👩‍👧 Current Guests")

    staying = bookings[bookings.status=="Staying"]

    if len(staying)==0:

        st.info("No guests")

    else:

        show = staying.rename(columns={
            "guest":"Guest",
            "phone":"Phone",
            "room":"Room",
            "checkin":"Check In",
            "checkout":"Check Out",
            "nights":"Nights",
            "total":"Total",
            "status":"Status"
        })

        st.dataframe(show, use_container_width=True)

# ==========================
# HISTORY
# ==========================
elif menu == "History":

    st.title("📜 Booking History")

    show = bookings.rename(columns={
        "guest":"Guest",
        "phone":"Phone",
        "room":"Room",
        "checkin":"Check In",
        "checkout":"Check Out",
        "nights":"Nights",
        "total":"Total",
        "status":"Status"
    })

    st.dataframe(show, use_container_width=True)

    done = bookings[bookings.status=="Checked Out"]

    if len(done)>0:

        st.divider()

        st.subheader("Revenue by Room")

        report = done.groupby("room")["total"].sum()

        st.bar_chart(report)

        st.subheader("Total Revenue")

        st.success(money(done.total.sum()))
