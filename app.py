
import streamlit as st
import checker

st.set_page_config(
    page_title="ClaimCheck | Nutrition Compliance",
    page_icon="🥗",
    layout="wide"
)

# ---------------- CUSTOM DESIGN ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

.stApp {
    background: #F6F8F5;
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1150px;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    color: #173F35 !important;
}

[data-testid="stSidebar"] {
    background: #173F35;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

.hero {
    background: linear-gradient(120deg, #173F35, #2C6A50);
    padding: 32px;
    border-radius: 22px;
    margin-bottom: 25px;
}

.hero h1 {
    color: white !important;
    font-size: 38px !important;
    margin-bottom: 5px;
}

.hero p {
    color: #D8E9DF !important;
    font-size: 16px;
}

.section-card {
    background: white;
    border: 1px solid #E3EAE4;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 18px;
}

.result-pass {
    background: #E7F5EC;
    border: 1px solid #A7D8B8;
    border-radius: 18px;
    padding: 25px;
}

.result-fail {
    background: #FCECEC;
    border: 1px solid #E9B5B5;
    border-radius: 18px;
    padding: 25px;
}

.result-review {
    background: #FFF5DF;
    border: 1px solid #E8D09A;
    border-radius: 18px;
    padding: 25px;
}

div.stButton > button[kind="primary"] {
    background: #26734D;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 1.5rem;
    font-weight: 700;
}

div.stButton > button[kind="primary"]:hover {
    background: #194F36;
    color: white;
}

.footer {
    text-align: center;
    color: #75847B;
    font-size: 13px;
    padding-top: 20px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- CLAIM DEFINITIONS ----------------
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


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## 🥗 ClaimCheck")
    st.caption("Nutrition claim compliance tool")

    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Claim Checker", "About the Project"]
    )

    st.markdown("---")

    st.markdown("### Project")
    st.write("FSSAI Schedule I")
    st.write("Rule-based compliance assessment")

    st.markdown("---")
    st.caption("Mini Project | Nutrition & Food Compliance")


# ---------------- ABOUT PAGE ----------------
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


# ---------------- MAIN PAGE ----------------
st.markdown("""
<div class="hero">
    <h1>🥗 ClaimCheck</h1>
    <p>Evaluate nutrition claims on packaged foods against FSSAI Schedule I.</p>
</div>
""", unsafe_allow_html=True)


# ---------------- INPUT SECTION ----------------
st.markdown("## Evaluate a Nutrition Claim")
st.caption("Enter the information exactly as shown on the food package.")

claim_label = st.selectbox(
    "Nutrition claim printed on the package",
    list(CLAIMS.keys())
)

wording, kind = CLAIMS[claim_label]

state = st.radio(
    "Food category",
    ["Solid", "Liquid"],
    horizontal=True,
    help="Solid products use per 100 g criteria and liquid products use per 100 ml criteria."
)

basis = "100 g" if state == "Solid" else "100 ml"

st.info(f"Enter nutrient information on an **as sold, per {basis}** basis.")


# Initialize values
protein = fat = sugar = fibre = trans = sodium = energy = None
ingredients = statement = ptype = None


# ---------------- DYNAMIC NUTRIENT INPUT ----------------
with st.container(border=True):

    st.markdown("### Nutrition Information")

    if kind == "fat":
        fat = st.number_input(
            f"Total fat (g per {basis})",
            min_value=0.0,
            step=0.1,
            format="%.2f"
        )

    elif kind == "sugar":
        sugar = st.number_input(
            f"Total sugars (g per {basis})",
            min_value=0.0,
            step=0.1,
            format="%.2f"
        )

    elif kind == "protein":
        protein = st.number_input(
            f"Protein (g per {basis})",
            min_value=0.0,
            step=0.1,
            format="%.2f"
        )

        energy = st.number_input(
            f"Energy (kcal per {basis}) — optional",
            min_value=0.0,
            step=1.0
        ) or None

    elif kind == "fibre":
        fibre = st.number_input(
            f"Dietary fibre (g per {basis})",
            min_value=0.0,
            step=0.1,
            format="%.2f"
        )

        energy = st.number_input(
            f"Energy (kcal per {basis}) — optional",
            min_value=0.0,
            step=1.0
        ) or None

    elif kind == "trans":
        trans = st.number_input(
            f"Trans fat (g per {basis})",
            min_value=0.0,
            step=0.01,
            format="%.2f"
        )

        if st.checkbox("Product is edible oil, fat or ghee"):
            ptype = "Edible oils and ghee"

        ingredients = st.text_area(
            "Ingredient list",
            placeholder="Enter ingredients as printed on the package..."
        )

    elif kind == "sodium":
        sodium = st.number_input(
            f"Sodium (mg per {basis})",
            min_value=0.0,
            step=1.0
        )

    elif kind == "nas":
        sugar = st.number_input(
            f"Total sugars (g per {basis})",
            min_value=0.0,
            step=0.1,
            format="%.2f"
        )

        ingredients = st.text_area(
            "Ingredient list",
            placeholder="Enter ingredients as printed on the package..."
        )

        statement = st.radio(
            "Does the package mention 'CONTAINS NATURALLY OCCURRING SUGARS'?",
            ["Yes", "No", "Not checked"],
            horizontal=True
        )

        if statement == "Not checked":
            statement = None


# ---------------- CHECK BUTTON ----------------
st.markdown("")

check_button = st.button(
    "🔍  Check Compliance",
    type="primary",
    use_container_width=True
)


# ---------------- RESULT ----------------
if check_button:

    result, explanation, rule_id = checker.check_claim(
        wording,
        state,
        protein_g=protein,
        fat_g=fat,
        sugar_g=sugar,
        fibre_g=fibre,
        trans_fat_g=trans,
        sodium_mg=sodium,
        energy_kcal=energy,
        ingredients=ingredients,
        product_type=ptype,
        naturally_occurring_statement=statement
    )

    st.markdown("---")
    st.markdown("## Assessment Result")

    if result == "PASS":

        st.markdown("""
        <div class="result-pass">
            <h2 style="color:#21633D !important;">✅ PASS</h2>
            <p style="color:#21633D;">The entered values meet the selected nutrition claim criteria.</p>
        </div>
        """, unsafe_allow_html=True)

    elif result == "FAIL":

        st.markdown("""
        <div class="result-fail">
            <h2 style="color:#A52C2C !important;">❌ FAIL</h2>
            <p style="color:#A52C2C;">The entered values do not meet the selected nutrition claim criteria.</p>
        </div>
        """, unsafe_allow_html=True)

    else:

        st.markdown("""
        <div class="result-review">
            <h2 style="color:#946300 !important;">⚠️ NEEDS REVIEW</h2>
            <p style="color:#946300;">The claim cannot be conclusively evaluated using the information provided.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Explanation")

    with st.container(border=True):
        st.write(explanation)

        if rule_id:
            st.caption(f"Applicable rule reference: {rule_id}")


# ---------------- DISCLAIMER ----------------
st.markdown("---")

with st.expander("Methodology & Disclaimer"):

    st.write("""
    ClaimCheck is an educational mini-project that evaluates selected
    nutrition claims using a rule-based approach based on FSSAI Schedule I.

    It is not an official FSSAI decision or legal advice.

    Results depend on the accuracy and completeness of the information entered.

    No Added Sugar claims cannot be fully established from the nutrition
    table alone. Ingredient information and applicable conditions must
    also be considered.

    Regulatory reference: FSSAI Compendium Version IV (14.12.2022).
    """)

st.markdown("""
<div class="footer">
    ClaimCheck | Nutrition Claim Compliance Mini Project
</div>
""", unsafe_allow_html=True)

