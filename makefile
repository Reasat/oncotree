.PHONY: all help install verify cleanup

# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: verify mappings/oncotree.sssom.tsv

# build: Create new mappings/oncotree.owl
# - OncoTree JSON is downloaded by the script at runtime
mappings/oncotree.owl:
	python3 -m oncotree2obo
	make cleanup

# Create mapping artefact(s)
mappings/oncotree.json: mappings/oncotree.owl
	robot convert -i $< --format json -o $@

# Create SSSOM mapping file from OWL
mappings/oncotree.sssom.tsv: mappings/oncotree.json
	sssom parse $< -I obographs-json -m data/metadata.sssom.yml -o $@
	make cleanup

cleanup:
	@rm -f mappings/oncotree.json

# SETUP / INSTALLATION -------------------------------------------------------------------------------------------------
install:
	pip install -r requirements-unlocked.txt --user --break-system-packages

# Verify mappings/oncotree.owl entity counts match API (or use: oncotree2obo.verify -j FILE)
verify: mappings/oncotree.owl
	python3 -m oncotree2obo.verify

# HELP -----------------------------------------------------------------------------------------------------------------
help:
	@echo "----------------------------------------"
	@echo "	Command reference: OncoTree"
	@echo "----------------------------------------"
	@echo "all"
	@echo "Creates all release artefacts.\n"
	@echo "mappings/oncotree.owl"
	@echo "Creates main release artefact: mappings/oncotree.owl\n"
	@echo "mappings/oncotree.sssom.tsv"
	@echo "Creates an SSSOM TSV of OncoTree terms.\n"
	@echo "install"
	@echo "Install's Python requirements.\n"
	@echo "verify"
	@echo "Verifies mappings/oncotree.owl entity counts match API (or use -j FILE for JSON).\n"
