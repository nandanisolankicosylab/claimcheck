"""
checker.py - ClaimCheck rule engine.
Reads every rule from claimcheck_rules_final.xlsx (nothing is hard-coded),
so if you correct a number in the Excel file, the results change.

Main function:
    check_claim(claim_text, physical_state, protein_g=None, fat_g=None, sugar_g=None,
                fibre_g=None, trans_fat_g=None, sodium_mg=None, energy_kcal=None,
                ingredients=None, product_type=None, naturally_occurring_statement=None)
returns (result, explanation, rule_id) where result is PASS, FAIL or NEEDS REVIEW.
All nutrient values are per 100 g (solids) or per 100 ml (liquids), as sold.
"""
import re
from pathlib import Path
import pandas as pd

RULES_PATH = Path(__file__).with_name("claimcheck_rules_final.xlsx")


def _load(path=RULES_PATH):
    x = pd.ExcelFile(path)
    sheet = lambda n: x.parse(n)
    R = {"rulebook": sheet("rulebook").set_index("rule_id")}
    wd = sheet("claim_wordings")
    wd["wording"] = wd["wording"].str.strip().str.lower()
    R["wordings"] = wd.set_index("wording")
    sv = sheet("spelling_variants")
    R["variants"] = sorted(zip(sv.variant.str.lower(), sv.standard_form.str.lower()),
                           key=lambda t: -len(t[0]))      # longest first
    R["kept"] = [k.lower() for k in sheet("nas_keywords")["keyword"]]
    R["unclear"] = [k.lower() for k in sheet("nas_unclear_terms")["unclear_term"]]
    R["settings"] = dict(zip(sheet("settings").key, sheet("settings").value))
    sl = sheet("solid_liquid")
    R["classes"] = dict(zip(sl.product_type.str.lower(), sl["class"]))
    return R


RULES = _load()
NUTRIENT_ARG = {"Fat": "fat_g", "Sugars": "sugar_g", "Protein": "protein_g",
                "Fibre": "fibre_g", "Trans fat": "trans_fat_g", "Sodium": "sodium_g"}
NUTRIENT_NAME = {"Fat": "Total fat", "Sugars": "Total sugars", "Protein": "Protein",
                 "Fibre": "Dietary fibre", "Trans fat": "Trans fat", "Sodium": "Sodium"}
OPS = {"<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
       ">=": lambda a, b: a >= b, ">": lambda a, b: a > b}
HYDROGENATED = ["hydrogenated", "vanaspati"]


def normalise(text):
    t = re.sub(r"\s+", " ", str(text).strip().lower())
    t = t.replace("fibres", "fibre")                       # simple plural
    for variant, standard in RULES["variants"]:
        t = t.replace(variant, standard)
    return t


def _blank(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


def _find_terms(text, terms):
    return [t for t in terms if re.search(r"\b" + re.escape(t) + r"s?\b", text)]


def _fmt(x):
    return f"{x:g}"


# PROJECT ASSUMPTION (not in the regulation): the statement CONTAINS NATURALLY OCCURRING SUGARS is only
# required when natural sugars are more than trivial. "Trivial" = at or below the Low sugar level in the
# rulebook (R03: 5 g per 100 g solids, 2.5 g per 100 ml liquids). Set to None to switch this off.
NAS_TRIVIAL_RULE = "R03"


def _no_added_sugar(sugar_g, ingredients, statement, physical_state=None):
    if _blank(ingredients):
        return "NEEDS REVIEW", "Ingredient list not provided, so added sugars cannot be checked.", "R09"
    ing = normalise(ingredients)
    # Fix 1: a sub-ingredient called "No Added Sugar ..." is not added sugar.
    ing = re.sub(r"no added sugars?", " ", ing)
    kept = _find_terms(ing, RULES["kept"])
    if kept:
        return "FAIL", f"An ingredient on the added-sugar list was found: {kept[0]}.", "R09"
    unclear = _find_terms(ing, RULES["unclear"])
    # Fix 2: chocolate / choco chips that are sweetened with a sweetener are not treated as sugar.
    if re.search(r"sweeten|stevia|sucralose|maltitol|ins\s*9[5-6]\d", ing):
        unclear = [u for u in unclear if u not in ("chocolate", "choco chips", "chocolate chips")]
    if unclear:
        return ("NEEDS REVIEW", f"An ingredient may contain or replace sugars: {unclear[0]}. "
                "Check the wording on the pack.", "R09")
    if _blank(sugar_g):
        return "NEEDS REVIEW", "Total sugars value is missing.", "R09"
    if sugar_g == 0:
        return ("PASS", "No added-sugar ingredient found and no sugars declared. "
                "(Condition (iv) cannot be verified from a label.)", "R09")
    if NAS_TRIVIAL_RULE and not _blank(physical_state):
        col = "per_100g_solid" if str(physical_state).strip().lower() == "solid" else "per_100ml_liquid"
        limit = RULES["rulebook"].loc[NAS_TRIVIAL_RULE, col]
        if sugar_g <= limit:
            return ("PASS", f"No added-sugar ingredient found. Sugars ({sugar_g} g) are at or below the Low sugar "
                    f"level ({limit} g), so the naturally-occurring-sugars statement is not required "
                    "(project threshold assumption).", "R09")
    st = str(statement).strip().lower() if not _blank(statement) else ""
    if st in ("yes", "y"):
        return ("PASS", "No added-sugar ingredient found. Sugars are naturally occurring and the "
                "required statement is present. (Condition (iv) cannot be verified from a label.)", "R09")
    if st in ("no", "n"):
        return ("FAIL", "No added-sugar ingredient found, but sugars are naturally present and the required "
                "statement CONTAINS NATURALLY OCCURRING SUGARS is missing from the pack "
                "(Regulation 6(1)(b)).", "R09")
    return ("NEEDS REVIEW", "Sugars are present and the statement CONTAINS NATURALLY OCCURRING SUGARS "
            "was not recorded. Check the pack.", "R09")


def check_claim(claim_text, physical_state, protein_g=None, fat_g=None, sugar_g=None,
                fibre_g=None, trans_fat_g=None, sodium_mg=None, energy_kcal=None,
                ingredients=None, product_type=None, naturally_occurring_statement=None):
    # T2: wording not found / health supplement
    if product_type and "supplement" in str(product_type).lower():
        return "NEEDS REVIEW", "Health supplement category: different rules apply.", ""
    wording = normalise(claim_text) if not _blank(claim_text) else ""
    if wording not in RULES["wordings"].index:
        return "NEEDS REVIEW", f"Claim wording '{claim_text}' is not a defined claim in the rulebook.", ""
    row = RULES["wordings"].loc[wording]
    rule_id = row["rule_id"]
    if rule_id == "NEEDS_REVIEW":
        return "NEEDS REVIEW", f"'{claim_text}' is ambiguous (not tied to a Schedule I level).", ""

    if rule_id == "R09":                                       # non-addition claim
        return _no_added_sugar(sugar_g, ingredients, naturally_occurring_statement, physical_state)

    # T3: solid / liquid
    state = str(physical_state).strip().capitalize() if not _blank(physical_state) else ""
    if state not in ("Solid", "Liquid"):
        return "NEEDS REVIEW", "Solid/liquid is not stated, so the threshold cannot be chosen.", rule_id

    rule = RULES["rulebook"].loc[rule_id]
    group = rule["analysis_group"]
    vals = {"fat_g": fat_g, "sugar_g": sugar_g, "protein_g": protein_g, "fibre_g": fibre_g,
            "trans_fat_g": trans_fat_g,
            "sodium_g": None if _blank(sodium_mg) else sodium_mg / 1000}
    value = vals[NUTRIENT_ARG[group]]
    name = NUTRIENT_NAME[group]
    if _blank(value):                                          # T1
        return "NEEDS REVIEW", f"{name} value is missing, so the claim cannot be checked.", rule_id
    if group == "Protein" and _blank(RULES["settings"].get("protein_rda_g_per_day")):   # T4
        return "NEEDS REVIEW", "Protein RDA is not set.", rule_id

    # trans fat: edible oils use the alternative rule R11
    ptype = str(product_type).lower() if product_type else ""
    if rule_id == "R10" and ptype in ("edible oils and ghee", "edible oil or fat"):
        rule_id = "R11"
        rule = RULES["rulebook"].loc[rule_id]

    unit_basis = "100 g" if state == "Solid" else "100 ml"
    threshold = rule["per_100g_solid"] if state == "Solid" else rule["per_100ml_liquid"]
    op = rule["operator"]
    meets = OPS[op](float(value), float(threshold))
    label = rule["claim_label"]
    sym = {"<=": "≤", ">=": "≥", "<": "<", ">": ">"}[op]
    unit = "g" if group != "Sodium" else "g"
    shown = f"{value * 1000:g} mg" if group == "Sodium" else f"{_fmt(value)} g"
    need = f"{_fmt(threshold * 1000)} mg" if group == "Sodium" else f"{_fmt(threshold)} g"
    expl = (f"{name} is {shown} per {unit_basis}; '{label}' needs {sym} {need} per {unit_basis} "
            f"({rule['schedule_ref']}).")

    if group == "Trans fat" and meets and any(h in str(ingredients).lower() for h in HYDROGENATED):
        return ("NEEDS REVIEW", "Declared trans fat is below the limit, but hydrogenated fat is listed. "
                "Check the label.", rule_id)

    if not meets and not _blank(rule["per_100kcal"]) and not _blank(energy_kcal) and energy_kcal > 0:
        per_kcal = value / energy_kcal * 100
        if OPS[op](per_kcal, float(rule["per_100kcal"])):
            expl += (f" Note: it would meet the per-100 kcal option ({per_kcal:.1f} g per 100 kcal); "
                     "this tool uses the per-100 g/ml basis.")
    return ("PASS" if meets else "FAIL"), expl, rule_id


def run_row(r):
    """Run the checker on one dataframe row (columns of the clean dataset)."""
    g = lambda k: None if k not in r or pd.isna(r[k]) else r[k]
    return check_claim(g("typed_phrase"), g("physical_state_guess"), g("protein_g_100g"),
                       g("total_fat_g_100g"), g("total_sugars_g_100g"), g("fibre_g_100g"),
                       g("trans_fat_g_100g"), g("sodium_mg_100g"), g("energy_kcal_100g"),
                       g("ingredient_list"), g("product_type"), g("naturally_occurring_sugars_statement"))


if __name__ == "__main__":
    df = pd.read_excel(Path(__file__).with_name("claimcheck_dataset_final.xlsx"), sheet_name="dataset")
    out = df.apply(run_row, axis=1, result_type="expand")
    df["result"], df["explanation"], df["rule_id"] = out[0], out[1], out[2]
    df.to_excel(Path(__file__).with_name("claimcheck_results.xlsx"), index=False)
    print(df.groupby("claim_on_pack")["result"].value_counts().unstack(fill_value=0))
