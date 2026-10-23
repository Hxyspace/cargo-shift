SHELL := /bin/sh

# Use an installed compiler, or the optional toolchain bootstrapped in this repo.
CL65 ?= $(if $(shell command -v cl65 2>/dev/null),cl65,$(if $(wildcard .tools/cc65/bin/cl65),$(CURDIR)/.tools/cc65/bin/cl65,cl65))
HOST_CC ?= cc
PYTHON ?= python3

# The tested cc65 revision miscompiles game code with OptDupLoads enabled.
NES_CFLAGS := -Oirs --cc-args --disable-opt,OptDupLoads -I src/common -I assets/generated
TEST_CFLAGS ?= -std=c99 -Wall -Wextra -Werror -fsanitize=address,undefined -g
GENERATED := assets/generated/cargo_config.h assets/generated/cargo_tiles.chr assets/generated/cargo_view.h assets/generated/cargo_levels.h assets/generated/tile_ids.h
HEADERS := src/common/nes.h src/cargo_shift/model.h $(filter %.h,$(GENERATED))
OBJECTS := build/common/startup.o build/common/nes.o build/cargo_shift/chr.o build/cargo_shift/view.o build/cargo_shift/main.o build/cargo_shift/model.o

.PHONY: all clean assets solve test check verify bootstrap
all: build/cargo_shift.nes

$(GENERATED):
	@printf 'Missing %s; restore assets/generated/ or run make assets.\n' '$@' >&2
	@exit 1

build/common/startup.o: src/common/startup.s
	mkdir -p $(@D)
	"$(CL65)" -t nes -c -o $@ $<

build/common/nes.o: src/common/nes.c $(HEADERS) Makefile
	mkdir -p $(@D)
	"$(CL65)" -t nes $(NES_CFLAGS) -c -o $@ $<

build/cargo_shift/chr.o: src/cargo_shift/chr.s assets/generated/cargo_tiles.chr
	mkdir -p $(@D)
	"$(CL65)" -t nes --bin-include-dir assets/generated -c -o $@ $<

build/cargo_shift/view.o: src/cargo_shift/view.s
	mkdir -p $(@D)
	"$(CL65)" -t nes -c -o $@ $<

build/cargo_shift/%.o: src/cargo_shift/%.c $(HEADERS) Makefile
	mkdir -p $(@D)
	"$(CL65)" -t nes $(NES_CFLAGS) -c -o $@ $<

build/cargo_shift.nes: $(OBJECTS) tools/nrom.cfg
	"$(CL65)" -t nes -C tools/nrom.cfg -m build/cargo_shift.map -Ln build/cargo_shift.lbl -o $@ $(OBJECTS)

# Regeneration is explicit: normal builds use the committed runtime resources.
assets:
	$(PYTHON) tools/generate_assets.py

solve:
	$(PYTHON) tools/solve_levels.py

build/test-cargo: tests/test_cargo.c tests/fixtures/cargo_solutions.h src/cargo_shift/model.c src/cargo_shift/model.h assets/generated/cargo_levels.h Makefile
	mkdir -p $(@D)
	$(HOST_CC) $(TEST_CFLAGS) -I assets/generated -I tests/fixtures tests/test_cargo.c src/cargo_shift/model.c -o $@

test: build/test-cargo
	./build/test-cargo

check: all
	$(PYTHON) tools/check_rom.py build/cargo_shift.nes
	$(PYTHON) tools/check_budget.py cargo_shift

verify: test check

bootstrap:
	bash tools/bootstrap_cc65.sh

clean:
	rm -rf build
