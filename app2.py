import streamlit as st 
import pandas as pd
import re
import plotly.express as px

# ตั้งชื่อไฟล์ชั่วคราว
UPLOAD_PATH_OPTICAL = "uploaded_optical.xlsx"
UPLOAD_PATH_FM = "uploaded_fm.xlsx"


pd.set_option("styler.render.max_elements", 1_200_000)

# สร้าง session state
if 'optical_uploaded' not in st.session_state:
    st.session_state.optical_uploaded = False
if 'fm_uploaded' not in st.session_state:
    st.session_state.fm_uploaded = False



# Sidebar
menu = st.sidebar.radio("เลือกกิจกรรม", ["หน้าแรก","CPU","FAN","MSU","Line board","Client board","Fiber Flapping","Loss between Core","Loss between EOL"])

if menu == "หน้าแรก":
    st.subheader("DWDM Monitoring Dashboard")
    

if menu == "CPU":
    st.markdown("### Upload CPU File")

    # Upload CPU File
    uploaded_cpu = st.file_uploader("Upload CPU File", type=["xlsx"], key="cpu")
    if uploaded_cpu:
        df_cpu = pd.read_excel(uploaded_cpu)
        st.session_state.cpu_data = df_cpu
        st.success("CPU file uploaded and stored")

    # ใช้จาก session ถ้ามีข้อมูล
    if st.session_state.get("cpu_data") is not None:
        try:
            # เตรียม DataFrame
            df_cpu = st.session_state.cpu_data.copy()
            df_cpu.columns = df_cpu.columns.str.strip().str.replace(r'\s+', ' ', regex=True).str.replace('\u00a0', ' ')

            # ตรวจสอบคอลัมน์ที่จำเป็น
            required_cols = {"ME", "Measure Object", "CPU utilization ratio"}
            if not required_cols.issubset(df_cpu.columns):
                st.error(f"CPU file must contain columns: {', '.join(required_cols)}")
                st.stop()

            # สร้าง Mapping Format
            df_cpu["Mapping Format"] = df_cpu["ME"].astype(str).str.strip() + df_cpu["Measure Object"].astype(str).str.strip()

            # โหลด Reference File
            df_ref = pd.read_excel("data/CPU.xlsx")
            df_ref.columns = df_ref.columns.astype(str)\
                            .str.encode('ascii', 'ignore').str.decode('utf-8')\
                                .str.replace(r'\s+', ' ', regex=True)\
                                .str.strip()

            # ตรวจสอบคอลัมน์ใน reference
            required_ref_cols = {"Mapping", "Maximum threshold", "Minimum threshold"}
            if not required_ref_cols.issubset(df_ref.columns):
                st.error(f"Reference file must contain columns: {', '.join(required_ref_cols)}")
                st.stop()

            df_ref["Mapping"] = df_ref["Mapping"].astype(str).str.strip()

            # Merge ข้อมูล
            df_merged = pd.merge(
                df_cpu,
                df_ref[["Site Name", "Mapping", "Maximum threshold", "Minimum threshold"]],
                left_on="Mapping Format",
                right_on="Mapping",
                how="inner"
            )

            # ตรวจสอบผลลัพธ์
            if not df_merged.empty:
                df_result = df_merged[[
                    "Site Name", "ME", "Measure Object", "Maximum threshold", "Minimum threshold","CPU utilization ratio"
                ]]

                # ฟังก์ชันตรวจไม่ผ่าน
                def is_not_ok(row):
                    return row["CPU utilization ratio"] > row["Maximum threshold"] or row["CPU utilization ratio"] < row["Minimum threshold"]

                highlight_mask = df_result.apply(is_not_ok, axis=1)

                # ฟังก์ชันไฮไลต์สีแดงเฉพาะ column
                def highlight_red_single_column(x):
                    return ['background-color: #ff4d4d; color: white' if highlight_mask.iloc[i] else '' for i in range(len(x))]

                # สร้าง styled table
                styled_df = df_result.style.apply(
                    highlight_red_single_column,
                    subset=["CPU utilization ratio"]
                ).format({
                    "CPU utilization ratio": "{:.2f}",
                    "Maximum threshold": "{:.2f}",
                    "Minimum threshold": "{:.2f}"
                })

                st.markdown("### CPU Performance")
                st.dataframe(styled_df, use_container_width=True)

                # แสดงผลสรุป
                if highlight_mask.any():
                    st.markdown("""
<div style='text-align: center; color: red; font-size: 24px; font-weight: bold;'>
CPU NOT OK
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown("""
<div style='text-align: center; color: green; font-size: 24px; font-weight: bold;'>
CPU OK
</div>
""", unsafe_allow_html=True)

            else:
                st.warning("ไม่พบ Mapping ที่ตรงกันระหว่าง CPU file และ reference")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดระหว่างการประมวลผล: {e}")
    else:
        st.info("กรุณาอัปโหลด CPU file ก่อนเพื่อเริ่มการวิเคราะห์")







elif menu == "FAN":
    st.markdown("### 📂 Upload FAN File ")        
    uploaded_fan = st.file_uploader(" Upload FAN File", type=["xlsx"], key="fan")

    # ถ้าอัปโหลดใหม่ ให้โหลดและบันทึกใน session
    if uploaded_fan:
        df_fan = pd.read_excel(uploaded_fan)
        st.session_state.fan_data = df_fan  # เก็บลง session
        st.success("FAN file uploaded and stored")


    # ใช้ข้อมูลจาก session หากมี
    if st.session_state.get("fan_data") is not None:


        df_fan = st.session_state.fan_data.copy()

        try:
            # อ่านไฟล์ที่อัป
            df_fan = pd.read_excel("uploaded_fan.xlsx")
            df_fan.columns = df_fan.columns.str.strip().str.replace(r'\s+', ' ', regex=True).str.replace('\u00a0', ' ')

            # ตรวจสอบคอลัมน์ที่ต้องมี
            required_cols = {"ME", "Measure Object", "Begin Time", "End Time", "Value of Fan Rotate Speed(Rps)"}
            if not required_cols.issubset(df_fan.columns):
                st.error(f" ไฟล์ที่อัปโหลดต้องมีคอลัมน์: {', '.join(required_cols)}")
                st.write("คอลัมน์ที่พบ:", df_fan.columns.tolist())
                st.stop()

            #  Mapping Format 
            df_fan["Mapping Format"] = df_fan["ME"].astype(str).str.strip() + df_fan["Measure Object"].astype(str).str.strip()

            # โหลด reference FAN จากระบบ
            df_ref = pd.read_excel("data/FAN.xlsx")
            df_ref.columns = df_ref.columns.str.strip().str.replace(r'\s+', ' ', regex=True).str.replace('\u00a0', ' ')

            # เตรียมคอลัมน์สำคัญจาก df_ref
            df_ref_subset = df_ref[["Mapping", "Site Name", "Maximum threshold", "Minimun threshold"]].copy()
            df_ref_subset["Mapping"] = df_ref_subset["Mapping"].astype(str).str.strip()

            # รวมข้อมูลทั้งสอง DataFrame โดย match ด้วย Mapping Format
            df_merged = pd.merge(
                df_fan,
                df_ref_subset,
                left_on="Mapping Format",
                right_on="Mapping",
                how="inner"
            )

            # แสดงผลลัพธ์
            if not df_merged.empty:
                df_result = df_merged[[
                    "Begin Time", "End Time", "Site Name", "ME", "Measure Object",
                    "Maximum threshold", "Minimun threshold", "Value of Fan Rotate Speed(Rps)"
                ]]

                # 🔍 ตรวจสอบ FAN Performance โดยไม่ใส่ "Not OK" แต่เน้นสีแดง
                # สร้างคอลัมน์ flag ว่าแถวนี้เข้าเงื่อนไข Not OK หรือไม่
                #  สร้าง mask แยกสำหรับแถวที่ต้องไฮไลต์ โดยไม่ใส่ลงใน DataFrame
                def is_not_ok(row):
                    mo = str(row["Measure Object"])
                    val = row["Value of Fan Rotate Speed(Rps)"]
                    if "FCC" in mo and val > 120:
                        return True
                    elif "FCPP" in mo and val > 250:
                        return True
                    elif "FCPL" in mo and val > 120:
                        return True
                    elif "FCPS" in mo and val > 230:
                        return True
                    else:
                        return False

                # สร้าง boolean mask
                highlight_mask = df_result.apply(is_not_ok, axis=1)

                #  ฟังก์ชันไฮไลต์เฉพาะคอลัมน์เดียว
                def highlight_red_single_column(x):
                    return ['background-color: #ff4d4d; color: white' if highlight_mask.iloc[i] else '' for i in range(len(x))]

               
                styled_df = df_result.style.apply(
                    highlight_red_single_column,
                    subset=["Value of Fan Rotate Speed(Rps)"]
                )

                # ทศนิยม 2 ตำแหน่ง 
                styled_df = styled_df.format({
                    "Value of Fan Rotate Speed(Rps)": "{:.2f}"
                })


                st.markdown("### FAN Performance")
                st.dataframe(styled_df, use_container_width=True)

                if highlight_mask.any():
                    st.markdown("""
<div style='text-align: center; color: red; font-size: 24px; font-weight: bold;'>
FAN NOT OK
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown("""
<div style='text-align: center; color: green; font-size: 24px; font-weight: bold;'>
FAN OK
</div>
""", unsafe_allow_html=True)


            else:
                st.info("ไม่พบรายการที่ Mapping Format ตรงกับ FAN reference")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดระหว่างการประมวลผล: {e}")
    else:
        st.info("Please upload FAN ratio file")





elif menu == "MSU":
    st.markdown("### 📂 Upload MSU File")

    uploaded_msu = st.file_uploader("Upload MSU File", type=["xlsx"], key="msu")
    if uploaded_msu:
        df_msu = pd.read_excel(uploaded_msu)
        st.session_state.msu_data = df_msu
        st.success(" MSU file uploaded and stored")

    if st.session_state.get("msu_data") is not None:
        try:
            df_msu = st.session_state.msu_data.copy()
            df_msu.columns = df_msu.columns.str.strip().str.replace(r'\s+', ' ', regex=True).str.replace('\u00a0', ' ')

            # ตรวจสอบคอลัมน์ที่ต้องมี
            required_cols = {"ME", "Measure Object", "Laser Bias Current(mA)"}
            if not required_cols.issubset(df_msu.columns):
                st.error(f"❗ MSU file must contain columns: {', '.join(required_cols)}")
                st.stop()

            # สร้าง Mapping Format
            df_msu["Mapping Format"] = df_msu["ME"].astype(str).str.strip() + df_msu["Measure Object"].astype(str).str.strip()

            # โหลด Reference File
            df_ref = pd.read_excel("data/MSU.xlsx")
            df_ref.columns = df_ref.columns.str.strip().str.replace(r'\s+', ' ', regex=True).str.replace('\u00a0', ' ')

            # ตรวจสอบคอลัมน์ใน reference
            required_ref_cols = {"Mapping", "Maximum threshold"}
            if not required_ref_cols.issubset(df_ref.columns):
                st.error(f"❗ Reference file must contain columns: {', '.join(required_ref_cols)}")
                st.stop()

            df_ref["Mapping"] = df_ref["Mapping"].astype(str).str.strip()

            # Merge ข้อมูล
            df_merged = pd.merge(
                df_msu,
                df_ref[["Mapping", "Maximum threshold"]],
                left_on="Mapping Format",
                right_on="Mapping",
                how="inner"
            )

            if not df_merged.empty:
                df_result = df_merged[[
                    "ME", "Measure Object", "Maximum threshold", "Laser Bias Current(mA)"
                ]]

                # เช็คว่าเกิน threshold มั้ย
                def is_not_ok(row):
                    return row["Laser Bias Current(mA)"] > row["Maximum threshold"]

                highlight_mask = df_result.apply(is_not_ok, axis=1)

                # ฟังก์ชันเน้นสีแดง
                def highlight_red_single_column(x):
                    return ['background-color: #ff4d4d; color: white' if highlight_mask.iloc[i] else '' for i in range(len(x))]

                # แสดงผล
                styled_df = df_result.style.apply(
                    highlight_red_single_column,
                    subset=["Laser Bias Current(mA)"]
                ).format({
                    "Laser Bias Current(mA)": "{:.2f}",
                    "Maximum threshold": "{:.2f}"
                })

                st.markdown("### MSU Performance")
                st.dataframe(styled_df, use_container_width=True)

                # แสดงสถานะ
                if highlight_mask.any():
                    st.markdown("""
<div style='text-align: center; color: red; font-size: 24px; font-weight: bold;'>
🔴 MSU NOT OK
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown("""
<div style='text-align: center; color: green; font-size: 24px; font-weight: bold;'>
🟢 MSU OK
</div>
""", unsafe_allow_html=True)
            else:
                st.warning("ไม่พบ Mapping ที่ตรงกันระหว่าง MSU file และ reference")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดระหว่างการประมวลผล: {e}")
    else:
        st.info("กรุณาอัปโหลด MSU file ก่อนเพื่อเริ่มการวิเคราะห์")

   









elif menu == "Fiber Flapping":
    st.markdown("### Upload OSC & FM Files")

    # Upload OSC
    uploaded_optical = st.file_uploader("Upload OSC Optical File", type=["xlsx"], key="osc")
    if uploaded_optical:
        df_optical = pd.read_excel(uploaded_optical)
        st.session_state.osc_optical_data = df_optical
        st.success("OSC Optical File Uploaded")

    # Upload FM
    uploaded_fm = st.file_uploader("Upload FM Alarm File", type=["xlsx"], key="fm")
    if uploaded_fm:
        df_fm = pd.read_excel(uploaded_fm)
        st.session_state.osc_fm_data = df_fm
        st.success("FM Alarm File Uploaded")

    # ประมวลผลเมื่อทั้งสองไฟล์ถูกอัปโหลดแล้ว
    if "osc_optical_data" in st.session_state and "osc_fm_data" in st.session_state:
        try:
            df_optical = st.session_state.osc_optical_data.copy()
            df_fm = st.session_state.osc_fm_data.copy()

            df_optical.columns = df_optical.columns.str.strip()
            df_optical["Max - Min (dB)"] = df_optical["Max Value of Input Optical Power(dBm)"] - df_optical["Min Value of Input Optical Power(dBm)"]

            # Extract Target ME
            def extract_target(measure_obj):
                match = re.search(r'\(([^)]+)\)', str(measure_obj))
                return match.group(1) if match else None

            df_optical["Target ME"] = df_optical["Measure Object"].apply(extract_target)
            df_optical["Begin Time"] = pd.to_datetime(df_optical["Begin Time"], errors="coerce")
            df_optical["End Time"] = pd.to_datetime(df_optical["End Time"], errors="coerce")

            # Filter > 2dB
            df_filtered = df_optical[df_optical["Max - Min (dB)"] > 2].copy()

            df_fm.columns = df_fm.columns.str.strip()
            df_fm["Occurrence Time"] = pd.to_datetime(df_fm["Occurrence Time"], errors="coerce")
            df_fm["Clear Time"] = pd.to_datetime(df_fm["Clear Time"], errors="coerce")

            link_col = [col for col in df_fm.columns if col.startswith("Link")][0]

            # หา no-match
            result = []
            for _, row in df_filtered.iterrows():
                me = re.escape(str(row["ME"]))
                target_me = re.escape(str(row["Target ME"]))
                matched = df_fm[
                    df_fm[link_col].astype(str).str.contains(me, na=False) &
                    df_fm[link_col].astype(str).str.contains(target_me, na=False) &
                    (df_fm["Occurrence Time"] <= row["End Time"]) &
                    (df_fm["Clear Time"] >= row["Begin Time"])
                ]
                if matched.empty:
                    result.append(row)

            df_nomatch = pd.DataFrame(result)

            # Show result
            st.markdown("### OSC Power Flapping (No Alarm Match)")
            if not df_nomatch.empty:
                st.dataframe(
                    df_nomatch[[
                        "Begin Time", "End Time", "Granularity", "ME", "ME IP", "Measure Object",
                        "Max Value of Input Optical Power(dBm)", "Min Value of Input Optical Power(dBm)",
                        "Input Optical Power(dBm)", "Max - Min (dB)"
                    ]],
                    use_container_width=True
                )

                # Daily graph
                df_nomatch["Date"] = df_nomatch["Begin Time"].dt.date
                site_count = df_nomatch.groupby("Date")["ME"].nunique().reset_index()
                site_count.columns = ["Date", "Sites"]

                import plotly.express as px
                fig = px.bar(site_count, x="Date", y="Sites", text="Sites", title="No Fiber Break Alarm Match")
                fig.update_traces(marker_color="crimson", textposition="outside")
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

                # แสดงแยกรายวัน
                for date, group in df_nomatch.groupby("Date"):
                    st.markdown(f"#### {date.strftime('%Y-%m-%d')}")
                    st.dataframe(group[[
                        "Begin Time", "End Time", "Granularity", "ME", "ME IP", "Measure Object",
                        "Max Value of Input Optical Power(dBm)", "Min Value of Input Optical Power(dBm)",
                        "Input Optical Power(dBm)", "Max - Min (dB)"
                    ]], use_container_width=True)
            else:
                st.success("ไม่มีรายการ Flapping ที่ไม่แมตช์ FM")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        st.info("กรุณาอัปโหลดทั้ง OSC และ FM ไฟล์ก่อน")
  