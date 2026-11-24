"""
ClaimCheck - Streamlit app
Checks a nutrition claim printed on a packaged food label against FSSAI Schedule I
using the same rule engine (checker.py) that was used for the project dataset.

Run:  streamlit run app.py
Run from the app folder. The examples use the adjacent data and evidence directories.
"""
import hashlib
from pathlib import Path

import pandas as pd
from PIL import Image
from label_scan import read_label, parse_label

import streamlit as st
import checker
import theme

st.set_page_config(page_title="ClaimCheck", layout="wide", initial_sidebar_state="collapsed")
theme.apply()
page = st.sidebar.radio("Navigation", ["Claim Checker", "About the Project"])

if page == "About the Project":

    st.markdown("""
    <div class="hero">
        <h1>About ClaimCheck</h1>
        <p>A rule-based tool for evaluating nutrition claims on packaged foods.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Objective")

    st.write("""
    ClaimCheck evaluates nutrition claims printed on packaged food labels
    against the criteria defined in FSSAI Schedule I.
    """)

    st.markdown("### How it works")

    st.write("""
    1. Select the nutrition claim printed on the product.
    2. Select whether the food is solid or liquid.
    3. Enter the nutrient values from the nutrition information panel.
    4. The rule engine evaluates the selected claim.
    5. The application returns PASS, FAIL or NEEDS REVIEW.
    """)

    st.markdown("### Assessment categories")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.success("PASS")
        st.caption("Claim meets the selected criteria.")

    with c2:
        st.error("FAIL")
        st.caption("Claim does not meet the selected criteria.")

    with c3:
        st.warning("NEEDS REVIEW")
        st.caption("Available information is insufficient for a decision.")

    st.markdown("### Regulatory reference")
    st.write("FSSAI Compendium Version IV — 14 December 2022")

    st.stop()




# claim shown to the user -> wording understood by the rulebook, nutrient needed
CLAIMS = {
    "Low fat": ("low fat", "fat"),
    "Fat free": ("fat free", "fat"),
    "Low sugar": ("low sugar", "sugar"),
    "Sugar free": ("sugar free", "sugar"),
    "No added sugar": ("no added sugar", "nas"),
    "Source of protein": ("source of protein", "protein"),
    "High protein": ("high protein", "protein"),
    "Source of fibre": ("source of fibre", "fibre"),
    "High fibre": ("high fibre", "fibre"),
    "Trans fat free": ("trans fat free", "trans"),
    "Low sodium": ("low sodium", "sodium"),
    "Very low sodium": ("very low sodium", "sodium"),
    "Sodium free": ("sodium free", "sodium"),
}

NUTRIENTS = {
    "fat_g": ("Total fat", "g", "total_fat_g_100g"),
    "sugar_g": ("Total sugars", "g", "total_sugars_g_100g"),
    "protein_g": ("Protein", "g", "protein_g_100g"),
    "fibre_g": ("Dietary fibre", "g", "fibre_g_100g"),
    "trans_fat_g": ("Trans fat", "g", "trans_fat_g_100g"),
    "sodium_mg": ("Sodium", "mg", "sodium_mg_100g"),
    "energy_kcal": ("Energy (optional)", "kcal", "energy_kcal_100g"),
}


@st.cache_data
def example_records(path):
    df = pd.read_excel(path, sheet_name="results").sort_values(["brand", "product_name"])
    rows = df.astype(object).where(df.notna(), None).to_dict("records")
    return {r["claim_id"]: dict(r, display=f"{r['brand']} - {r['product_name']} ({r['typed_phrase']})")
            for r in rows}


def render_checker():
    mode = st.radio("Start with", ["Enter values", "Try a real product", "Scan a label"], horizontal=True)
    source = "manual"
    defaults = {}
    initial_claims = ["Low fat"]
    initial_state = "Solid"
    initial_basis = "Per 100"
    serving_default = None
    ingredients_default = ""
    statement_default = "Not checked"
    photos = Path(__file__).resolve().parent / "evidence" / "label_photos" / "photos"

    if mode == "Try a real product":
        dataset = Path(__file__).resolve().parent / "data" / "claimcheck_results_final.xlsx"
        if not dataset.is_file():
            st.error("The project examples workbook is missing from this installation.")
            return
        records = example_records(str(dataset))
        chosen = st.selectbox("Product and recorded claim", records, index=None,
                              format_func=lambda key: records[key]["display"])
        if not chosen:
            return
        row = records[chosen]
        source = chosen
        initial_claims = [row["claim_on_pack"] if row["claim_on_pack"] in CLAIMS else row["typed_phrase"]]
        initial_state = row["physical_state_guess"]
        defaults = {key: row[column] for key, (_, _, column) in NUTRIENTS.items()}
        ingredients_default = row["ingredient_list"] or ""
        statement_default = row["naturally_occurring_sugars_statement"] or "Not checked"
        st.caption(f"Recorded wording on the pack: {row['typed_phrase']}")
        pictures = sorted(photos.glob(f"{chosen}_*.jpg"))
        if pictures:
            with st.expander("Inspect label photos"):
                for photo in pictures:
                    st.image(str(photo), caption=photo.stem.split("_")[-1].capitalize())
        elif row["off_page"]:
            st.link_button("View product on Open Food Facts", row["off_page"])

    elif mode == "Scan a label":
        upload = st.file_uploader("Upload a clear photo of one nutrition column", type=["png", "jpg", "jpeg", "webp"])
        if not upload:
            return
        data = upload.getvalue()
        source = hashlib.sha256(data).hexdigest()
        if st.session_state.get("scan_id") != source:
            if not st.button("Read photo", type="primary"):
                return
            try:
                with st.spinner("Reading the nutrition panel..."):
                    text = read_label(data)
            except (ValueError, OSError, Image.DecompressionBombError) as exc:
                st.error(str(exc))
                return
            st.session_state.update(scan_id=source, scan_text=text)
        text = st.session_state.scan_text
        scan = parse_label(text)
        defaults = scan["values"]
        initial_state = {"g": "Solid", "ml": "Liquid"}.get(scan["unit"])
        initial_basis = scan["basis"]
        serving_default = scan["serving"]
        with st.expander("Compare with the uploaded label"):
            st.image(data)
            st.text(text.strip() or "No readable text found.")
        st.caption("Review the suggested values, units and measurement basis against the photo. Fill in any missed entries.")

    claims = st.multiselect("Claims printed on the pack", list(dict.fromkeys([*CLAIMS, *initial_claims])),
                            default=initial_claims, key=f"{source}_claims")
    if not claims:
        st.info("Choose at least one claim to check.")
        return
    states = ["Solid", "Liquid"]
    state = st.radio("Is the product sold as a solid or a liquid?", states, horizontal=True,
                     index=states.index(initial_state) if initial_state in states else None, key=f"{source}_state")
    bases = ["Per 100", "Per serving"]
    basis = st.radio("Values on the label", bases, horizontal=True,
                     format_func=lambda value: "Per 100 g / 100 ml" if value == "Per 100" else value,
                     index=bases.index(initial_basis) if initial_basis in bases else None, key=f"{source}_basis")
    if not state or not basis:
        st.info("Select the product type and the basis printed on the label.")
        return
    unit = "g" if state == "Solid" else "ml"
    per_serving = basis == "Per serving"
    context = f"{source}_{state}_{basis}"
    if (initial_basis and basis != initial_basis) or (initial_state and state != initial_state):
        defaults = {}
    size = None
    if per_serving:
        size = st.number_input(f"Serving size ({unit})", min_value=0.0,
                               value=serving_default if state == initial_state else None,
                               key=f"{context}_size", placeholder="Size of one serving")
        if not size:
            st.info("Enter a serving size greater than zero to convert the label values.")
    kinds = {CLAIMS.get(claim, (claim, None))[1] for claim in claims}
    needed = {"fat_g": "fat" in kinds, "sugar_g": bool({"nas", "sugar"} & kinds),
              "protein_g": "protein" in kinds, "fibre_g": "fibre" in kinds, "trans_fat_g": "trans" in kinds,
              "sodium_mg": "sodium" in kinds, "energy_kcal": bool({"protein", "fibre"} & kinds)}
    values = {}
    preview = []
    for key, (label, nutrient_unit, _) in NUTRIENTS.items():
        if not needed[key]:
            continue
        field_key = f"{context}_{key}"
        suffix = "serving" if per_serving else f"100 {unit}"
        col, flag = st.columns([2, 1])
        missing = flag.checkbox("Not listed", key=f"{field_key}_missing", help=f"{label} is not listed on the pack.")
        value = col.number_input(f"{label} ({nutrient_unit} per {suffix})", min_value=0.0,
                                 value=defaults.get(key), disabled=missing, key=field_key,
                                 placeholder="Enter label value", step=0.01, format="%.3f")
        if missing:
            value = None
        if per_serving and size and value is not None:
            value = value * 100 / size
            preview.append(f"{label}: {value:.5g} {nutrient_unit}")
        values[key] = value
    if preview:
        st.markdown(f"**Converted per 100 {unit}**  \n" + " / ".join(preview))

    if {"nas", "trans"} & kinds:
        values["ingredients"] = st.text_area("Ingredient list (copy it from the pack)", value=ingredients_default,
                                              key=f"{source}_ingredients")
    if "trans" in kinds and st.checkbox("This product is an edible oil, fat or ghee", key=f"{source}_oil"):
        values["product_type"] = "Edible oils and ghee"
    if "nas" in kinds:
        options = ["Not checked", "Yes", "No"]
        statement = st.radio("Does the pack say CONTAINS NATURALLY OCCURRING SUGARS?", options,
                             index=options.index(statement_default) if statement_default in options else 0,
                             horizontal=True, key=f"{source}_statement")
        values["naturally_occurring_statement"] = None if statement == "Not checked" else statement

    button_label = "Check claim" if len(claims) == 1 else "Check claims"
    if mode == "Scan a label":
        button_label = "Confirm values and check claims"
    if st.button(button_label, type="primary", disabled=per_serving and not size):
        for claim in claims:
            wording = CLAIMS.get(claim, (claim, None))[0]
            verdict, explanation, rule_id = checker.check_claim(wording, state, **values)
            message = {"PASS": st.success, "FAIL": st.error, "NEEDS REVIEW": st.warning}[verdict]
            message(f"{verdict}: {claim}")
            st.write(explanation)
            if rule_id:
                st.caption(f"Rule used: {rule_id}")


st.markdown(
    '<header class="intro"><span class="eyebrow">FSSAI &nbsp;/&nbsp; Schedule I</span>'
    '<h1>ClaimCheck<span aria-hidden="true">.</span></h1>'
    '<p>Check a nutrition claim on a packaged food label against FSSAI Schedule I.</p></header>',
    unsafe_allow_html=True,
)
with st.container(key="product-visual"):
    st.image(str(Path(__file__).with_name("grocery-aisle.webp")), width="stretch")

render_checker()

st.divider()
st.caption(
    "Disclaimer: an educational tool, not legal advice or an official FSSAI decision. Results depend on the "
    "values you enter. 'No added sugar' cannot be fully proven from a nutrition table, and for that claim the "
    "naturally-occurring-sugars statement is only required when sugars are above the Low sugar level "
    "(a project assumption). Rules: FSSAI Compendium Version IV (14.12.2022).")

