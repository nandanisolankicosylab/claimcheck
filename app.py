"""
ClaimCheck - Streamlit app
Checks a nutrition claim printed on a packaged food label against FSSAI Schedule I
using the same rule engine (checker.py) that was used for the project dataset.

Run:  streamlit run app.py
Keep app.py, checker.py and claimcheck_rules_final.xlsx in the same folder.
"""
import streamlit as st
import checker

st.set_page_config(page_title="ClaimCheck", page_icon="🔎", layout="centered")

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

st.title("ClaimCheck")
st.caption("Check a nutrition claim on a packaged food label against FSSAI Schedule I.")

claim_label = st.selectbox("Claim printed on the pack", list(CLAIMS))
wording, kind = CLAIMS[claim_label]

state = st.radio("Is the product sold as a solid or a liquid?", ["Solid", "Liquid"], horizontal=True,
                 help="Solids are measured per 100 g, liquids per 100 ml. Use the values 'as sold'.")
basis = "100 g" if state == "Solid" else "100 ml"
st.markdown(f"Enter values from the nutrition table, **per {basis}**.")

protein = fat = sugar = fibre = trans = sodium = energy = None
ingredients = statement = ptype = None

if kind == "fat":
    fat = st.number_input(f"Total fat (g per {basis})", min_value=0.0, step=0.1, format="%.2f")
elif kind == "sugar":
    sugar = st.number_input(f"Total sugars (g per {basis})", min_value=0.0, step=0.1, format="%.2f")
elif kind == "protein":
    protein = st.number_input(f"Protein (g per {basis})", min_value=0.0, step=0.1, format="%.2f")
    energy = st.number_input(f"Energy (kcal per {basis}), optional", min_value=0.0, step=1.0) or None
elif kind == "fibre":
    fibre = st.number_input(f"Dietary fibre (g per {basis})", min_value=0.0, step=0.1, format="%.2f")
    energy = st.number_input(f"Energy (kcal per {basis}), optional", min_value=0.0, step=1.0) or None
elif kind == "trans":
    trans = st.number_input(f"Trans fat (g per {basis})", min_value=0.0, step=0.01, format="%.2f")
    if st.checkbox("This product is an edible oil, fat or ghee"):
        ptype = "Edible oils and ghee"
    ingredients = st.text_area("Ingredient list (used to look for hydrogenated fat)")
elif kind == "sodium":
    sodium = st.number_input(f"Sodium (mg per {basis})", min_value=0.0, step=1.0)
elif kind == "nas":
    sugar = st.number_input(f"Total sugars (g per {basis})", min_value=0.0, step=0.1, format="%.2f")
    ingredients = st.text_area("Ingredient list (copy it from the pack)")
    statement = st.radio("Does the pack say CONTAINS NATURALLY OCCURRING SUGARS?",
                         ["Yes", "No", "Not checked"], horizontal=True)
    if statement == "Not checked":
        statement = None

if st.button("Check claim", type="primary"):
    result, explanation, rule_id = checker.check_claim(
        wording, state, protein_g=protein, fat_g=fat, sugar_g=sugar, fibre_g=fibre,
        trans_fat_g=trans, sodium_mg=sodium, energy_kcal=energy,
        ingredients=ingredients, product_type=ptype, naturally_occurring_statement=statement)
    if result == "PASS":
        st.success(f"PASS: the '{claim_label}' claim is supported by the values entered.")
    elif result == "FAIL":
        st.error(f"FAIL: the '{claim_label}' claim is not supported by the values entered.")
    else:
        st.warning("NEEDS REVIEW: the claim cannot be decided from the values entered.")
    st.write(explanation)
    if rule_id:
        st.caption(f"Rule used: {rule_id}")

st.divider()
st.caption(
    "Disclaimer: an educational tool, not legal advice or an official FSSAI decision. Results depend on the "
    "values you enter. 'No added sugar' cannot be fully proven from a nutrition table, and for that claim the "
    "naturally-occurring-sugars statement is only required when sugars are above the Low sugar level "
    "(a project assumption). Rules: FSSAI Compendium Version IV (14.12.2022).")
