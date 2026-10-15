# Build all proofs with coqc (via coq_makefile).  `make` fails on any error.
COQMAKEFILE ?= Makefile.coq

all: $(COQMAKEFILE)
	+$(MAKE) -f $(COQMAKEFILE) all

$(COQMAKEFILE): _CoqProject
	coq_makefile -f _CoqProject -o $(COQMAKEFILE)

clean:
	if [ -f $(COQMAKEFILE) ]; then $(MAKE) -f $(COQMAKEFILE) cleanall; fi
	rm -f $(COQMAKEFILE) $(COQMAKEFILE).conf .$(COQMAKEFILE).d

.PHONY: all clean
