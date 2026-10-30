# OpenROAD-flow-scripts design config: five-stage RV32I pipeline core on Nangate45.
# Run from the ORFS flow/ directory:
#   make DESIGN_CONFIG=<repo>/pnr/nangate45/config.mk

PNR_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO_DIR := $(abspath $(PNR_DIR)/../..)

export DESIGN_NAME     = rv32i_pipeline_core
export DESIGN_NICKNAME = rv32i_pipeline
export PLATFORM        = nangate45

export VERILOG_FILES = $(REPO_DIR)/rtl/alu.sv \
                       $(REPO_DIR)/rtl/decoder.sv \
                       $(REPO_DIR)/rtl/immediate_generator.sv \
                       $(REPO_DIR)/rtl/register_file.sv \
                       $(REPO_DIR)/rtl/pipeline_frontend.sv \
                       $(REPO_DIR)/rtl/pipeline_id.sv \
                       $(REPO_DIR)/rtl/pipeline_id_ex.sv \
                       $(REPO_DIR)/rtl/pipeline_ex.sv \
                       $(REPO_DIR)/rtl/pipeline_ex_mem.sv \
                       $(REPO_DIR)/rtl/pipeline_mem.sv \
                       $(REPO_DIR)/rtl/pipeline_mem_wb.sv \
                       $(REPO_DIR)/rtl/pipeline_hazard.sv \
                       $(REPO_DIR)/rtl/rv32i_pipeline_core.sv

# Same constraints as the pre-layout OpenSTA run (10 ns clock).
export SDC_FILE = $(REPO_DIR)/timing/pipeline_constraints.sdc

export CORE_UTILIZATION = 40
export PLACE_DENSITY    = 0.60

# Optional tighter-clock variant: make ... FLOW_VARIANT=fast
ifeq ($(FLOW_VARIANT),fast)
export SDC_FILE = $(PNR_DIR)/constraint_2p2ns.sdc
endif
ifeq ($(FLOW_VARIANT),p2p0)
export SDC_FILE = $(PNR_DIR)/constraint_2p0ns.sdc
endif
ifeq ($(FLOW_VARIANT),p1p8)
export SDC_FILE = $(PNR_DIR)/constraint_1p8ns.sdc
endif
ifeq ($(FLOW_VARIANT),p1p6)
export SDC_FILE = $(PNR_DIR)/constraint_1p6ns.sdc
endif
ifeq ($(FLOW_VARIANT),p1p4)
export SDC_FILE = $(PNR_DIR)/constraint_1p4ns.sdc
endif
ifeq ($(FLOW_VARIANT),p1p2)
export SDC_FILE = $(PNR_DIR)/constraint_1p2ns.sdc
endif
