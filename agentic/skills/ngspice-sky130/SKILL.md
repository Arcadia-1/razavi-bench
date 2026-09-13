---
name: ngspice-sky130
description: "Use ngspice with the Razavi-Bench Sky130 model bundle when a task has a concrete quantity worth probing. Provides workflows for operating-point checks, small-signal extraction, and simple AC/transient sanity tests. Use simulation selectively as evidence; final answers must be driven by analog-circuit reasoning and stated assumptions."
---

# Sky130 Ngspice Skill

Use this skill when a Razavi-Bench task benefits from checking a circuit intuition with ngspice and the bundled Sky130 1.8 V primitive models. You are not required to simulate every task. Use ngspice when it can answer a clearly stated electrical question; skip it when the task is mainly conceptual, topological, or under-specified.

Do not treat simulation as the answer. Many tasks are qualitative, depend on small-signal assumptions, or omit exact device sizes and bias points. A simulation is useful only if the deck topology, held-fixed condition, bias condition, device sizes, and measured quantity match the question you are answering. If a Sky130 simulation conflicts with a textbook trend, first check whether you changed the assumptions.

This is simulation-assisted reasoning, not grounded PDK truth. Some tasks are
property-strong: a small equation deck or simplified netlist can reproduce the
exact trend or mechanism the question asks about. Other tasks are topology-only,
state-counting, or sign-convention tasks where simulation should be skipped.

## Environment

In the Razavi-Bench `ngspice-sky130` setting:

- task files are in `/app`;
- Sky130 models are in `/tools/ngspice-sky130/models`;
- example decks are in `/tools/ngspice-sky130/examples`;
- this skill, when installed for Claude Code, is in `/app/.claude/skills/ngspice-sky130`.

The core include is:

```spice
.include "/tools/ngspice-sky130/models/sky130.lib.spice"
```

If you are running from a checkout instead of Vela, use a relative path to `simulator/ngspice-sky130/models/sky130.lib.spice`.

## Required Geometry Units

Sky130 instance geometry is expressed in SI units. Every device must use
explicit suffixes, for example:

```spice
Xn d g s b sky130_fd_pr__nfet_01v8 w=1.26u l=0.15u
```

Never write unitless geometry such as `w=1.26 l=0.15`. Ngspice interprets
those values as meters. The `W/L` ratio can leave a DC trend looking plausible
while absolute current, transconductance, capacitance, AC response, and
transient behavior are wrong by many orders of magnitude. Before trusting a
deck, inspect at least one absolute operating-point quantity or capacitance and
confirm that the dimensions carry `u` suffixes.

## Bundled Assets

The skill includes reusable Sky130 templates and runners:

```text
assets/
├── run_op_probe.py        # Render and run one operating-point probe
├── run_examples.py        # Run standard sanity-check examples
├── sky130_common.py       # Model discovery, template rendering, ngspice runner
├── templates/             # Small OP probes: nfet, pfet, CS, source follower
└── netlist/               # Standard examples: RC, I-V, CS AC, mirror, TG Ron
```

The standard examples write generated decks and logs to `./ngspice_outputs/` by default, or to `$SKY130_NGSPICE_OUTPUT_DIR` if set. Treat these as scratch artifacts. Do not edit files under `.claude/skills` unless the user is improving the skill itself; copy a generated deck into `/app` before adapting it for a task.

## Decision Workflow

Before running ngspice, write down the intended use of simulation in one sentence:

```text
I will simulate <quantity/trend> while holding <condition> fixed, because the task asks about <same condition>.
```

If you cannot fill in that sentence honestly, do not simulate. Answer from analog reasoning and state the missing information.

Use this order:

1. Read `/app/instruction.md` and inspect any PNGs in `/app`.
2. Identify the intended analysis assumption: long-channel vs. PDK device, fixed current vs. fixed voltage/overdrive, fixed geometry ratio vs. fixed width/length, small-signal vs. large-signal, open-loop vs. feedback.
3. Classify the question by probe family using the general table below. Do this from the task itself; do not rely on per-task routing hints.
4. Decide whether ngspice can test the same assumption.
5. If yes, run a minimal deck and use the result as supporting evidence.
6. If no, skip simulation and give the analog-circuit answer directly.

Do not run a generic MOS probe merely because this skill is available. A generic probe is useful only to learn syntax or to check the simulator installation; it is not evidence for an unrelated task.

## Minimal Simulation Workflow

1. Decide what the simulation is supposed to test: operating point, sign, trend, pole, gain, impedance, or switch resistance.
2. Create a new deck under `/app`, or copy an example from `/tools/ngspice-sky130/examples`.
3. Check that the deck matches the question. Do not blindly reuse example topology, sizes, bias, or held-fixed conditions.
4. Run:

```bash
ngspice -b /app/your_deck.cir > /app/your_deck.log 2>&1
```

5. Read the log, compare it against the theoretical mechanism, then write only the final reasoning to `/app/answer.md`.

## Zero-Start Quickstart

If you have never used ngspice in this environment and the task appears simulation-suitable, do this first:

```bash
ls -la /app
ls -la /tools/ngspice-sky130/models
ls -la /tools/ngspice-sky130/examples
ngspice --version
```

You may run a known-good probe to learn syntax:

```bash
python3 /app/.claude/skills/ngspice-sky130/assets/run_op_probe.py \
  --template nfet_op \
  --out /app/nfet_op.cir

sed -n '1,120p' /app/nfet_op.cir
sed -n '1,160p' /app/nfet_op.log
```

This teaches the three essential pieces, but it is not task evidence unless the task is actually an NMOS operating-point probe:

- a deck includes `sky130.lib.spice`;
- the transistor instance name `Xn` maps to ngspice operating-point variables such as `@m.xn.msky130_fd_pr__nfet_01v8[gm]`;
- `.control ... print ... .endc` prints values into the log.

After that, copy the closest generated deck and change only what the question requires. If no generated deck matches the task topology and assumptions, do not force it.

Available helper templates:

```text
nfet_op
pfet_op
common_source_op
source_follower_op
```

Example:

```bash
python3 /app/.claude/skills/ngspice-sky130/assets/run_op_probe.py \
  --template source_follower_op \
  --out /app/source_follower_op.cir
```

To see the broader example set:

```bash
python3 /app/.claude/skills/ngspice-sky130/assets/run_examples.py --example all
python3 /app/.claude/skills/ngspice-sky130/assets/run_examples.py --example nmos_iv
python3 /app/.claude/skills/ngspice-sky130/assets/run_examples.py --example cs_ac
```

Available standard examples:

```text
rc_tran
rc_ac
nmos_iv
cs_ac
current_mirror
tgate_ron
```

## Choosing A Probe

Before writing a deck, classify the task. Use ngspice only when the task has a concrete electrical quantity that can be probed under a stated bias condition and a clear held-fixed condition.

| Question type | Useful probe | Avoid |
| --- | --- | --- |
| Device region, saturation, overdrive, bias feasibility | `.op`, print node voltages and device operating-point values | treating one arbitrary bias as proof for all operating points |
| Gain, source follower gain, transconductance trend | `.op` for `gm`, `gds`, `gmbs`; optional `.ac` if the topology is fully specified | using a common-source deck for a different topology |
| Input/output resistance | inject a small test current or voltage source and compute `v/i` | measuring the wrong port or leaving independent sources active incorrectly |
| Capacitance, pole, speed, or phase-noise trend | use simulation only as a sanity check for sign/trend after deriving the mechanism | pretending Sky130 short-channel numbers are the textbook answer |
| Feedback interpretation, latch topology, oscillation condition, qualitative “why” questions | usually answer from analog reasoning directly | forcing a simulation without a complete transient setup |
| Textbook MOS scaling, intrinsic gain, gm trends | reason from the stated square-law or small-signal assumptions first; simulate only if the task explicitly asks for a PDK/device example | letting one fixed-bias Sky130/BSIM4 result override a long-channel or held-current/held-overdrive conclusion |

If the figure or prompt omits sizes, loads, bias currents, clock waveforms, or initial conditions, state the missing assumption. A simulation with invented values can support a trend, but it cannot replace the reasoning. If different reasonable assumptions give different answers, say so.

## Supported Probe Families

Use these generic probe families for any Razavi-Bench task. They are public
skill capabilities, not per-task hints:

| Probe family | How to use it |
| --- | --- |
| `equation_scaling` | Write a `.control` deck that computes the formula or trend directly, such as `gm`, `Rin`, oscillator `f0`, feedback conductance, or frequency shift. |
| `long_channel_equation` | Explicitly encode long-channel assumptions such as `lambda ~ 1/L`; do not use minimum-channel Sky130 as the final evidence for textbook long-channel questions. |
| `sky130_dc_op` | Use the bundled Sky130 primitives for operating point, region, `gm`, `gds`, and local transfer sanity checks. |
| `small_signal_gain` | Probe gain sign/magnitude with `.op`-derived small-signal values or a simple `.ac` setup when topology and bias are specified. |
| `resistance_impedance` | Inject a test source or write a small equivalent network to compute input resistance, output resistance, transimpedance, or negative resistance. |
| `timing_delay_toy` | Use explicit RC/timing equations to check delay and capacitance trends; state that it is illustrative unless clocks and parasitics are specified. |
| `noise_phase_equation` | Encode the phase-noise/noise formula or nonmonotonic qualitative terms; do not claim quantitative oscillator-noise truth without a proper setup. |
| `topology_only` | Usually skip simulation; the answer is in the figure connectivity or topology classification. |
| `state_counting` | Skip simulation as primary evidence; answer by counting independent dynamic nodes or latch states. |
| `sign_convention` | Skip simulation as primary evidence; answer by explaining small-signal variable orientation and signs. |

## Backend-Callable Skill Contract

A backend can expose this skill uniformly for all tasks by providing the same
files and tools every time:

```text
/app/instruction.md
/app/figure-*.png
/tools/ngspice-sky130/models
/tools/ngspice-sky130/examples
/app/.claude/skills/ngspice-sky130
```

Do not give the agent a task-specific list of recommended probes, expected
simulation value, or known useful deck. The agent should infer the probe family
from the task statement and figure. The backend may log which files were created
and whether ngspice was invoked, but scoring should still use only
`/app/answer.md`.

A reasonable agent workflow is:

1. State the analog mechanism before simulation.
2. State the probe family and held-fixed condition.
3. Build the smallest deck that tests that condition.
4. Compare the result with the mechanism.
5. Put only the conclusion and any concise supporting trend in `/app/answer.md`.

If the agent cannot state the mechanism and held-fixed condition, it should not
simulate.

## Generic Equation Deck Pattern

For textbook or under-specified questions, an equation-level ngspice deck is
often better than a fabricated transistor-level circuit. Use this form when the
task asks about a formula or scaling law:

```spice
* Example: compute a trend directly from stated equations.
Vx x 0 1

.control
dc Vx 1 4 1
let scale=v(x)
let quantity=<expression involving scale>
print scale quantity
.endc

.end
```

This is appropriate for trends such as `gm` scaling, `Rin` formulas, oscillator
frequency scaling, Miller multiplication, feedback input conductance, or
phase-noise proportionalities. Clearly label it as an equation-level probe.

## Generic Port-Probe Pattern

For resistance and impedance questions, use an explicit test source at the port
whose impedance is being asked about:

```spice
* Example pattern: inject 1 A AC and read V/I.
Itest in 0 AC 1

.control
ac dec 20 1 1e9
let zin=v(in)/1
print zin
.endc

.end
```

Deactivate or small-signal-ground independent sources according to the circuit
question. If the required port is ambiguous, resolve the topology first instead
of probing an arbitrary node.

## Generic Sky130 Device Pattern

Use the bundled Sky130 devices for sanity checks where the question is about a
specific transistor topology, region, local gain sign, or operating-point
quantity. Keep the device dimensions, bias, and load simple and explicitly
stated.

Do not use this pattern to override textbook assumptions. For example, a
minimum-channel BSIM result may fail to show an ideal long-channel trend; in
that case, use a long-channel equation probe and mention the PDK caveat.

## Common Checks

Operating point:

```spice
.op
.control
run
print v(out)
let gm=@m.xn.msky130_fd_pr__nfet_01v8[gm]
let gds=@m.xn.msky130_fd_pr__nfet_01v8[gds]
print gm gds
.endc
```

Small-signal gain estimate:

```spice
let gain_cs=-gm/(gds+1/20000)
print gain_cs
```

Source-follower estimate:

```spice
let gain_sf=gm/(gm+@m.xn.msky130_fd_pr__nfet_01v8[gmbs]+1/10000)
print gain_sf
```

Sanity checks before trusting a result:

- Is the device in the intended region? Check `vds`, `vgs`, threshold, and `vdsat` when possible.
- Are you holding the same quantity fixed as the question? For example, fixed overdrive, fixed current, fixed geometry ratio, and fixed VGS can produce different trends.
- Are the model limits relevant? A Sky130 short-channel simulation may disagree with a long-channel textbook assumption.
- Is the result a model artifact or bias artifact? If the result is surprising, rerun with a second bias or derive the expected trend before trusting it.
- Does the sign convention match the circuit? PMOS and NMOS signs can look different while the small-signal form is equivalent.
- Does the question provide enough numerical detail for simulation? If not, state the assumption and use simulation only as a qualitative sanity check.
- Did the deck answer the same question? A common-source example does not answer a source-follower question; a fixed-`VGS` sweep does not answer a fixed-current design question.

## When Not To Simulate

Skip simulation, or treat it only as secondary evidence, when:

- the question asks for a pure topology classification;
- the figure lacks enough device sizes, loads, or bias points;
- the intended answer is a long-channel textbook trend;
- the question asks about sign conventions, model form, or feedback interpretation.
- you would need to invent most of the circuit, bias, or waveform details.

In these cases, write the analog reasoning directly and mention any assumptions.

## Writing The Final Answer

The grader reads `/app/answer.md`, not your `.cir` files or logs. Your final answer should include:

- the circuit conclusion;
- the key analog mechanism;
- the relevant assumption, if simulation required one;
- at most one concise simulation-backed number or trend, only if it truly supports the conclusion.

Do not paste raw ngspice logs into `/app/answer.md`.

## Helper Scripts

The `assets/` directory contains small Python helpers that copy templates into `/app`, run ngspice, and print parsed output. They are convenience tools, not required.

Example:

```bash
python3 /app/.claude/skills/ngspice-sky130/assets/run_op_probe.py \
  --template nfet_op \
  --out /app/nfet_op.cir
```

Then inspect `/app/nfet_op.log`.
