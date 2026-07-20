# cdk-test-optimization

Fix extremely slow AWS CDK tests (30+ minutes for a single test file). Use when:
(1) CDK tests take 30+ minutes to run,
(2) Each test creates `new cdk.App()` in beforeEach,
(3) Tests trigger Docker image builds repeatedly,
(4) Jest shows tests running but no progress for minutes,
(5) Disk fills up during test runs (see also: cdk-temp-folder-disk-bloat).
Solution: Use beforeAll to share CDK synthesis across tests.
