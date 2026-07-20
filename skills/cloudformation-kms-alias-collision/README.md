# cloudformation-kms-alias-collision

Fix CloudFormation deployment failures caused by KMS alias collisions. Use when:
(1) CDK deploy fails with "AWS::EarlyValidation::ResourceExistenceCheck" error,
(2) Multiple CDK stacks create KMS keys with similar aliases,
(3) Deployment fails before changeset execution due to resource existence check.
Covers diagnosing KMS alias conflicts and resolving them in CDK stacks.
