#!/usr/bin/env python3
"""Write article_answers.jsonl: the AI answers Razavi scored in his two articles, as printed there.

Part 1 (Fall 2025) gives ChatGPT's answers to 30 questions, Part 2 (June 2026) Gemini 3.1 Pro's
answers to 20; each with Razavi's 0-4 score. The text below is transcribed from the article pages,
which print abridged answers; parenthetical notes such as "(A small-signal analysis is also
provided.)" are Razavi's and are kept. Square brackets mark the one editorial insertion: P2 Q8 cites
"(5)", the gain expression Gemini gave in its answer to Q7, which is written out. Article question
n maps to task part1-0nn / part2-0nn. Each answer is written JUDGE_REPEATS times (rollout 1..3) so
that GPT-6 Luna grades it independently three times.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
JUDGE_REPEATS = 3

PART1 = [  # (ChatGPT answer, Razavi's score)
    ("A_i = g_m r_O, g_m ∝ √(W/L), r_O ∝ L; thus, g_m r_O is doubled.", 4),
    ("g_m = μ_n C_ox (W/L) V_ov = 2 I_D / V_ov. At fixed V_ov, a larger V_ov yields a larger g_m. At fixed I_D, increasing V_ov makes g_m go down.", 2),
    ("Yes.", 4),
    ("For V_X ≤ V_TH, I_X ≈ 0. For V_X > V_TH, I_X rises quadratically with V_X.", 4),
    ("For V_TH < V_X < V_TH + 1 V, I_X rises quadratically. For V_X > V_TH + 1 V, it transitions to a straight line.", 4),
    ("Yes, it can act as a current source. The device is an NMOS transistor with its gate shorted to its drain and called a diode-connected MOSFET.", 0),
    ("Transistor M1 is an NMOS device whose source is connected to R_S. A_v = −g_m R_D / (1 + g_m R_S).", 1),
    ("This is a source follower. A_v = g_m R_S / (1 + g_m R_S).", 4),
    ("This is a common-source amplifier. The input is applied to the gate.", 0),
    ("This is a common-gate amplifier. The input is applied at the source (through C1). A_v ≈ g_m R_D.", 1),
    ("There are two independent energy-storing nodes. Thus, the circuit has two poles.", 3),
    ("M1: NMOS, source at ground. R1-R2: Resistor divider at output. The circuit has negative feedback.", 3),
    ("M1 (NMOS) acts as the main amplifying transistor. M2 (NMOS) acts as a current-source load. The circuit is a common-source amplifier with an active load. A_v ≈ −g_m1 (r_O1 ∥ r_O2).", 0),
    ("This is the classic CMOS inverter.", 4),
    ("M1: A PMOS transistor; M2: An NMOS transistor. This is the CMOS inverter.", 0),
    ("This is a common-source stage with a diode-connected load. A_v = −g_m1 / (g_m2 + 1/r_O2).", 3),
    ("The circuit has two stacked NMOS devices. M2 acts as a diode-connected load, and M1 as the amplifying transistor. A_v = −g_m1 / g_m2.", 0),
    ("This is a cascoded NMOS current source. Looking into the output node (the drain of M1, i.e., the node between M1 and M2), R_out = r_O1 + r_O2 + g_m2 r_O1 r_O2. Intuition: The cascode device M2 holds the drain of M1 nearly constant.", 0),
    ("Treat M2 as the PMOS device whose source is at V_DD. So we ensure that M2 is in saturation by choosing V_b2 so that X never rises above V_b2 + |V_T2|.", 1),
    ("This is a common-source amplifier with an active load. M1: NMOS, M2: PMOS, with its drain connected to X and its source to V_out.", 0),
    ("Yes, this is a cascode structure. The output resistance becomes r_out ≈ g_m2 r_O2 r_O1.", 0),
    ("In a cascode, you stack a common-gate device (M2) on top of the common-source device (M1). The drain of M1 is \"clamped\" by M2, which keeps the voltage at the drain of M1 relatively constant. So the effective gain across C_gd1 is very small.", 3),
    ("M1 (PMOS), M2 (NMOS), its gate receives V_in. This is a common-source amplifier with an active load. V_out = −g_m2 r_O,eq V_in.", 0),
    ("Two poles as there are two independent energy-storing nodes. The output node contains C_GS2 (to the ac-grounded gate of M2), etc.", 3),
    ("Response 1: This is a two-NMOS series transistor with a resistive load. This is a differential-style cascode, sometimes called a gain-boosting stage. A_v = −g_m1 (r_O1 ∥ r_O2 ∥ R_D). Response 2: M2 is a diode-connected NMOS. This is the classic NMOS differential amplifier's \"half-circuit.\"", 0),
    ("M1: NMOS with its gate driven by V_in, M2: NMOS used as an active load/current mirror transistor. This is a common-source amplifier with an NMOS cascode.", 0),
    ("This is a cascode circuit with source degeneration at the input. Looking into the drain of M2, Z_out ≈ g_m1 R_S / (s C_gs1). The gate-source capacitance of M1 combined with R_S creates a phase shift. After being \"buffered\" by the cascode transistor, M2, this combination mimics an inductor.", 2),
    ("M1: NMOS, common-source stage; M2: NMOS, diode-connected (its gate and drain are shorted at X). The input is a current source.", 1),
    ("M1: NMOS, with gate at X; M2: NMOS, gate biased at constant V_b; R_F: Feedback resistor. M1 converts the source voltage into a drain current. M2 is a common-source amplifier with fixed gate bias V_b.", 2),
    ("M1: NMOS; acts as a cascode transistor. M2: NMOS, with the gate tied to the input, operates as the amplifying device.", 0),
]
PART2 = [  # (Gemini 3.1 Pro answer, Razavi's score)
    ("No, it does not. The circuit simply operates at a lower frequency. (A small-signal analysis is also provided.)", 4),
    ("The phase noise falls by a factor of four. (An analysis based on the edge rate is also provided.)", 4),
    ("Yes, it does. (A small-signal analysis is also provided.)", 4),
    ("The phase noise drops by 3 dB.", 4),
    ("We have R_X ≈ (1/3)(1/g_m1 + 1/g_m2) because each inverter behaves as two diode-connected devices in series.", 1),
    ("Yes, it does. The average resistance is now much higher because the path from V_DD to ground through the transistors is off most of the time.", 1),
    ("As this width increases, the gain drops. Equation (1) in the article, A_v ≈ g_m1,2 V_THN / I_CM, suggests that a greater I_CM (= I_D7) lowers A_v because g_m1,2 ∝ √I_CM.", 4),
    ("The gain remains constant because [A_v ≈ g_m1,2 V_THN / I_CM] does not depend on this capacitance.", 4),
    ("It degrades because their transconductance increases by a smaller factor than do their capacitances.", 1),
    ("The speed degrades because the data-driven devices are the bottleneck.", 2),
    ("Yes, it does. The output at Y or Z is in quadrature with respect to that at X.", 2),
    ("The speed degrades, and charge sharing leads to catastrophic results.", 1),
    ("This is a divide-by-two circuit using dynamic latches.", 4),
    ("The inverter acts as a keeper, forming a cross-coupled latch with the first inverter. This removes the minimum clock frequency requirement (due to leakage).", 0),
    ("I apologize. This creates a problematic configuration. There must be a mistake in this drawing.", 0),
    ("The NF is given by F ≈ 1 + R_s/R_F + γ and the input resistance by R_in = (R_F + R_L) / (1 + g_m,tot R_L), where R_L is the load resistance. We maximize R_L by choosing long-channel devices so that R_in → 1/g_m,tot. The lowest NF is given by 1 + γ if R_in = R_s = 1/g_m,tot and R_F is large enough.", 1),
    ("This is a shunt-shunt feedback amplifier. R_in = R_F / (1 + |A_vol|), where A_vol = −(1/2) g_m1 g_m2,3 R_D1 (R_D2 ∥ R_F).", 2),
    ("We need to find the VCO pushing gain, defined as K_push = ∂f_osc/∂V_out, typically found by SPICE simulations. Then, L(Δf) = 10 log(K_push² S_th / (2 Δf²)).", 3),
    ("It generally lowers the phase noise by shunting the I_SS noise at 2ω0 and by suppressing the 2ω0 voltage ripple at the tail node, which could push the transistors into the triode region. The capacitor pins P to ground and ensures that M1 and M2 are in saturation.", 1),
    ("If the total capacitance at each node is C_node, then ω_osc = ω0 + Δω, where ω0 = 1/√(L C_node) and Δω = g_mc / (2 C_node). Here, g_mc denotes the transconductance of the coupling pairs.", 1),
]


def main() -> None:
    assert len(PART1) == 30 and len(PART2) == 20
    assert sum(s for _, s in PART1) == 49 and sum(s for _, s in PART2) == 44   # 49/120 and 44/80, as printed
    slugs = {p.name[:9]: p.name for p in (REPO / "tasks").iterdir() if p.is_dir()}
    rows = []
    for part, model, answers in (("part1", "article_chatgpt", PART1), ("part2", "article_gemini_31_pro", PART2)):
        for number, (answer, score) in enumerate(answers, 1):
            slug = slugs[f"{part}-{number:03d}"]
            for repeat in range(1, JUDGE_REPEATS + 1):
                rows.append({"benchmark": "razavi-bench", "experiment": "2026-11-09-razavi-calibration", "task_slug": slug,
                             "task_path": f"tasks/{slug}", "rollout": repeat, "model_name": model,
                             "article_question": f"{part[:1].upper()}{part[-1]} Q{number}", "razavi_score": score, "answer": answer})
    with (HERE / "article_answers.jsonl").open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} rows ({len(rows) // JUDGE_REPEATS} answers x {JUDGE_REPEATS} judge repeats)")


if __name__ == "__main__":
    main()
