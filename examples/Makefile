.PHONY: help 01 02 03 clean-all

REPO ?= $(shell git rev-parse --show-toplevel 2>/dev/null || echo ".")

help:
	@echo "rebuild examples — available targets:"
	@echo ""
	@echo "  make 01          01-dry-run-walk      — scan last 30 days, no deploy"
	@echo "  make 02          02-docker-compose-project — full walk with docker"
	@echo "  make 03          03-restore-endpoint  — restore last working endpoint"
	@echo ""
	@echo "  make REPO=/path/to/repo 01   run against a specific repository"
	@echo ""
	@echo "  make clean-all   remove .rebuild output dirs from all examples"

01:
	@echo "==> Example 01: dry-run walk on $(REPO)"
	bash 01-dry-run-walk/run.sh "$(REPO)"

02:
	@echo "==> Example 02: docker-compose walk on $(REPO)"
	bash 02-docker-compose-project/run.sh "$(REPO)"

03:
	@echo "==> Example 03: restore endpoint from $(REPO)"
	bash 03-restore-endpoint/run.sh "$(REPO)"

clean-all:
	rm -rf 01-dry-run-walk/.rebuild
	rm -rf 02-docker-compose-project/.rebuild
	rm -rf 03-restore-endpoint/.rebuild
	rm -rf 03-restore-endpoint/restored/
	@echo "Cleaned all example output directories."
