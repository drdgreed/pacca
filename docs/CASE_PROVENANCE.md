# Case Provenance — Per-Case Rationale, Failure Mode, and Iteration of Origin

> **Companion to:** [`DATASET_SUFFICIENCY.md`](./DATASET_SUFFICIENCY.md) — this document provides the audit-trail "why does each case exist" answer for every case in the dataset.
> **Status:** v1.2 at iter-6 close (100-case state — production-pilot milestone hit). New rows added per case; iteration column tracks when the case landed.

## Schema

Each row answers four questions:
- **Case ID** — `GC-NNN`, links to its file location
- **Clinical rationale** — the medical reasoning the case is built around (≤2 sentences)
- **Named failure mode** — what specific failure pattern this case probes (or "coverage" if it's a routine positive/negative case rather than an adversarial probe)
- **Iteration of origin** — which harness iteration added or last meaningfully modified the case

A reviewer asking "why is this case here?" can answer from this table without reading the case definition.

## Provenance table

| Case ID | File | Clinical rationale | Named failure mode (or "coverage") | Iteration |
|---|---|---|---|---|
| GC-001 | golden_cases.py | NSCLC pembrolizumab — all NCCN Category 1 criteria documented for stage IV metastatic disease, PD-L1 62%, no EGFR/ALK; canonical clean approve | **Coverage** (canonical positive for the H2 memory-trap sibling family); also test-data integrity (iter-2 chg-6 fix stage IIIA→IV) | iter-1 (baseline); modified iter-2 chg-6 |
| GC-002 | golden_cases.py | Lumbar MRI after 8 weeks documented conservative therapy failure; meets imaging guidelines | Coverage (clean orthopedic/imaging auto-approve) | iter-1 |
| GC-003 | golden_cases.py | T2DM, HbA1c 8.4 on metformin → SGLT2 inhibitor; clean step-therapy advancement | Coverage (clean endocrine auto-approve) | iter-1 |
| GC-004 | golden_cases.py | Lumbar MRI requested after only 2 weeks of symptoms with no conservative therapy — premature | **Test-data adequacy** (probes premature-imaging anti-pattern; IN_REVIEW expected) | iter-1 |
| GC-005 | golden_cases.py | Biologic (adalimumab) for psoriasis with NO step-therapy documentation; patient preference cited as justification | **Step-therapy enforcement** (the agent must NOT accept patient preference as justification per AAD-NPF guidelines); cross-condition memory bleed test for iter-4 chg-1 RA entry | iter-1; risk case for iter-4 chg-1 |
| GC-006 | golden_cases.py | CAR-T cell therapy (procedure code Q2041) — experimental procedure code triggers pre-flight | **Experimental-treatment branch_4** (positive case) | iter-1 |
| GC-007 | golden_cases.py | Gaucher disease enzyme replacement — rare condition ICD-10 prefix triggers pre-flight | **Rare-condition branch_5** (positive case) | iter-1 |
| GC-008 | golden_cases.py | Pembrolizumab re-request after prior denial on same procedure code | **Prior-denial branch_7** (positive case) | iter-1 |
| GC-009 | golden_cases.py | Phase II clinical trial drug — experimental keyword triggers pre-flight | **Experimental-treatment branch_4** via keyword detection (alternative to procedure-code detection path of GC-006) | iter-1 |
| GC-010 | golden_cases.py | Abatacept for seropositive RA, all ACR 2021 criteria met, $288K/year annual cost exceeds $100K threshold | **High-cost escalation branch_2** (predicted fix in iter-3 chg-1; verified live 1→5); canonical risk case for iter-4 chg-1 RA memory non-override | iter-1; predicted_fix verified iter-3 chg-1; risk case for iter-4 chg-1 |
| GC-011 | golden_cases.py | Treatment with conflicting guidance across NCCN and CMS sources | **Conflicting-guidelines branch_6** (positive case) | iter-1 |
| GC-012 | golden_cases.py | 14yo with severe persistent asthma uncontrolled on high-dose ICS/LABA, eos 450; eligible for dupilumab BUT pediatric+complexity triggers specialist | **Pediatric-complex escalation branch_2** (predicted fix in iter-3 chg-1; verified live 2→4); canonical risk case for iter-5 chg-4 asthma memory non-override of pediatric_complex check | iter-1; predicted_fix verified iter-3 chg-1; risk case for iter-5 chg-3 and chg-4 |
| GC-013 | golden_cases.py | Confidence-boundary case — borderline clinical documentation that should route ambiguously | **Confidence-low branch_3** (positive case) | iter-1 |
| GC-014 | golden_cases.py | Institutional-memory precedent guides approval — referenced precedent block in guidelines_context | **Institutional-memory precedent** (positive case) — predicates the v2.3 Phase H2 memory work | iter-1 |
| GC-015 | golden_cases.py | Incomplete submission with key lab values missing → IN_REVIEW | **Incomplete-docs IN_REVIEW** (positive case at "ambiguous" completeness tier) | iter-1 |
| GC-016 | golden_cases.py | Crohn's disease biologic (adalimumab) — adequate step therapy with azathioprine intolerance, immunomodulator failure, steroid dependence | **Coverage** (clean GI auto-approve); cross-condition memory bleed test for iter-4 chg-1 RA entry | iter-1; risk case for iter-4 chg-1 |
| GC-017 | golden_cases.py | Psoriatic arthritis biologic, NSAID-only step therapy (inadequate per ACR PsA Guidelines) | **Step-therapy enforcement** for PsA-specific guideline; cross-condition memory bleed test for iter-4 chg-1 RA entry | iter-1; risk case for iter-4 chg-1; jitter case (4↔2 across runs — informed iter-3 chg-3) |
| GC-018 | golden_cases.py | Sparse-notes hallucination trap — agent must not invent lab values | **Hallucination zero-tolerance** (sparse-docs adversarial) | iter-1 |
| GC-019 | golden_cases.py | Sparse-notes hallucination trap — agent must not assume prior therapy | **Hallucination zero-tolerance** (sparse-docs adversarial) | iter-1 |
| GC-020 | golden_cases.py | Oncological emergency requiring expedited processing | **Coverage** (urgent-care expedited workflow) | iter-1 |
| GC-021 | near_miss_cases.py | NSCLC pembrolizumab near-miss — PD-L1 45% (below 50% threshold); deliberately differs from GC-001 by one disqualifier | **False pattern-matching (memory trap)** — designed to catch H2 memory entries that compress "NSCLC + pembrolizumab → approve" too aggressively; risk case for iter-3 chg-2 NSCLC memory | iter-2 chg-3; risk case validated iter-3 chg-2 (initial regression → wording fix); preserved at iter-4/5 |
| GC-022 | near_miss_cases.py | NSCLC pembrolizumab near-miss — EGFR sensitizing mutation present (first-line is targeted therapy, not pembrolizumab) | **False pattern-matching (memory trap)** — same family as GC-021, different disqualifier; risk case for iter-3 chg-2 NSCLC memory | iter-2 chg-3; risk case for iter-3 chg-2; preserved at iter-4/5 |
| GC-023 | pediatric_cases.py | 10yo with mild well-controlled asthma on low-dose ICS, well-controlled markers (PEF, eos, FeNO normal) | **Discriminator negative class** for iter-5 chg-3 complexity-score model — pediatric BUT mild should NOT escalate; risk case for iter-5 chg-4 asthma memory non-override on mild cases | iter-5 chg-2; risk case for iter-5 chg-3 + chg-4 |
| GC-024 | pediatric_cases.py | 16yo with moderate Crohn's, immunomodulator failure, comorbid growth delay — clinical criteria for biologic met but multi-factor complexity warrants specialist review | **Discriminator ambiguous case** for iter-5 chg-3 complexity-score model — pushed over threshold by multiple weights | iter-5 chg-2; risk case for iter-5 chg-3 |
| GC-025 | pediatric_cases.py | 9yo with severe refractory atopic dermatitis, multiple topical + systemic failures, atopic march comorbidities | **Discriminator positive class** for iter-5 chg-3 (different disease from GC-012, validates score model generalizes beyond asthma) | iter-5 chg-2; risk case for iter-5 chg-3 |
| GC-026 | expansion_cases.py | Proton-beam radiation for low-risk prostate cancer (Gleason 6, PSA 5.2) with no contraindication to IMRT; patient preference cited as justification | **Coverage** (DENY class — closes the 0-DENY gap from `EVALUATION_COVERAGE.md`); also **step-therapy enforcement** parallel to GC-005 (preference is not a clinical justification) | iter-6 |
| GC-027 | expansion_cases.py | Cardiac catheterization for atypical chest pain in a 44yo with zero cardiac risk factors and no prior non-invasive workup (stress test or coronary CTA) | **Coverage** (DENY class, 2nd) + **cardiology specialty** (1st); probes ACC/AHA workup-hierarchy enforcement | iter-6 |
| GC-028 | expansion_cases.py | 82yo with ischemic cardiomyopathy, LVEF 28%, NYHA II on GDMT > 6 months, ICD implant meeting every CMS NCD 20.4 criterion | **Coverage** (cardiology auto-approve) + **age stratification ≥75 (1st geriatric case)**; probes that the agent does not escalate purely on age | iter-6 |
| GC-029 | expansion_cases.py | Adult ADHD stimulant request in a patient with concurrent cannabis use and AUD-in-remission; no formal neuropsych testing | **Coverage** (psychiatry/behavioral specialty, 1st) + **controlled-substance specialist-review gate**; tests routing to BRANCH_2 for SUD + Schedule II combination | iter-6 |
| GC-030 | expansion_cases.py | HbSS sickle cell with 5 painful crises in 12 months (3 hospitalized), hydroxyurea initiation per NHLBI/ASH | **Coverage** (hematology / rare-genetic auto-approve); probes that rare-condition pre-flight (branch_5) noting doesn't escalate when guideline criteria are clearly met | iter-6 |
| GC-031 | expansion_cases.py | 14-month post-renal-transplant maintenance tacrolimus refill, stable graft function, target trough | **Coverage** (nephrology/transplant auto-approve, 1st); probes that procedure-class complexity (transplant immunosuppression) does not over-escalate routine refills | iter-6 |
| GC-032 | expansion_cases.py | Chronic migraine (18 HA-days/month, MIDAS 28) with documented failure of 2 preventives (topiramate + propranolol); CGRP per AAN/AHS | **Coverage** (neurology auto-approve, 1st); probes that the agent does NOT demand onabotulinumtoxinA step-up before CGRP (common mis-application) | iter-6 |
| GC-033 | expansion_cases.py | 29yo with stage II breast cancer, pre-chemo oocyte cryopreservation per ASCO/ASRM (medically-indicated fertility preservation) | **Coverage** (reproductive-endocrine / OB-overlap auto-approve, 1st); probes that the agent distinguishes medically-indicated fertility preservation from elective fertility services | iter-6 |
| GC-034 | denial_cases.py | Off-label nivolumab for pancreatic adenocarcinoma without NCCN compendia support | **Coverage** (DENY — off-label oncology category); also tests CMS NCD compendia-based coverage logic | iter-6 Batch A |
| GC-035 | denial_cases.py | PT visits exceeded annual benefit cap (50 of 30 used); no documented exception criteria | **Coverage** (DENY — benefit-cap category); probes contractual vs medical-necessity distinction | iter-6 Batch A |
| GC-036 | denial_cases.py | Re-request for adalimumab 60 days after prior denial with identical documentation | **Coverage** (DENY — prior-denial-without-new-evidence category); also probes branch_7 interaction (pre-flight fires but no new evidence supports approve) | iter-6 Batch A |
| GC-037 | cardiology_cases.py | TAVR for severe symptomatic AS, intermediate STS, heart-team consensus documented | **Coverage** (cardiology AUTO_APPROVE — interventional); per CMS NCD 20.32 | iter-6 Batch B |
| GC-038 | cardiology_cases.py | AFib catheter ablation after failure of 2 antiarrhythmics (flecainide intolerance + sotalol inefficacy) | **Coverage** (cardiology AUTO_APPROVE — electrophysiology); ACC/AHA two-drug-failure criterion | iter-6 Batch B |
| GC-039 | cardiology_cases.py | ICD primary prevention denied — LVEF 36% just above CMS NCD 35% cutoff; ischemic CM | **Coverage** (DENY — threshold-boundary) + **near-miss to GC-028** (LVEF 28% AUTO_APPROVED); tests threshold discrimination at cardiology surface | iter-6 Batch B |
| GC-040 | cardiology_cases.py | Statin in 38yo with genetically-confirmed FH + strong family history; ACC/AHA FH exemption from age-based ASCVD | **Coverage** (cardiology AUTO_APPROVE — preventive); probes FH exemption to age-based ASCVD thresholds (common mis-application) | iter-6 Batch B |
| GC-041 | mental_health_cases.py | TMS for treatment-resistant MDD after 2 AD trials + augmentation failure | **Coverage** (psychiatry AUTO_APPROVE — TRD); APA + CMS NCD criteria | iter-6 Batch C |
| GC-042 | mental_health_cases.py | Esketamine intranasal for TRD requires SPRAVATO REMS + certified clinic | **REMS-required gate** (psychiatry IN_REVIEW); probes correct routing of REMS-program initiation | iter-6 Batch C |
| GC-043 | mental_health_cases.py | Inpatient psychiatric admission for active SI with specific plan + intent | **Coverage** (psychiatry AUTO_APPROVE — urgent level-of-care); CMS InterQual / MCG criteria; time-sensitive | iter-6 Batch C |
| GC-044 | mental_health_cases.py | LAI antipsychotic (paliperidone palmitate) for schizophrenia with documented non-adherence + 3 hospitalizations | **Coverage** (psychiatry AUTO_APPROVE — chronic disease management); same-molecule oral-to-LAI transition | iter-6 Batch C |
| GC-045 | mental_health_cases.py | 16yo MDD SSRI initiation triggers specialist review per FDA black box + suicidality monitoring | **Coverage** (psychiatry IN_REVIEW — pediatric safety gate); FDA black-box warning surface | iter-6 Batch C |
| GC-046 | geriatric_cases.py | 85yo cataract surgery with documented falls history + 20/100 vision | **Coverage** (geriatric AUTO_APPROVE — ophthalmology); probes that complexity-score model does NOT over-escalate purely on age | iter-6 Batch D |
| GC-047 | geriatric_cases.py | 88yo adjuvant FOLFOX for stage III colon cancer; G8 score 13 (impaired) | **Coverage** (geriatric IN_REVIEW — oncology with frailty); SIOG/NCCN comprehensive geriatric assessment | iter-6 Batch D |
| GC-048 | geriatric_cases.py | 82yo elective THA, ASA 2, independent in ADLs | **Coverage** (geriatric AUTO_APPROVE — orthopedic elective); probes age-only over-escalation failure mode | iter-6 Batch D |
| GC-049 | geriatric_cases.py | 84yo dialysis initiation with frailty + cognitive impairment + family ambivalence | **Coverage** (geriatric IN_REVIEW — shared decision-making); KDIGO + RPA SDM Guideline | iter-6 Batch D |
| GC-050 | pulmonology_adult_cases.py | Adult severe eosinophilic asthma dupilumab per GINA + EMA | **Coverage** (adult pulm AUTO_APPROVE); canonical positive for iter-5 chg-4 asthma H2 memory | iter-6 Batch E |
| GC-051 | pulmonology_adult_cases.py | COPD escalation to triple LABA/LAMA/ICS after exacerbation; eos 280 | **Coverage** (adult pulm AUTO_APPROVE — COPD); GOLD Group E step-up | iter-6 Batch E |
| GC-052 | pulmonology_adult_cases.py | Pulmonary rehab post-COPD-exacerbation, mMRC 3 | **Coverage** (adult pulm AUTO_APPROVE — rehab); CMS NCD 240.8 | iter-6 Batch E |
| GC-053 | pulmonology_adult_cases.py | CPAP initiation post-AASM-conformant home sleep study, AHI 28 | **Coverage** (adult pulm AUTO_APPROVE — sleep med); CMS NCD 240.4; probes that home study is acceptable | iter-6 Batch E |
| GC-054 | pulmonology_adult_cases.py | Adult severe asthma mepolizumab (anti-IL-5) | **Coverage** (adult pulm AUTO_APPROVE — biologic class diversity); sibling of GC-050 tests no class hierarchy | iter-6 Batch E |
| GC-055 | ambiguous_completeness_cases.py | Psoriasis biologic — prior MTX duration and dose omitted | **Documentation-completeness graded** (ambiguous-tier IN_REVIEW); tests INFORMATION_NEEDED vs DENIED distinction | iter-6 Batch G |
| GC-056 | ambiguous_completeness_cases.py | MS DMT — severity described qualitatively but EDSS score omitted | **Documentation-completeness graded** (ambiguous-tier IN_REVIEW); tests hallucination avoidance on missing standard metric | iter-6 Batch G |
| GC-057 | ambiguous_completeness_cases.py | T2DM intensification — HbA1c value present but measurement date omitted | **Documentation-completeness graded** (ambiguous-tier IN_REVIEW); ADA 90-day recency rule | iter-6 Batch G |
| GC-058 | ambiguous_completeness_cases.py | Oncology 2nd-line — prior regimen named but response not characterized | **Documentation-completeness graded** (ambiguous-tier IN_REVIEW); regimen choice depends on response classification | iter-6 Batch G |
| GC-059 | ambiguous_completeness_cases.py | CGRP migraine prevention — "tried multiple preventives" without naming agents | **Documentation-completeness graded** (ambiguous-tier IN_REVIEW); AAN/AHS step-therapy documentation standard | iter-6 Batch G |
| GC-060 | transplant_cases.py | Heart transplant tacrolimus initiation POD #8 per ISHLT | **Coverage** (transplant AUTO_APPROVE — initiation); probes that high target trough is appropriate for early post-op | iter-6 Batch H |
| GC-061 | transplant_cases.py | 8yo liver transplant tacrolimus refill — pediatric + transplant intersection | **Cross-condition escalation** (transplant IN_REVIEW); two complexity drivers (pediatric + transplant) | iter-6 Batch H |
| GC-062 | transplant_cases.py | Allogeneic BMT conditioning regimen for AML CR1 with adverse cytogenetics | **Coverage** (transplant IN_REVIEW — institutional protocol review by policy); ASTCT-recognized but BMT is always specialist-routed | iter-6 Batch H |
| GC-063 | transplant_cases.py | Renal transplant Banff IIA rejection treated with IV methylprednisolone | **Coverage** (transplant AUTO_APPROVE — acute rejection); KDIGO first-line; time-sensitive | iter-6 Batch H |
| GC-064 | neurology_cases.py | Ocrelizumab for highly active relapsing MS; JCV-negative; no prior DMT | **Coverage** (neurology AUTO_APPROVE — MS DMT); probes that current AAN guidance supports first-line high-efficacy (not platform DMT step-up) | iter-6 Batch I |
| GC-065 | neurology_cases.py | Lecanemab for early AD with amyloid PET+ and APOE ε4 heterozygote | **Coverage** (neurology IN_REVIEW — REMS-like surveillance); ARIA monitoring + APOE risk discussion | iter-6 Batch I |
| GC-066 | neurology_cases.py | VNS for refractory focal epilepsy after 3 AED failures + EMU eval (not surgical candidate) | **Coverage** (neurology IN_REVIEW — surgical-device specialist review); AAN VNS criteria met | iter-6 Batch I |
| GC-067 | neurology_cases.py | IV alteplase for acute ischemic stroke within 75 min of onset, NIHSS 14 | **Urgent-care expedited workflow** (neurology AUTO_APPROVE — time-critical); AHA/ASA Class I; tests no-delay routing | iter-6 Batch I |
| GC-068 | ob_cases.py | First-trimester dating ultrasound, uncertain LMP | **Coverage** (OB AUTO_APPROVE — routine prenatal); ACOG standard | iter-6 Batch J |
| GC-069 | ob_cases.py | NIPT cell-free DNA in 38yo AMA primigravida | **Coverage** (OB AUTO_APPROVE — prenatal screening); ACOG/SMFM endorsement | iter-6 Batch J |
| GC-070 | ob_cases.py | Brexanolone IV for postpartum depression after SSRI failure (REMS) | **REMS-required gate** (OB IN_REVIEW — Zulresso REMS); 60-hour infusion at certified setting | iter-6 Batch J |
| GC-071 | ob_cases.py | Gestational diabetes insulin initiation after diet failure at 28 weeks | **Coverage** (OB AUTO_APPROVE — gestational complication); ACOG insulin preference in pregnancy | iter-6 Batch J |
| GC-072 | ob_cases.py | Postpartum tubal ligation with Medicaid 30-day consent satisfied | **Coverage** (OB AUTO_APPROVE — sterilization); probes Medicaid-specific 42 CFR 441.250 consent rules | iter-6 Batch J |
| GC-073 | expansion_cases.py | Vedolizumab at $99,500/year — cost just under $100K threshold; clinically inappropriate for PsA | **Cost-boundary** (parser does not fire cost trigger under threshold); IN_REVIEW for clinical inappropriateness (separate concern) | iter-6 Batch F |
| GC-074 | expansion_cases.py | Abatacept at $102,000/year — cost just over $100K threshold; ACR criteria met | **Cost-boundary** (cost trigger fires at over-threshold); sibling of GC-010 ($288K) near boundary | iter-6 Batch F |
| GC-075 | expansion_cases.py | Mixed-cost case: $45K requested infliximab + extraneous $250K spouse-therapy mention | **Cost-boundary parser disambiguation**; tests that parser extracts requested-drug cost, not maximum dollar amount in notes | iter-6 Batch F |
| GC-076 | endocrinology_cases.py | Adjuvant RAI ablation after total thyroidectomy for intermediate-high-risk DTC | **Coverage** (endocrine AUTO_APPROVE — thyroid oncology); ATA risk stratification | iter-6 Batch K |
| GC-077 | endocrinology_cases.py | Adrenal MRI ordered before biochemical confirmation of Cushing's | **Sequential-workup enforcement** (endocrine IN_REVIEW); Endo Society biochem-before-imaging hierarchy | iter-6 Batch K |
| GC-078 | endocrinology_cases.py | Laparoscopic adrenalectomy for biochemically-confirmed 4.5cm pheochromocytoma post-alpha-blockade | **Coverage** (endocrine AUTO_APPROVE — surgical); Endo Society criteria | iter-6 Batch K |
| GC-079 | hematology_cases.py | IV iron sucrose for severe IDA after PO iron intolerance + minimal response | **Coverage** (hematology AUTO_APPROVE — deficiency anemia); AGA/ASH criteria | iter-6 Batch L |
| GC-080 | hematology_cases.py | AML 7+3 induction in fit adult with intermediate-risk cytogenetics | **Coverage** (hematology AUTO_APPROVE — leukemia induction); NCCN Category 1; time-sensitive | iter-6 Batch L |
| GC-081 | hematology_cases.py | ITP rituximab after corticosteroid + IVIG failure | **Coverage** (hematology AUTO_APPROVE — biologic 2nd-line); ASH 2019 | iter-6 Batch L |
| GC-082 | hematology_cases.py | Warfarin-associated ICH — 4-factor PCC reversal | **Urgent-care expedited workflow** (hematology AUTO_APPROVE — time-critical); AHA/ASA + NCS guideline; tests no-delay routing | iter-6 Batch L |
| GC-083 | oncology_depth_cases.py | Multiple myeloma DRd induction, transplant-eligible NDMM | **Coverage** (oncology AUTO_APPROVE — MM); NCCN Cat 1 | iter-6 oncology depth |
| GC-084 | oncology_depth_cases.py | Ovarian cancer PARP maintenance (olaparib) after platinum CR in BRCA1+ | **Coverage** (oncology AUTO_APPROVE — gyn-onc); NCCN Cat 1 / SOLO-1 | iter-6 oncology depth |
| GC-085 | oncology_depth_cases.py | Locally advanced H&N SCC — cetuximab + radiation (cisplatin-ineligible from CKD) | **Coverage** (oncology AUTO_APPROVE — H&N); NCCN bioradiotherapy alternative | iter-6 oncology depth |
| GC-086 | oncology_depth_cases.py | BRAF V600E metastatic melanoma — dabrafenib + trametinib (symptomatic) | **Coverage** (oncology AUTO_APPROVE — melanoma targeted); NCCN Cat 1 | iter-6 oncology depth |
| GC-087 | oncology_depth_cases.py | mCRPC progressing on ADT — abiraterone + prednisone | **Coverage** (oncology AUTO_APPROVE — prostate); NCCN Cat 1 | iter-6 oncology depth |
| GC-088 | oncology_depth_cases.py | Advanced HCC atezolizumab + bevacizumab, Child-Pugh A, EGD safety-cleared | **Coverage** (oncology AUTO_APPROVE — HCC); IMbrave150 / NCCN Cat 1; tests bevacizumab safety screen | iter-6 oncology depth |
| GC-089 | depth_extension_cases.py | 15yo mild UC mesalamine induction per ESPGHAN | **Coverage** (adolescent AUTO_APPROVE — IBD); tests pediatric_complex does NOT fire on mild severity | iter-6 Batch M |
| GC-090 | depth_extension_cases.py | 13yo severe MDD escitalopram initiation with passive death-wish ideation | **Coverage** (adolescent IN_REVIEW — psych); FDA black-box specialist gate | iter-6 Batch M |
| GC-091 | depth_extension_cases.py | 16yo healthy female combined OC contraception in minor-consent state | **Coverage** (adolescent AUTO_APPROVE — contraception); CDC USMEC Cat 1; tests state minor-consent recognition | iter-6 Batch M |
| GC-092 | depth_extension_cases.py | Knee MRI for suspected meniscal tear after PT × 6 weeks with mechanical symptoms | **Coverage** (imaging AUTO_APPROVE — orthopedic MRI); ACR Appropriateness | iter-6 Batch N |
| GC-093 | depth_extension_cases.py | Shoulder MRI for chronic rotator cuff symptoms after PT with positive exam | **Coverage** (imaging AUTO_APPROVE — orthopedic MRI surgical planning); ACR | iter-6 Batch N |
| GC-094 | depth_extension_cases.py | CTPA for high-Wells-probability PE workup with elevated D-dimer | **Urgent-care expedited workflow** (imaging AUTO_APPROVE — PE workup); time-sensitive; ACR + ATS/ESC | iter-6 Batch N |
| GC-095 | depth_extension_cases.py | Adalimumab for HS Hurley II after clindamycin + rifampin failure | **Coverage** (derm AUTO_APPROVE — HS biologic); only FDA-approved HS biologic | iter-6 Batch O |
| GC-096 | depth_extension_cases.py | Ruxolitinib topical for non-segmental vitiligo (newer FDA indication, 2022) | **Coverage** (derm IN_REVIEW — newer indication specialist review); FDA-approved | iter-6 Batch O |
| GC-097 | depth_extension_cases.py | Isotretinoin for severe scarring nodular acne after oral antibiotic + topical failure; iPLEDGE registered | **Coverage** (derm AUTO_APPROVE — REMS-managed); AAD + iPLEDGE | iter-6 Batch O |
| GC-098 | depth_extension_cases.py | Moderate UC vedolizumab first biologic after 5-ASA + steroid failure | **Coverage** (GI AUTO_APPROVE — UC biologic); ECCO + AGA; tests no class-hierarchy demand | iter-6 Batch P |
| GC-099 | depth_extension_cases.py | EoE dupilumab after PPI + topical steroid failure (newer FDA indication, 2022) | **Coverage** (GI IN_REVIEW — newer indication specialist review); FDA-approved | iter-6 Batch P |
| GC-100 | depth_extension_cases.py | Type II achalasia Heller myotomy + Dor fundoplication after pneumatic dilation failure | **Coverage** (GI AUTO_APPROVE — surgical; cap case at GC-100); ACG-endorsed; closes the iter-6 dataset-growth arc | iter-6 Batch P |

## How to use this document

- **Audit defense.** A reviewer asking "why does this case exist?" gets a per-case answer with citation to the iteration.
- **Regression triage.** A regression on case X tells the cycle exactly which iteration's contract is potentially broken.
- **Dataset planning.** When the dataset reaches a milestone (50/100/300/500), this document grows correspondingly — every new case requires a row.
- **SME review.** A clinical SME reviewing the dataset's appropriateness can scan this document for a high-level rationale per case without reading 25 case definitions.

## Add a case → add a row

When a new case lands, add a row with:
1. Case ID + file
2. ≤2-sentence clinical rationale
3. Named failure mode (use the established taxonomy below; add new modes only when an existing one doesn't fit)
4. Iteration of origin

**Established failure-mode taxonomy** (extend only when justified):
- Coverage (routine positive or negative case for a gate)
- Hallucination zero-tolerance
- False pattern-matching (memory trap)
- Step-therapy enforcement
- Cross-condition memory bleed
- Test-data adequacy
- Discriminator (negative / ambiguous / positive) class
- Branch-N pre-flight (where N = 1-7)
- Confidence-N boundary (where N = low / ambiguous / high)
- High-cost / pediatric-complex / other policy-trigger override

---

*This document is part of the PACCA v2.4+ harness-engineering cycle documentation set. Last updated: 2026-05-25 at iter-6 close (100-case state — production-pilot milestone hit).*
