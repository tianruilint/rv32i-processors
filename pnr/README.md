# Physical implementation (OpenROAD-flow-scripts)

The five-stage pipeline core (`rv32i_pipeline_core`) is taken from RTL to GDS
with [OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts)
on the Nangate45 platform: Yosys synthesis, floorplan (40 % core utilisation),
placement, clock-tree synthesis, global and detailed routing, fill, and a
final logic-equivalence check of the routed netlist against synthesis.

The first sweep found two RTL-caused limiting paths; after the RTL fix below
the whole sweep was rerun on 2026-11-07 (results in `reports/pnr/<clock>/`, the
first sweep kept in `reports/pnr/pre_flush_fix/`). The constraints are the pre-layout
`timing/pipeline_constraints.sdc` (0.1 ns setup uncertainty, 0.5 ns input and
output delay, 5 fF output load) with only the clock period varied.

## Files

| Path | Contents |
| --- | --- |
| `pnr/nangate45/config.mk` | ORFS design config; `FLOW_VARIANT` selects the clock |
| `pnr/nangate45/constraint_*ns.sdc` | Copies of the pipeline SDC with the period changed |
| `pnr/summarize.py` | Rebuilds the sweep table from `reports/pnr/` |
| `reports/pnr/<clock>/` | Saved final metrics, final SDC, route-DRC count and LEC result per clock |
| `reports/pnr/{1p6ns,1p4ns,1p2ns}/6_finish.rpt` | Full final timing reports around the fastest closing clock |
| `reports/pnr/pre_flush_fix/` | The first sweep, before the RTL fix, in the same layout |
| `pnr/collect.sh` | Copies the files above out of an ORFS `flow/` directory |
| `docs/pnr/*_1p6ns.webp` | Placement, all-layer, routing, clock-tree and worst-path images of the first-sweep 625 MHz run |

## Reproducing

Tools used: ORFS `cca3a7179`, OpenROAD `26Q4-518-gbc739caf43`, Yosys `0.68+`
(`a5af9d690`), built locally on WSL Ubuntu 24.04 with `./setup.sh` and
`./build_openroad.sh --local`.

```bash
cd OpenROAD-flow-scripts && source env.sh && cd flow
CFG=<path-to-this-repo>/pnr/nangate45/config.mk
make DESIGN_CONFIG=$CFG                      # 10 ns, results in .../base
make DESIGN_CONFIG=$CFG FLOW_VARIANT=fast    # 2.2 ns
make DESIGN_CONFIG=$CFG FLOW_VARIANT=p2p0    # 2.0 ns (also p1p8, p1p6, p1p4, p1p2)
```

Results land in `flow/{logs,reports,results}/nangate45/rv32i_pipeline/<variant>/`.
`bash pnr/collect.sh <ORFS>/flow` copies `6_report.json`, `6_final.sdc`, the
route-DRC line count and the LEC result into `reports/pnr/<clock>/`; then run
`python3 pnr/summarize.py`. Run `make ... clean_all` for a variant first when
the RTL has changed.

## Clock sweep

| Clock | Freq | WNS (ns) | TNS (ns) | Hold WS (ns) | Max-slew / max-cap viol. | Route DRC | Power | Std-cell area (µm²) | Repair buffers | LEC |
| ---: | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | --- |
| 10.0 ns | 100 MHz | +8.228 (met) | 0.000 | +0.016 | 0 / 1 | 0 | 2.48 mW | 20,339 | 915 | equivalent |
| 2.2 ns | 455 MHz | +0.483 (met) | 0.000 | +0.019 | 0 / 0 | 0 | 9.89 mW | 20,328 | 910 | equivalent |
| 2.0 ns | 500 MHz | +0.367 (met) | 0.000 | +0.013 | 0 / 0 | 0 | 10.84 mW | 20,337 | 913 | equivalent |
| 1.8 ns | 556 MHz | +0.188 (met) | 0.000 | +0.011 | 0 / 1 | 0 | 12.01 mW | 20,379 | 935 | equivalent |
| 1.6 ns | 625 MHz | +0.076 (met) | 0.000 | +0.019 | 0 / 0 | 0 | 13.50 mW | 20,425 | 974 | equivalent |
| 1.4 ns | 714 MHz | +0.005 (met) | 0.000 | +0.015 | 0 / 0 | 0 | 15.29 mW | 20,543 | 1072 | equivalent |
| 1.2 ns | 833 MHz | -0.015 (**violated**) | -0.125 | +0.020 | 0 / 1 | 0 | 17.85 mW | 21,496 | 1690 | equivalent |

Power is the ORFS default activity estimate at each clock, not a workload
measurement. The single max-capacitance violator left at 10, 1.8 and 1.2 ns
was left by the repair step and is reported as-is.

## First sweep and RTL fix

The first sweep closed at 1.6 ns (+0.080) and failed at 1.4 ns (−0.006,
TNS −0.020) and 1.2 ns (−0.176, TNS −14.647, 1,886 repair buffers). Its
limiting paths were caused by the RTL, not the flow:

- **MEM/WB → branch compare → flush → ID/EX (2.2–1.4 ns).** From
  `u_mem_wb.out_result_src` through the write-back result select, MEM/WB-to-EX
  forwarding and the 32-bit branch comparator to `redirect`; as `flush`, it
  synchronously cleared every ID/EX field, so the endpoints were unrelated
  ID/EX flops such as `alu_op`, `pc` and `imm`.
- **`reset` input → `data_write_data` output (1.6 and 1.2 ns).** A
  combinational feed-through: `pipeline_mem.sv` gated the store data with
  `!reset`, so the output depended on the input port within the same cycle,
  using both 0.5 ns I/O budgets.

Fix: a slot with valid=0 cannot write memory, write a register, or redirect,
so `pipeline_id_ex.sv` now clears only valid, `reg_write`, `mem_write`,
`branch` and `jump_type` on flush/bubble and clears the payload only on
reset; `pipeline_frontend.sv` invalidates IF/ID on a redirect without clearing
its payload; and `pipeline_mem.sv` applies reset to `data_write_en` only.
The 74-case regression and the ISA reference cases pass after the change.

| Clock | WNS before → after (ns) | TNS before → after (ns) |
| ---: | ---: | ---: |
| 1.6 ns | +0.080 → +0.076 | 0 → 0 |
| 1.4 ns | −0.006 → **+0.005** | −0.020 → 0 |
| 1.2 ns | −0.176 → −0.015 | −14.647 → −0.125 |

Above 1.4 ns the differences are within run-to-run placement variation.

## Limiting paths now

- **MEM/WB `rd` / ID/EX `rs2` → forwarding → branch compare → redirect →
  `stall` → IF/ID enable (1.6 and 1.4 ns).** `stall` is `load_use && !redirect`,
  so the redirect still reaches the IF/ID hold enable. Holding IF/ID on the raw
  load-use signal would remove it, since a redirected slot is invalid anyway.
- **ID/EX `rs2_addr` → forwarding select → 32-bit ALU → EX/MEM `alu_result`
  (1.2 ns).** The usual EX-stage path of a five-stage pipeline; shortening it
  needs a micro-architectural change rather than a fanout fix.

## Layout images (first-sweep 1.6 ns run)

| Image | Shows |
| --- | --- |
| [final_placement](../docs/pnr/final_placement_1p6ns.webp) | Standard-cell placement and I/O pins |
| [final_clocks](../docs/pnr/final_clocks_1p6ns.webp) | Routed clock tree and CTS buffers |
| [final_routing](../docs/pnr/final_routing_1p6ns.webp) | Signal routing on all metal layers |
| [final_worst_path](../docs/pnr/final_worst_path_1p6ns.webp) | Worst setup path highlighted |
| [final_all](../docs/pnr/final_all_1p6ns.webp) | Every layer overlaid: cells, signal routing, power-grid straps (wide horizontal bars) and pins |

## Limits

- Nangate45 is an open educational library; analysis is single-corner
  (typical) with ideal I/O budgets taken from the pre-layout SDC.
- Core-only block: no memories, I/O pads or package; external memories are
  modelled only by the I/O delays.
- No IR-drop/EM signoff, LVS against a foundry deck, or multi-corner analysis
  is claimed.
