.PHONY: download storm allplot clean

# Download SYM-H data from OMNIWeb
# Usage: make download START=240510 END=240513
download:
	python3 src/download_symh.py $(START) $(END)

# Run storm identification (individual plots per storm)
# Usage: make storm
#        make storm LLIMIT=30
storm:
	python3 src/mstorm.py $(if $(LLIMIT),--llimit $(LLIMIT),)

# Run storm identification (all storms in one figure)
# Usage: make allplot
#        make allplot LLIMIT=30
allplot:
	python3 src/mstorm.py --all $(if $(LLIMIT),--llimit $(LLIMIT),)

# Run both download and storm identification
# Usage: make all START=240510 END=240513 LLIMIT=90
all: download storm

# Clean output files
clean:
	rm -rf output/*
