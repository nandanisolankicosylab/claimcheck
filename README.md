# ClaimCheck

**A web-based computational tool for verifying nutrition claims on packaged food labels**

ClaimCheck checks whether a nutrition claim printed on a packaged food label (for example "High Protein", "Low Fat", "Sugar Free", "No Added Sugar") is supported by the nutrition values on the same pack, using the FSSAI nutrition-claim conditions (Schedule I and Regulation 6). Each claim gets one of three results:

- **PASS**: the values support the claim
- **FAIL**: the values do not support the claim
- **NEEDS REVIEW**: the claim cannot be decided (missing value, undefined wording, missing ingredient list, and so on)

**Live app:** https://claimcheck-eenzvberjnmzxwch6pz4v8.streamlit.app/

## Folder contents

| Folder / file | What it is |
|---|---|
| `app/app.py` | Streamlit web app |
| `app/checker.py` | Rule engine used by both the app and the dataset check |
| `app/claimcheck_rules_final.xlsx` | All rules (thresholds, claim wordings, keyword lists, settings). Edit a number here and the results change |
| `app/requirements.txt` | Python packages needed |
| `data/claimcheck_results_final.xlsx` | Final dataset with results. Sheets: `results` (150 claim rows), `summary`, `removed_rows` (4 duplicates removed) |
| `validation/claimcheck_validation_final.xlsx` | Manual validation of 20 products against label photos |
| `analysis/claimcheck_analysis.xlsx` | Results by claim type (main claims with percentages; small claims as counts only) |
| `analysis/claimcheck_chart.png` | Chart of PASS / FAIL / NEEDS REVIEW by claim type |

## How to run

**Online:** open the live app link above.

**Locally** (needs internet access for the first install):

```
cd app
pip install -r requirements.txt
streamlit run app.py
```

**Re-check the whole dataset** (from the `app` folder):

```
python checker.py
```

This re-runs the rules on `data/claimcheck_results_final.xlsx` and saves a `_rechecked` copy next to it. Keep `app.py`, `checker.py` and `claimcheck_rules_final.xlsx` in the same folder.

## Results (150 claim rows from 114 products)

| Claim | n | PASS | FAIL | NEEDS REVIEW |
|---|---|---|---|---|
| High protein | 36 | 32 | 4 | 0 |
| Sugar free | 22 | 17 | 5 | 0 |
| Low fat | 16 | 8 | 8 | 0 |
| No added sugar | 42 | 22 | 18 | 2 |
| Fibre claims (high + source) | 14 | 14 | 0 | 0 |

Counts only (too few for percentages): Fat free 4 PASS; Source of protein 2 PASS, 1 NEEDS REVIEW; Trans fat free 1 PASS, 2 NEEDS REVIEW; Low sodium 1 PASS. Nine claims with undefined wording ("less oil", "lite fat" and similar) are always NEEDS REVIEW.

**Validation:** 20 products checked by hand against label photos; the checker agreed in 20 of 20 cases, and all 20 dataset values matched the label.

## Rules and assumptions

- Source: FSSAI Compendium Version IV (14.12.2022), Schedule I (claim levels) and Regulation 6(1).
- Values are taken **as sold**, per 100 g (solids) or per 100 ml (liquids).
- Protein claims use the ICMR-NIN 2024 reference value of 54 g/day (see the `settings` sheet of the rules file).
- A claim is only counted if it is actually printed on the pack.
- **No added sugar:** FAIL if an added-sugar ingredient is listed (sugar, honey, jaggery, syrups and so on). If sugars are present, the pack must also carry the statement "CONTAINS NATURALLY OCCURRING SUGARS" (Regulation 6(1)(b)); without it the claim FAILs.
- **Project assumption (not in the regulation):** the statement is treated as required only when total sugars are above the Low sugar level (5 g per 100 g solids, 2.5 g per 100 ml liquids). At or below that level the natural sugars are treated as trivial. This can be switched off with `NAS_TRIVIAL_RULE = None` in `checker.py`. With it off, 30 of the 42 "No added sugar" claims FAIL instead of 18.
- A product with a sub-ingredient named "No Added Sugar ..." is not treated as containing added sugar, and chocolate sweetened only with a sweetener is not treated as sugar.
- "Trans fat free" goes to NEEDS REVIEW if hydrogenated fat is listed.

## Dataset columns (sheet `results`)

`claim_id` (unique row id) | `pick_id` (product id) | `brand`, `product_name` | `claim_on_pack` (standardised claim) | `typed_phrase` (wording as printed) | `physical_state_guess` (Solid / Liquid, checked against label photos) | `energy_kcal_100g`, `protein_g_100g`, `total_fat_g_100g`, `trans_fat_g_100g`, `total_sugars_g_100g`, `fibre_g_100g`, `sodium_mg_100g` (per 100 g / 100 ml) | `ingredient_list` | `naturally_occurring_sugars_statement` (Yes / No, read from the pack) | `front_image_url`, `off_page` (Open Food Facts links) | `result`, `explanation`, `rule_id` (checker output).

## Limitations

- The sample is not random. Percentages describe this sample only, not all products in India.
- Nutrition values come from Open Food Facts, a crowd-sourced database. Only 20 products were checked against label photos.
- "No added sugar" cannot be fully proven from a nutrition table (Regulation 6(1) condition (iv) is not verifiable from a label).
- Fibre (14 rows) and Low fat (16 rows) have fewer than 20 rows, so their percentages are less stable.
- Two products (C082, C101) have no ingredient list, so their "No added sugar" claims stay NEEDS REVIEW.
- Solid / liquid for a few products was assigned by judgement; one error (C146) was found in validation and corrected.
- The tool is educational and is not an official FSSAI decision or legal advice.
