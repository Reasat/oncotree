.PHONY: all help install test verify update-mappings cleanup

# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: oncotree.owl oncotree.sssom.tsv

# build: Create new oncotree.owl
# - OncoTree JSON is downloaded by the script at runtime
oncotree.owl:
	python3 -m oncotree2obo
	make cleanup

# Create mapping artefact(s)
oncotree.json: oncotree.owl
	robot convert -i $< -o oncotree.json

# Create SSSOM mapping file from OWL
oncotree.sssom.tsv: oncotree.json
	sssom parse oncotree.json -I obographs-json -m data/metadata.sssom.yml -o oncotree.sssom.tsv
	make cleanup

# Update mappings from upstream sources
update-mappings:
	python3 -m oncotree2obo.update_mappings
	make cleanup

cleanup:
	@rm -f oncotree.json

# SETUP / INSTALLATION -------------------------------------------------------------------------------------------------
install:
	pip install -r requirements-unlocked.txt --user --break-system-packages

# QA / TESTING ---------------------------------------------------------------------------------------------------------
test:
	python3 -m unittest discover -v

# Verify oncotree.owl entity counts match API (or use: oncotree2obo.verify -j FILE)
verify: oncotree.owl
	python3 -m oncotree2obo.verify

# HELP -----------------------------------------------------------------------------------------------------------------
help:
	@echo "----------------------------------------"
	@echo "	Command reference: OncoTree"
	@echo "----------------------------------------"
	@echo "all"
	@echo "Creates all release artefacts.\n"
	@echo "oncotree.owl"
	@echo "Creates main release artefact: oncotree.owl\n"
	@echo "oncotree.sssom.tsv"
	@echo "Creates an SSSOM TSV of OncoTree terms.\n"
	@echo "update-mappings"
	@echo "Updates mappings from upstream sources.\n"
	@echo "install"
	@echo "Install's Python requirements.\n"
	@echo "test"
	@echo "Runs unit tests.\n"
	@echo "verify"
	@echo "Verifies oncotree.owl entity counts match API (or use -j FILE for JSON).\n"
