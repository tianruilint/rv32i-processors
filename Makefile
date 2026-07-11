SHELL := /bin/bash

PROJECT_ROOT := $(abspath .)
RTL_DIR := $(PROJECT_ROOT)/rtl
TB_DIR := $(PROJECT_ROOT)/tb
BUILD_DIR := $(PROJECT_ROOT)/build
REPORTS_DIR := $(PROJECT_ROOT)/reports
WAVES_DIR := $(PROJECT_ROOT)/waves
VENV_BIN := $(PROJECT_ROOT)/.venv/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest
COCOTB_CONFIG := $(VENV_BIN)/cocotb-config
RTL_SOURCE := $(RTL_DIR)/full_adder.sv
ALU_RTL_SOURCE := $(RTL_DIR)/alu.sv
REGISTER_FILE_RTL_SOURCE := $(RTL_DIR)/register_file.sv
PC_RTL_SOURCE := $(RTL_DIR)/pc.sv
IMMEDIATE_GENERATOR_RTL_SOURCE := $(RTL_DIR)/immediate_generator.sv
DECODER_RTL_SOURCE := $(RTL_DIR)/decoder.sv
CORE_RTL_SOURCES := \
	$(RTL_DIR)/rv32i_core.sv \
	$(PC_RTL_SOURCE) \
	$(DECODER_RTL_SOURCE) \
	$(REGISTER_FILE_RTL_SOURCE) \
	$(IMMEDIATE_GENERATOR_RTL_SOURCE) \
	$(ALU_RTL_SOURCE)
CORE_TEST_MODULES := test_core,test_lw_sw,test_beq,test_program
COCOTB_MAKEFILES := $(shell $(COCOTB_CONFIG) --makefiles 2>/dev/null)
SEED ?= 20260916

.PHONY: env lint test waves clean check-venv prepare-generated-dirs lint-alu lint-core test-alu waves-alu test-register-file test-pc test-immediate-generator test-decoder test-core waves-core regression

# Keep the original per-module targets; this entry runs and summarizes all of them.
# Targets refresh XML under reports/; the runner overwrites per-target logs
# under reports/regression/. No per-run manifest is generated.
regression: check-venv
	@'$(PYTHON)' '$(PROJECT_ROOT)/scripts/run_regression.py' --seed '$(SEED)'

env:
	@printf '%s\n' '=== RV32I project verification environment ==='
	@printf 'Project root: %s\n' '$(PROJECT_ROOT)'
	@uname -a
	@git --version
	@make --version | head -n 1
	@verilator --version
	@python3 --version
	@if command -v pytest >/dev/null 2>&1; then pytest --version; else echo 'system pytest: not found (project uses .venv)'; fi
	@if command -v cocotb-config >/dev/null 2>&1; then cocotb-config --version; else echo 'system cocotb-config: not found (project uses .venv)'; fi
	@gtkwave --version 2>&1 | head -n 1
	@yosys -V
	@riscv64-unknown-elf-gcc --version | head -n 1
	@riscv64-unknown-elf-objdump --version | head -n 1
	@if command -v gh >/dev/null 2>&1; then gh --version | head -n 1; else echo 'gh: not found'; fi
	@if [ -x '$(PYTHON)' ]; then '$(PYTHON)' --version; else echo '.venv python: not found'; fi
	@if [ -x '$(PIP)' ]; then '$(PIP)' --version; else echo '.venv pip: not found'; fi
	@if [ -x '$(PYTEST)' ]; then '$(PYTEST)' --version; else echo '.venv pytest: not found'; fi
	@if [ -x '$(COCOTB_CONFIG)' ]; then '$(COCOTB_CONFIG)' --version; else echo '.venv cocotb-config: not found'; fi

# -Wno-fatal keeps bootstrap warnings visible while allowing the intentionally
# incomplete educational module to reach cocotb. It does not suppress warnings.
lint:
	verilator --lint-only --Wall -Wno-fatal --top-module full_adder '$(RTL_SOURCE)'

lint-alu:
	verilator --lint-only --Wall -Wno-fatal --top-module alu '$(ALU_RTL_SOURCE)'

lint-core:
	verilator --lint-only --Wall -Wno-fatal --top-module rv32i_core $(CORE_RTL_SOURCES)

check-venv:
	@test -x '$(PYTHON)' || { echo 'Missing .venv; create it and install requirements.txt.' >&2; exit 1; }
	@test -x '$(COCOTB_CONFIG)' || { echo 'Missing cocotb in .venv; install requirements.txt.' >&2; exit 1; }
	@test -n '$(COCOTB_MAKEFILES)' || { echo 'Unable to locate cocotb makefiles.' >&2; exit 1; }

prepare-generated-dirs:
	@mkdir -p '$(BUILD_DIR)' '$(REPORTS_DIR)' '$(WAVES_DIR)'

test: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/full_adder.xml'
	@PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(RTL_SOURCE)' \
		COCOTB_TOPLEVEL=full_adder \
		COCOTB_TEST_MODULES=test_full_adder \
		SIM_BUILD='$(BUILD_DIR)/verilator-test' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/full_adder.xml' \
		'$(REPORTS_DIR)/full_adder.xml'

test-alu: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/alu.xml'
	@PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(ALU_RTL_SOURCE)' \
		COCOTB_TOPLEVEL=alu \
		COCOTB_TEST_MODULES=test_alu \
		SIM_BUILD='$(BUILD_DIR)/verilator-alu' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/alu.xml' \
		'$(REPORTS_DIR)/alu.xml'

test-register-file: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/register_file.xml'
	@PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(REGISTER_FILE_RTL_SOURCE)' \
		COCOTB_TOPLEVEL=register_file \
		COCOTB_TEST_MODULES=test_register_file \
		SIM_BUILD='$(BUILD_DIR)/verilator-register-file' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/register_file.xml' \
		'$(REPORTS_DIR)/register_file.xml'

test-pc: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/pc.xml'
	@PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(PC_RTL_SOURCE)' \
		COCOTB_TOPLEVEL=pc \
		COCOTB_TEST_MODULES=test_pc \
		SIM_BUILD='$(BUILD_DIR)/verilator-pc' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/pc.xml' \
		'$(REPORTS_DIR)/pc.xml'

test-immediate-generator: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/immediate_generator.xml'
	@PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(IMMEDIATE_GENERATOR_RTL_SOURCE)' \
		COCOTB_TOPLEVEL=immediate_generator \
		COCOTB_TEST_MODULES=test_immediate_generator \
		SIM_BUILD='$(BUILD_DIR)/verilator-immediate-generator' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/immediate_generator.xml' \
		'$(REPORTS_DIR)/immediate_generator.xml'

test-decoder: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/decoder.xml'
	@PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(DECODER_RTL_SOURCE)' \
		COCOTB_TOPLEVEL=decoder \
		COCOTB_TEST_MODULES=test_decoder \
		SIM_BUILD='$(BUILD_DIR)/verilator-decoder' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/decoder.xml' \
		'$(REPORTS_DIR)/decoder.xml'

test-core: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/core.xml'
	@PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(CORE_RTL_SOURCES)' \
		COCOTB_TOPLEVEL=rv32i_core \
		COCOTB_TEST_MODULES='$(CORE_TEST_MODULES)' \
		SIM_BUILD='$(BUILD_DIR)/verilator-core' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/core.xml' \
		'$(REPORTS_DIR)/core.xml'


waves: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/full_adder-waves.xml' dump.fst
	@set +e; \
	PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal --trace-fst' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(RTL_SOURCE)' \
		COCOTB_TOPLEVEL=full_adder \
		COCOTB_TEST_MODULES=test_full_adder \
		SIM_BUILD='$(BUILD_DIR)/verilator-waves' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/full_adder-waves.xml' \
		WAVES=1 \
		SIM_ARGS='--trace' \
		'$(REPORTS_DIR)/full_adder-waves.xml'; \
	status=$$?; \
	if [ -f dump.fst ]; then \
		mv -f dump.fst '$(WAVES_DIR)/full_adder.fst'; \
		printf 'FST waveform: %s\n' '$(WAVES_DIR)/full_adder.fst'; \
	else \
		echo 'Expected FST waveform dump.fst was not generated.' >&2; \
		if [ $$status -eq 0 ]; then status=1; fi; \
	fi; \
	exit $$status

waves-alu: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/alu-waves.xml' dump.fst
	@set +e; \
	PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal --trace-fst' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(ALU_RTL_SOURCE)' \
		COCOTB_TOPLEVEL=alu \
		COCOTB_TEST_MODULES=test_alu \
		COCOTB_TEST_FILTER=test_cases1 \
		SIM_BUILD='$(BUILD_DIR)/verilator-alu-waves' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/alu-waves.xml' \
		WAVES=1 \
		SIM_ARGS='--trace' \
		'$(REPORTS_DIR)/alu-waves.xml'; \
	status=$$?; \
	if [ -f dump.fst ]; then \
		mv -f dump.fst '$(WAVES_DIR)/alu.fst'; \
		printf 'FST waveform: %s\n' '$(WAVES_DIR)/alu.fst'; \
	else \
		echo 'Expected FST waveform dump.fst was not generated.' >&2; \
		if [ $$status -eq 0 ]; then status=1; fi; \
	fi; \
	exit $$status

waves-core: check-venv prepare-generated-dirs
	@rm -f '$(REPORTS_DIR)/core-waves.xml' dump.fst
	@set +e; \
	PATH='$(VENV_BIN)':$$PATH PYTHONPATH='$(TB_DIR)' \
	COMPILE_ARGS='--Wall -Wno-fatal --trace-fst' \
	$(MAKE) --no-print-directory -f '$(COCOTB_MAKEFILES)/Makefile.sim' \
		SIM=verilator \
		TOPLEVEL_LANG=verilog \
		VERILOG_SOURCES='$(CORE_RTL_SOURCES)' \
		COCOTB_TOPLEVEL=rv32i_core \
		COCOTB_TEST_MODULES='$(CORE_TEST_MODULES)' \
		SIM_BUILD='$(BUILD_DIR)/verilator-core-waves' \
		COCOTB_RESULTS_FILE='$(REPORTS_DIR)/core-waves.xml' \
		WAVES=1 \
		SIM_ARGS='--trace' \
		'$(REPORTS_DIR)/core-waves.xml'; \
	status=$$?; \
	if [ -f dump.fst ]; then \
		mv -f dump.fst '$(WAVES_DIR)/core.fst'; \
		printf 'FST waveform: %s\n' '$(WAVES_DIR)/core.fst'; \
	else \
		echo 'Expected FST waveform dump.fst was not generated.' >&2; \
		if [ $$status -eq 0 ]; then status=1; fi; \
	fi; \
	exit $$status


clean:
	@find '$(BUILD_DIR)' '$(REPORTS_DIR)' '$(WAVES_DIR)' \
		-mindepth 1 ! -name .gitkeep -delete
	@find '$(TB_DIR)' -type f -name '*.py[co]' -delete
	@find '$(TB_DIR)' -type d -name __pycache__ -empty -delete
	@rm -rf '$(PROJECT_ROOT)/.pytest_cache'
	@rm -f '$(PROJECT_ROOT)/dump.vcd' '$(PROJECT_ROOT)/dump.fst' \
		'$(PROJECT_ROOT)/results.xml'
