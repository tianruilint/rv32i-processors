# Physical implementation (OpenROAD-flow-scripts)

The five-stage pipeline core (`rv32i_pipeline_core`) is taken from RTL to GDS
with [OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts)
on the Nangate45 platform: Yosys synthesis, floorplan (40 % core utilisation),
placement, clock-tree synthesis, global and detailed routing, fill, and a
final logic-equivalence check of the routed netlist against synthesis.

No RTL is changed for this flow. The constraints are the pre-layout
`timing/pipeline_constraints.sdc` (0.1 ns setup uncertainty, 0.5 ns input and
output delay, 5 fF output load) with only the clock period varied.

## Files

| Path | Contents |
| --- | --- |
| `pnr/nangate45/config.mk` | ORFS design config; `FLOW_VARIANT` selects the clock |
| `pnr/nangate45/constraint_*ns.sdc` | Copies of the pipeline SDC with the period changed |
| `pnr/summarize.py` | Rebuilds the sweep table from `reports/pnr/` |
| `reports/pnr/<clock>/` | Saved final metrics, final SDC, route-DRC count and LEC result per clock |
| `reports/pnr/1p6ns/6_finish.rpt`, `reports/pnr/1p4ns/6_finish.rpt` | Full final timing reports for the fastest closing and the first failing clock |
| `docs/pnr/*_1p6ns.webp` | Placement, all-layer, routing, clock-tree and worst-path images of the 625 MHz run |

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
Copy `logs/.../6_report.json`, `results/.../6_final.sdc`, the line count of
`reports/.../5_route_drc.rpt` and the last line of `logs/.../6_final_lec_check.log`
into `reports/pnr/<clock>/`, then run `python3 pnr/summarize.py`.

## Clock sweep

| Clock | Freq | WNS (ns) | TNS (ns) | Hold WS (ns) | Max-slew / max-cap viol. | Route DRC | Power | Std-cell area (µm²) | Repair buffers | LEC |
| ---: | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | --- |
| 10.0 ns | 100 MHz | +8.174 (met) | 0.000 | +0.009 | 0 / 1 | 0 | 2.47 mW | 20,304 | 883 | equivalent |
| 2.2 ns | 455 MHz | +0.515 (met) | 0.000 | +0.016 | 0 / 0 | 0 | 9.87 mW | 20,314 | 883 | equivalent |
| 2.0 ns | 500 MHz | +0.348 (met) | 0.000 | +0.017 | 0 / 3 | 0 | 10.85 mW | 20,312 | 885 | equivalent |
| 1.8 ns | 556 MHz | +0.180 (met) | 0.000 | +0.015 | 0 / 0 | 0 | 12.01 mW | 20,336 | 894 | equivalent |
| 1.6 ns | 625 MHz | +0.080 (met) | 0.000 | +0.020 | 0 / 1 | 0 | 13.43 mW | 20,403 | 956 | equivalent |
| 1.4 ns | 714 MHz | -0.006 (**violated**) | -0.020 | +0.010 | 0 / 0 | 0 | 15.26 mW | 20,577 | 1080 | equivalent |
| 1.2 ns | 833 MHz | -0.176 (**violated**) | -14.647 | +0.014 | 0 / 0 | 0 | 18.38 mW | 22,677 | 1886 | equivalent |

Power is the ORFS default activity estimate at each clock, not a workload
measurement. The 1–3 remaining max-capacitance violators at 10, 2.0 and
1.6 ns were left by the repair step and are reported as-is.

## Limiting paths

- **MEM/WB → branch compare → flush → ID/EX (2.2–1.4 ns).** From
  `u_mem_wb.out_result_src` through the write-back result select, MEM/WB-to-EX
  forwarding and the 32-bit branch comparator to `redirect`; as `flush`, it
  synchronously clears every ID/EX field (`pipeline_id_ex.sv`), so the
  endpoints are unrelated ID/EX flops such as `alu_op`, `pc` and `imm`. This
  is the internal frequency limiter; it fails by 6 ps at 1.4 ns. Clearing
  only the valid bit and write enables on a flush would cut that fanout.
- **`reset` input → `data_write_data` output (1.6 and 1.2 ns).** A
  combinational feed-through: `pipeline_mem.sv` gates the store data with
  `!reset`, so the output depends on the input port within the same cycle.
  With 0.5 ns input and 0.5 ns output budgets, little of a 1.6 ns period is
  left for this path, and at 1.2 ns it is the worst violating path.
  Registering the memory-interface outputs (or dropping the reset gating on
  the data, keeping it on `data_write_en`) would remove it.

## Layout images (1.6 ns run)

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
