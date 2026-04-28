.PHONY: test test-api test-ui

test: test-api test-ui

test-api:
	cd cheerleader-api && bash test.sh

test-ui:
	cd cheerleader-ui && npm test
