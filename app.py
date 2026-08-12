from flask import Flask, render_template, request, jsonify
import pandas as pd
import re
from pathlib import Path

app = Flask(__name__)

CSV_PATH = Path(__file__).parent / "ncdd_admin_database.csv"

NCDD_PROVINCES = {
    "01": ("បន្ទាយមានជ័យ", "Banteay Meanchey", "ខេត្ត"),
    "02": ("បាត់ដំបង", "Battambang", "ខេត្ត"),
    "03": ("កំពង់ចាម", "Kampong Cham", "ខេត្ត"),
    "04": ("កំពង់ឆ្នាំង", "Kampong Chhnang", "ខេត្ត"),
    "05": ("កំពង់ស្ពឺ", "Kampong Speu", "ខេត្ត"),
    "06": ("កំពង់ធំ", "Kampong Thom", "ខេត្ត"),
    "07": ("កំពត", "Kampot", "ខេត្ត"),
    "08": ("កណ្តាល", "Kandal", "ខេត្ត"),
    "09": ("កោះកុង", "Koh Kong", "ខេត្ត"),
    "10": ("ក្រចេះ", "Kratie", "ខេត្ត"),
    "11": ("មណ្ឌលគិរី", "Mondulkiri", "ខេត្ត"),
    "12": ("ភ្នំពេញ", "Phnom Penh", "រាជធានី"),
    "13": ("ព្រះវិហារ", "Preah Vihear", "ខេត្ត"),
    "14": ("ព្រៃវែង", "Prey Veng", "ខេត្ត"),
    "15": ("ពោធិ៍សាត់", "Pursat", "ខេត្ត"),
    "16": ("រតនគិរី", "Ratanakiri", "ខេត្ត"),
    "17": ("សៀមរាប", "Siem Reap", "ខេត្ត"),
    "18": ("ព្រះសីហនុ", "Preah Sihanouk", "ខេត្ត"),
    "19": ("ស្ទឹងត្រែង", "Stung Treng", "ខេត្ត"),
    "20": ("ស្វាយរៀង", "Svay Rieng", "ខេត្ត"),
    "21": ("តាកែវ", "Takeo", "ខេត្ត"),
    "22": ("ឧត្តរមានជ័យ", "Oddar Meanchey", "ខេត្ត"),
    "23": ("កែប", "Kep", "ខេត្ត"),
    "24": ("ប៉ៃលិន", "Pailin", "ខេត្ត"),
    "25": ("ត្បូងឃ្មុំ", "Tboung Khmum", "ខេត្ត"),
}

def detect_district_prefix(type_val, name_kh, name_en):
    combined = f"{type_val} {name_kh} {name_en}".lower()
    if "khan" in combined or "ខណ្ឌ" in combined:
        return "ខណ្ឌ"
    if "krong" in combined or "municipality" in combined or "ក្រុង" in combined:
        return "ក្រុង"
    return "ស្រុក"

def detect_commune_prefix(type_val, name_kh, name_en, parent_d_prefix):
    combined = f"{type_val} {name_kh} {name_en}".lower()
    if "sangkat" in combined or "សង្កាត់" in combined:
        return "សង្កាត់"
    if "commune" in combined or "khum" in combined or "ឃុំ" in combined:
        return "ឃុំ"
    if parent_d_prefix in ["ក្រុង", "ខណ្ឌ"]:
        return "សង្កាត់"
    return "ឃុំ"

def process_ncdd_gazetteer(csv_path):
    df_raw = pd.read_csv(csv_path, header=None, dtype=str, encoding="utf-8-sig")

    header_row_idx = 0
    province_from_header_kh = ""
    province_from_header_en = ""
    province_from_header_prefix = "ខេត្ត"

    for idx, row in df_raw.iterrows():
        row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
        match = re.search(r'for\s*["\']?([^"\']+)["\']?', row_str, re.IGNORECASE)
        if match:
            p_name = match.group(1).strip()
            for code, (p_kh, p_en, p_pref) in NCDD_PROVINCES.items():
                if p_en.lower() in p_name.lower():
                    province_from_header_kh = p_kh
                    province_from_header_en = p_en
                    province_from_header_prefix = p_pref
                    break
        if "Code" in row_str and "Name (Khmer)" in row_str:
            header_row_idx = idx
            break

    headers = [str(h).strip() for h in df_raw.iloc[header_row_idx].values]
    df_data = df_raw.iloc[header_row_idx + 1:].copy()
    df_data.columns = headers

    type_col = next((c for c in headers if "type" in c.lower()), headers[0])
    code_col = next((c for c in headers if "code" in c.lower()), headers[1])
    kh_col = next((c for c in headers if "khmer" in c.lower()), headers[2])
    en_col = next((c for c in headers if "latin" in c.lower() or "english" in c.lower()), headers[3])

    cur_p_kh, cur_p_en, cur_p_prefix = province_from_header_kh, province_from_header_en, province_from_header_prefix
    cur_d_kh, cur_d_en, cur_d_prefix = "", "", "ស្រុក"
    cur_c_kh, cur_c_en, cur_c_prefix = "", "", "ឃុំ"
    villages = []

    for _, row in df_data.iterrows():
        code = str(row.get(code_col, "")).strip()
        type_val = str(row.get(type_col, "")).strip().lower()
        name_kh = str(row.get(kh_col, "")).strip()
        name_en = str(row.get(en_col, "")).strip()

        if not code or code.lower() == "nan" or not name_kh or name_kh.lower() == "nan":
            continue

        clean_code = re.sub(r"\D", "", code)
        if clean_code:
            if len(clean_code) <= 2:
                clean_code = clean_code.zfill(2)
            elif len(clean_code) <= 4:
                clean_code = clean_code.zfill(4)
            elif len(clean_code) <= 6:
                clean_code = clean_code.zfill(6)
            else:
                clean_code = clean_code.zfill(8)

        code_len = len(clean_code)
        p_code_2 = clean_code[:2] if len(clean_code) >= 2 else ""

        if p_code_2 in NCDD_PROVINCES:
            map_kh, map_en, map_pref = NCDD_PROVINCES[p_code_2]
            cur_p_kh, cur_p_en, cur_p_prefix = map_kh, map_en, map_pref

        if code_len == 2 or any(k in type_val for k in ["province", "capital", "រាជធានី", "ខេត្ត"]):
            cur_p_kh, cur_p_en = name_kh, name_en
            cur_p_prefix = "រាជធានី" if (
                "phnom penh" in cur_p_en.lower() or "ភ្នំពេញ" in cur_p_kh or "capital" in type_val
            ) else "ខេត្ត"
            cur_d_kh, cur_d_en, cur_d_prefix = "", "", "ស្រុក"
            cur_c_kh, cur_c_en, cur_c_prefix = "", "", "ឃុំ"

        elif code_len == 4 or any(k in type_val for k in ["district", "khan", "krong", "municipality", "ស្រុក", "ខណ្ឌ", "ក្រុង"]):
            cur_d_kh, cur_d_en = name_kh, name_en
            cur_d_prefix = detect_district_prefix(type_val, name_kh, name_en)
            cur_c_kh, cur_c_en, cur_c_prefix = "", "", "ឃុំ"

        elif code_len == 6 or any(k in type_val for k in ["commune", "sangkat", "ឃុំ", "សង្កាត់"]):
            cur_c_kh, cur_c_en = name_kh, name_en
            cur_c_prefix = detect_commune_prefix(type_val, name_kh, name_en, cur_d_prefix)

        elif code_len == 8 or any(k in type_val for k in ["village", "phum", "ភូមិ"]):
            villages.append({
                "v_kh": name_kh, "v_en": name_en,
                "c_kh": cur_c_kh, "c_en": cur_c_en, "c_prefix": cur_c_prefix,
                "d_kh": cur_d_kh, "d_en": cur_d_en, "d_prefix": cur_d_prefix,
                "p_kh": cur_p_kh, "p_en": cur_p_en, "p_prefix": cur_p_prefix,
                "code": clean_code,
            })

    return pd.DataFrame(villages)

def format_khmer_address(row):
    v_clean = str(row["v_kh"]).replace("ភូមិ", "").strip()
    c_clean = str(row["c_kh"]).replace("ឃុំ", "").replace("សង្កាត់", "").strip()
    d_clean = str(row["d_kh"]).replace("ស្រុក", "").replace("ខណ្ឌ", "").replace("ក្រុង", "").strip()
    p_clean = str(row["p_kh"]).replace("ខេត្ត", "").replace("រាជធានី", "").strip()

    if "phnom penh" in str(row["p_en"]).lower() or "ភ្នំពេញ" in p_clean:
        p_clean = "ភ្នំពេញ"
        p_prefix = "រាជធានី"
    else:
        p_prefix = row["p_prefix"]

    return f"ភូមិ {v_clean} {row['c_prefix']} {c_clean} {row['d_prefix']} {d_clean} {p_prefix} {p_clean}"

print("Loading NCDD gazetteer...")
DF = process_ncdd_gazetteer(CSV_PATH)
RECORDS = DF.to_dict("records")

@app.route("/")
def index():
    provinces = sorted(
        {(r["p_en"], r["p_kh"]) for r in RECORDS},
        key=lambda x: x[0].lower()
    )
    return render_template("index.html", total=len(RECORDS), provinces=provinces)

@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip().lower()
    province = request.args.get("province", "").strip().lower()
    limit = min(max(int(request.args.get("limit", 100)), 1), 500)

    if not q and not province:
        return jsonify({"count": 0, "results": []})

    results = []
    for r in RECORDS:
        hay = " ".join([
            str(r.get("v_kh","")), str(r.get("v_en","")),
            str(r.get("c_kh","")), str(r.get("c_en","")),
            str(r.get("d_kh","")), str(r.get("d_en","")),
            str(r.get("p_kh","")), str(r.get("p_en","")),
            str(r.get("code",""))
        ]).lower()

        if q and q not in hay:
            continue
        if province and province not in str(r.get("p_en","")).lower():
            continue

        item = {
            "v_kh": r["v_kh"], "v_en": r["v_en"],
            "c_kh": r["c_kh"], "c_en": r["c_en"], "c_prefix": r["c_prefix"],
            "d_kh": r["d_kh"], "d_en": r["d_en"], "d_prefix": r["d_prefix"],
            "p_kh": r["p_kh"], "p_en": r["p_en"], "p_prefix": r["p_prefix"],
            "code": r["code"],
            "address_kh": format_khmer_address(r)
        }
        results.append(item)
        if len(results) >= limit:
            break

    return jsonify({"count": len(results), "results": results})

@app.route("/api/stats")
def stats():
    provinces = sorted({r["p_en"] for r in RECORDS})
    return jsonify({
        "villages": len(RECORDS),
        "provinces": len(provinces),
        "districts": len({(r["p_en"], r["d_en"]) for r in RECORDS}),
        "communes": len({(r["p_en"], r["d_en"], r["c_en"]) for r in RECORDS}),
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
