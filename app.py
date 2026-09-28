import streamlit as st
import pandas as pd
from datetime import datetime, date

st.set_page_config(
    page_title="Hotel Management System",
    page_icon="🏨",
    layout="wide"
)

# =========================
# Session State
# =========================
if "rooms" not in st.session_state:
    st.session_state.rooms = pd.DataFrame([
        ["101","Standard",500000,"Available"],
        ["102","Standard",500000,"Available"],
        ["201","Deluxe",800000,"Available"],
        ["202","Deluxe",800000,"Available"],
        ["301","Suite",1500000,"Available"],
    ], columns=["Room","Type","Price","Status"])

if "bookings" not in st.session_state:
    st.session_state.bookings = pd.DataFrame(columns=[
        "Guest","Phone","Room","CheckIn","CheckOut","Nights","Total","Status"
    ])

# =========================
# Functions
# =========================
def money(x):
    return f"{int(x):,} VNĐ".replace(",", ".")

rooms = st.session_state.rooms
bookings = st.session_state.bookings

# =========================
# Sidebar
# =========================
st.sidebar.title("🏨 Hotel Manager")
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard","Rooms","Check In","Check Out","Guests","History"]
)

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    total_rooms = len(rooms)
    available = len(rooms[rooms.Status=="Available"])
    occupied = len(rooms[rooms.Status=="Occupied"])
    revenue = bookings[bookings.Status=="Checked Out"]["Total"].sum()

    st.title("🏨 Hotel Management Dashboard")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Total Rooms", total_rooms)
    c2.metric("Available", available)
    c3.metric("Occupied", occupied)
    c4.metric("Revenue", money(revenue))

    st.divider()

    left,right = st.columns([2,1])

    with left:
        st.subheader("Room Status")
        st.dataframe(rooms, use_container_width=True)

    with right:
        st.subheader("Room Type")
        chart = rooms.groupby("Type").size()
        st.bar_chart(chart)

# =========================
# ROOM MANAGEMENT
# =========================
elif menu == "Rooms":

    st.title("🛏 Room Management")

    st.subheader("Current Rooms")
    st.dataframe(rooms, use_container_width=True)

    st.divider()

    st.subheader("Add New Room")

    with st.form("room_form"):
        c1,c2 = st.columns(2)

        room = c1.text_input("Room Number")
        room_type = c2.selectbox(
            "Room Type",
            ["Standard","Deluxe","Suite","Family"]
        )

        price = st.number_input(
            "Price per Night",
            min_value=100000,
            step=50000
        )

        submit = st.form_submit_button("Add Room")

        if submit:

            if room == "":
                st.warning("Enter room number")

            elif room in rooms.Room.values:
                st.error("Room already exists")

            else:
                new = pd.DataFrame([[room,room_type,price,"Available"]],
                                   columns=rooms.columns)

                st.session_state.rooms = pd.concat([rooms,new], ignore_index=True)
                st.success("Room added successfully")
                st.rerun()

# =========================
# CHECK IN
# =========================
elif menu == "Check In":

    st.title("📝 Guest Check In")

    available_rooms = rooms[rooms.Status=="Available"]

    if len(available_rooms)==0:
        st.warning("No available rooms")

    else:

        with st.form("checkin"):

            guest = st.text_input("Guest Name")
            phone = st.text_input("Phone")

            room = st.selectbox(
                "Select Room",
                available_rooms.Room.tolist()
            )

            checkin = st.date_input(
                "Check-in Date",
                value=date.today()
            )

            checkout = st.date_input(
                "Check-out Date",
                value=date.today()
            )

            submit = st.form_submit_button("Check In")

            if submit:

                if guest == "":
                    st.error("Enter guest name")

                else:

                    nights = (checkout-checkin).days

                    if nights <= 0:
                        nights = 1

                    room_info = rooms[rooms.Room==room].iloc[0]
                    total = nights * room_info.Price

                    new = pd.DataFrame([[
                        guest,
                        phone,
                        room,
                        str(checkin),
                        str(checkout),
                        nights,
                        total,
                        "Staying"
                    ]], columns=bookings.columns)

                    st.session_state.bookings = pd.concat(
                        [bookings,new],
                        ignore_index=True
                    )

                    idx = rooms[rooms.Room==room].index[0]
                    st.session_state.rooms.loc[idx,"Status"]="Occupied"

                    st.success(f"Check-in successful! Total: {money(total)}")
                    st.rerun()

# =========================
# CHECK OUT
# =========================
elif menu == "Check Out":

    st.title("💳 Guest Check Out")

    staying = bookings[bookings.Status=="Staying"]

    if len(staying)==0:
        st.info("No guests staying")

    else:

        room = st.selectbox(
            "Select Room",
            staying.Room.tolist()
        )

        booking = staying[staying.Room==room].iloc[0]

        st.write("### Guest Information")
        st.write("**Name:**", booking.Guest)
        st.write("**Phone:**", booking.Phone)
        st.write("**Nights:**", booking.Nights)
        st.write("**Amount:**", money(booking.Total))

        if st.button("Confirm Check Out"):

            idx = bookings[bookings.Room==room].index[0]
            st.session_state.bookings.loc[idx,"Status"]="Checked Out"

            r = rooms[rooms.Room==room].index[0]
            st.session_state.rooms.loc[r,"Status"]="Available"

            st.success("Check-out completed!")
            st.rerun()

# =========================
# GUESTS
# =========================
elif menu == "Guests":

    st.title("👨‍👩‍👧 Guests Currently Staying")

    staying = bookings[bookings.Status=="Staying"]

    if len(staying)==0:
        st.info("No current guests")

    else:
        st.dataframe(staying, use_container_width=True)

# =========================
# HISTORY
# =========================
elif menu == "History":

    st.title("📜 Booking History")

    st.dataframe(bookings, use_container_width=True)

    done = bookings[bookings.Status=="Checked Out"]

    if len(done)>0:

        st.divider()

        st.subheader("Revenue Report")

        report = done.groupby("Room")["Total"].sum()
        st.bar_chart(report)

        st.write("### Total Revenue")
        st.success(money(done.Total.sum()))
