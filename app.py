def dashboard(df, title, is_industrial=False):

    st.title(f"🛠️ {title}")

    status_col = safe_col(df, "status")
    cust_col = safe_col(df, "customer")
    fab_col = safe_col(df, "fabrication")

    # ==============================
    # 📊 METRICS
    # ==============================
    if status_col:
        total = len(df)
        active = len(df[df[status_col].str.contains("Active", case=False, na=False)])
        shifted = len(df[df[status_col].str.contains("Shifted", case=False, na=False)])
        sold = len(df[df[status_col].str.contains("Sold", case=False, na=False)])

        st.markdown(f"""
        | 📦 Total | 🟢 Active | 🔵 Shifted | 🟠 Sold |
        |---|---|---|---|
        | **{total}** | **{active}** | **{shifted}** | **{sold}** |
        """)

    # Category Count
    cat_col = safe_col(df, "category")
    if cat_col:
        st.subheader("📊 Category Distribution")
        cat_df = df[cat_col].value_counts().reset_index()
        cat_df.columns = ["Category", "Count"]
        st.dataframe(cat_df)

    # ==============================
    # 🔍 MACHINE TRACKER
    # ==============================
    tab1, tab2, tab3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tab1:

        col1, col2 = st.columns(2)

        if cust_col:
    customers = ["All"] + sorted(df[cust_col].astype(str).unique())
else:
    st.error("Customer column missing")
    st.stop()
        sel_c = col1.selectbox("Customer", customers, key=title+"cust")

        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

        fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
        sel_f = col2.selectbox("Fabrication No", fabs, key=title+"fab")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

            c1, c2, c3, c4 = st.columns(4)

            # ==============================
            # 🧾 COLUMN 1 - CUSTOMER INFO
            # ==============================
            with c1:
                st.markdown("### **📋 Customer Info**")

                st.write(f"**Customer Name:** {row.get(cust_col)}")
                st.write(f"**Model:** {row.get(safe_col(df,'model'))}")
                st.write(f"**Location:** {row.get(safe_col(df,'location'))}")

                st.write(f"**Warranty Type:** {row.get(safe_col(df,'warranty'))}")
                st.write(f"**Warranty Start:** {fmt(row.get(safe_col(df,'start')))}")
                st.write(f"**Warranty End:** {fmt(row.get(safe_col(df,'end')))}")

                st.write(f"**Avg Run Hrs:** {row.get(safe_col(df,'avg'))}")
                st.write(f"**Running Hrs:** {row.get(safe_col(df,'hmr'))}")

            # ==============================
            # 🔧 COLUMN 2 - REPLACEMENT
            # ==============================
            with c2:
                st.markdown("### **🔧 Replacement Dates**")

                if is_industrial:
                    rep_cols = [
                        "MDA Oil R Date","MDA AF R Date","MDA OF R Date",
                        "MDA AOS R Date","MDA RGT R Date","MDA Valvekit R Date",
                        "MDA PF R DATE","MDA FF R DATE","MDA CF R DATE"
                    ]
                else:
                    rep_cols = [
                        "Oil R-Date","AFC R-Date","AFE R-Date","MOF R-Date",
                        "ROF R-Date","AOS R-Date","Greasing R-Date",
                        "1500 Kit R-Date","3000 Kit R-Date"
                    ]

                for col in rep_cols:
                    st.write(f"**{col}:** {fmt(row.get(col))}")

            # ==============================
            # ⚙️ COLUMN 3 - REMAINING HOURS
            # ==============================
            with c3:
                st.markdown("### **⚙️ Remaining Hours**")

                if is_industrial:
                    rem_cols = [
                        "AF Rem. HMR Till date","OF Rem. HMR Till date",
                        "OIL Rem. HMR Till date","AOS Rem. HMR Till date",
                        "VK Rem. HMR Till date","RGT Rem. HMR Till date"
                    ]

                    for col in rem_cols:
                        st.write(f"**{col}:** {row.get(col)}")

                else:
                    # LIVE FORMULA
                    last_hmr = row.get(safe_col(df,"last"))
                    avg = row.get(safe_col(df,"avg"))
                    curr = row.get(safe_col(df,"hmr"))

                    try:
                        live = int(curr - (last_hmr or 0))
                    except:
                        live = 0

                    st.write(f"**Live Remaining:** {live} Hrs")

            # ==============================
            # 🚨 COLUMN 4 - DUE DATE
            # ==============================
            with c4:
                st.markdown("### **🚨 Due Dates**")

                if is_industrial:
                    due_cols = [
                        "AF DUE DATE","OF DUE DATE","OIL DUE DATE",
                        "AOS DUE DATE","VALVEKIT DUE DATE","RGT DUE DATE",
                        "PF DUE DATE","FF DUE DATE","CF DUE DATE"
                    ]
                else:
                    due_cols = [c for c in df.columns if "due" in c.lower()]

                for col in due_cols:
                    st.write(f"**{col}:** {fmt(row.get(col))}")

            # ==============================
            # 🎁 FOC
            # ==============================
            foc_col = safe_col(foc_df, "fabrication")
            if foc_col:
                foc_data = foc_df[foc_df[foc_col].astype(str) == sel_f]
                st.subheader("🎁 FOC Details")
                st.dataframe(foc_data)

            # ==============================
            # 🕒 SERVICE
            # ==============================
            serv_col = safe_col(service_df, "fabrication")
            if serv_col:
                serv_data = service_df[service_df[serv_col].astype(str) == sel_f]
                st.subheader("🕒 Service History")
                st.dataframe(serv_data)

    # ==============================
    # 📦 FOC LIST
    # ==============================
    with tab2:
        st.download_button("Export FOC", to_excel(foc_df), "FOC.xlsx")
        st.dataframe(foc_df)

    # ==============================
    # ⏳ SERVICE PENDING
    # ==============================
    with tab3:
        over_col = safe_col(df, "over")
        if over_col:
            pending = df[df[over_col] != 0]
            st.write(f"Pending Count: {len(pending)}")
            st.dataframe(pending)
