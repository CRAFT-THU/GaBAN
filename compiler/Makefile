SOURCES = lif.py lif_simplify.py lif_snava.py lif_fixed.py if.py izhikevich.py izhikevich_euler.py hodgkin_huxley.py izhikevich_fixed.py poisson_source.py spike.py lif_snava_fixed.py
PATHS = $(patsubst %.py,../models/%.py,$(SOURCES))

all: $(patsubst %.py,%.h,$(PATHS))
.PRECIOUS: %.ssa %.asm %.hex %.ssa_opt

%.h: %.hex %.asm header.py
	python3 header.py $^ > $@

%.hex: %.asm assembler.py
	python3 assembler.py $^ > $@

%.asm: %.ssa_opt compiler.py
	python3 compiler.py $^ > $@

%.ssa_opt: %.ssa src/bin/optimizer/main.rs
	cargo run --bin optimizer -- $< > $@

%.ssa: %.py ../models/ir.py
	python3 $< > $@

clean:
	cd ../models && rm -rf *.asm *.ssa *.ssa_opt *.h *.hex
