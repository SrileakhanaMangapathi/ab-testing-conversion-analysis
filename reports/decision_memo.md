# Marketing A/B Test Decision Memo

## Recommendation

Roll out the advertisement, provided the expected value of an incremental conversion exceeds the marginal cost of serving the campaign. The experiment shows a clear positive conversion effect, and the confidence interval excludes effects close to zero.

## Primary result

The analysis compares 564,577 users shown the advertisement with 23,524 users shown the PSA. The advertisement group recorded 14,423 conversions (2.555%), while the PSA group recorded 420 conversions (1.785%).

The estimated advertisement effect is:

- Absolute lift: **0.769 percentage points**
- Relative lift: **43.1%**
- 95% confidence interval: **0.595 to 0.943 percentage points**
- Two-sided z-statistic: **7.37**
- P-value: **1.71 × 10⁻¹³**

At a 5% significance level, the null hypothesis of equal conversion rates is rejected. The lower confidence bound remains materially positive: about 595 additional conversions per 100,000 exposed users.

## Power and experiment quality

The observed effect had approximately 100% achieved power. For a future test designed to detect an absolute lift of 0.20 percentage points with 80% power and a two-sided 5% significance level, the estimated requirement is 72,547 users per group, or 145,094 total users with equal allocation.

The source data contains 588,101 unique users, no missing required values, no duplicate users, and both expected experiment groups. Treatment allocation is highly uneven at roughly 24 advertisement users per PSA user. This does not invalidate the proportion test, but equal allocation would generally provide better precision per enrolled user in future experiments.

## Limitations and safeguards

- The recommendation assumes group assignment was randomized and implementation was free of interference. The dataset does not document the randomization mechanism or experiment duration.
- The analysis evaluates user conversion, not revenue, profit, retention, or downstream customer quality.
- The 0.20 percentage-point planning threshold is an analytical assumption and should be replaced with a business-approved minimum worthwhile effect.
- Day and hour results are exploratory. They were not used for the primary decision and should not be interpreted as confirmed segment effects without multiplicity control and follow-up testing.
- The dataset does not reveal whether the sample size and stopping rule were selected before results were examined.

## Follow-up actions

1. Confirm assignment randomization and the planned stopping rule with the experiment owner.
2. Estimate incremental profit using the confidence interval, not only the point estimate.
3. Monitor conversion quality and downstream retention after rollout.
4. Prefer balanced allocation in future experiments unless there is an operational reason for unequal groups.
