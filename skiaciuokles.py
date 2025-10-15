#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import holidays

# ==========================
# Pagalbinės funkcijos
# ==========================

def lt_holidays_for_years(years):
    """Grąžina Lietuvos švenčių sąrašą nurodytiems metams."""
    return holidays.Lithuania(years=years)

def is_workday(d, lt_hols):
    """Darbo diena = pirmadienis–penktadienis ir ne šventė."""
    return d.weekday() < 5 and d not in lt_hols

def workdays_between_inclusive(start_d, end_d, lt_hols):
    """Darbo dienų skaičius intervale [start_d, end_d]."""
    total = 0
    d = start_d
    while d <= end_d:
        if is_workday(d, lt_hols):
            total += 1
        d += timedelta(days=1)
    return total

def list_holidays_in_range(start_d, end_d, lt_hols):
    """Grąžina sąrašą (data, pavadinimas) švenčių intervale [start_d, end_d]."""
    out = []
    d = start_d
    while d <= end_d:
        if d in lt_hols:
            out.append((d, lt_hols.get(d)))
        d += timedelta(days=1)
    return out

def nearest_workday_forward(d, lt_hols):
    """Jei diena nėra darbo diena, pastumia iki artimiausios kitos darbo dienos."""
    while not is_workday(d, lt_hols):
        d += timedelta(days=1)
    return d

def add_workdays(start_d, n_workdays):
    """Grąžina pabaigos datą pagal darbo dienų trukmę."""
    if n_workdays < 1:
        raise ValueError("Trukmė darbo dienomis turi būti >= 1")

    lt_hols = lt_holidays_for_years(range(start_d.year, start_d.year + 5))
    d = nearest_workday_forward(start_d, lt_hols)
    remaining = n_workdays - 1

    while remaining > 0:
        d += timedelta(days=1)
        if d.year not in lt_hols.years:
            lt_hols = holidays.Lithuania(years=set(lt_hols.years) | {d.year})
        if is_workday(d, lt_hols):
            remaining -= 1
    return d

# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="Skaičiuoklės 🇱🇹", page_icon="🧮", layout="centered")
st.title("🧮 Skaičiuoklės (Lietuvos kalendorius)")

tabs = st.tabs([
    "1️⃣ Darbo ir kalendorinės dienos tarp datų",
    "2️⃣ Savaitės kalendorinės dienos",
    "3️⃣ Laikotarpio pabaiga (dienos / savaitės / mėnesiai / metai)",
    "4️⃣ Laikotarpio pabaiga (darbo dienomis)"
])

# --------------------------
# 1️⃣ Darbo ir kalendorinės dienos
# --------------------------
with tabs[0]:
    st.subheader("Darbo ir kalendorinės dienos tarp dviejų datų")

    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Pradžios data", value=date.today())
    with c2:
        end_date = st.date_input("Pabaigos data", value=date.today())

    if st.button("Skaičiuoti", key="btn_days"):
        if end_date < start_date:
            st.error("❌ Pabaigos data negali būti ankstesnė nei pradžios.")
        else:
            years = range(start_date.year, end_date.year + 1)
            lt_hols = lt_holidays_for_years(years)
            calendar_days = (end_date - start_date).days + 1
            work_days = workdays_between_inclusive(start_date, end_date, lt_hols)
            hols = list_holidays_in_range(start_date, end_date, lt_hols)

            st.success(f"📅 Kalendorinių dienų: **{calendar_days}**")
            st.success(f"💼 Darbo dienų: **{work_days}**")
            st.info(f"🎉 Šventinių dienų: **{len(hols)}**")

            if hols:
                st.markdown("#### Šventinės dienos:")
                for d, name in hols:
                    st.write(f"- {d.isoformat()} — {name}")

# --------------------------
# 2️⃣ Savaitės dienos
# --------------------------
with tabs[1]:
    st.subheader("Savaitės kalendorinės dienos (pirmadienis–sekmadienis)")

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Metai", min_value=1900, max_value=2100, value=date.today().year)
    with col2:
        week = st.number_input("Savaitės numeris (1–53)", min_value=1, max_value=53, value=1)

    if st.button("Rodyti savaitės dienas", key="btn_week"):
        try:
            monday = date.fromisocalendar(int(year), int(week), 1)
            days = [monday + timedelta(days=i) for i in range(7)]
            st.success(f"{year} metų {week}-os savaitės dienos:")
            for d in days:
                st.write(f"- {d.isoformat()} ({d.strftime('%A')})")
        except ValueError:
            st.error("❌ Neteisingi metai arba savaitės numeris.")

# --------------------------
# 3️⃣ Laikotarpio pabaiga – kalendoriniais vienetais
# --------------------------
with tabs[2]:
    st.subheader("Laikotarpio pabaiga pagal trukmę (kalendoriniais vienetais)")

    c1, c2, c3 = st.columns(3)
    with c1:
        start_dt = st.date_input("Pradžios data", value=date.today(), key="rel_start")
    with c2:
        unit = st.selectbox("Vienetas", ["dienos", "savaitės", "mėnesiai", "metai"])
    with c3:
        amount = st.number_input("Trukmė", min_value=0, value=0, step=1)

    if st.button("Skaičiuoti pabaigos datą", key="btn_period"):
        if unit == "dienos":
            end_dt = start_dt + timedelta(days=amount)
        elif unit == "savaitės":
            end_dt = start_dt + timedelta(weeks=amount)
        elif unit == "mėnesiai":
            end_dt = start_dt + relativedelta(months=amount)
        else:
            end_dt = start_dt + relativedelta(years=amount)

        st.success(f"🏁 Pabaigos data: **{end_dt.isoformat()}**")

# --------------------------
# 4️⃣ Laikotarpio pabaiga – darbo dienomis
# --------------------------
with tabs[3]:
    st.subheader("Laikotarpio pabaiga pagal trukmę (darbo dienomis)")

    c1, c2 = st.columns(2)
    with c1:
        start_bd = st.date_input("Pradžios data", value=date.today(), key="bd_start")
    with c2:
        n_bd = st.number_input("Trukmė (darbo dienomis)", min_value=1, value=1, step=1)

    if st.button("Skaičiuoti pabaigos datą (darbo dienomis)", key="btn_bd"):
        try:
            end_bd = add_workdays(start_bd, int(n_bd))
            st.success(f"🏁 Pabaigos data (darbo dienomis): **{end_bd.isoformat()}**")
            st.caption("Pastaba: jei pradžios data nėra darbo diena, skaičiuojama nuo artimiausios darbo dienos.")
        except Exception as e:
            st.error(f"Klaida: {e}")


# In[ ]:




