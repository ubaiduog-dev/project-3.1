# Statistical Validation Report

## Purpose

This report records the statistical validation performed in Step 4. Each tested finding is documented with the claim, statistical test, result, effect size where applicable, sample size, and a plain-English verdict.

## T1. Does winning the toss help you win the match?

### Claim
Winning the toss helps a team win the match.

### Hypothesis
- **H₀:** The toss winner's true match-win rate is 50%.
- **H₁:** The toss winner's true match-win rate is different from 50%.

### Test
Binomial test.

### Result
- Decisive matches: **1,187**
- Toss winner also won: **613**
- Observed win rate: **51.64%**
- p-value: **0.2700**
- 95% Wilson confidence interval: **48.80%–54.48%**
- Effect: **1.64 percentage points above 50%**

### Verdict
**NOT SIGNIFICANT.**

The p-value is greater than 0.05, so we fail to reject H₀. There is insufficient evidence that winning the toss changes the chance of winning the match.

---

## T2. Does the decision taken after the toss matter?

### Claim
The decision made after winning the toss is associated with match outcome.

### Hypothesis
- **H₀:** Batting first and fielding first have the same win rate.
- **H₁:** Their win rates are different.

### Test
Chi-square test of independence.

### Result
- Bat first: **184 wins, 218 losses**
- Bat-first win rate: **45.77%**
- Field first: **429 wins, 356 losses**
- Field-first win rate: **54.65%**
- Difference: **8.88 percentage points**
- Chi-square: **8.04**
- p-value: **0.0046**
- Degrees of freedom: **1**

### Verdict
**SIGNIFICANT.**

The p-value is less than 0.05, so we reject H₀. The decision taken after the toss is associated with match outcome. The guide notes that this is another view of the chase advantage tested in T3, rather than a completely separate effect.

---## T3. Does the chasing team have an advantage?

### Claim
The chasing team has an advantage.

### Hypothesis
- **H₀:** The chase win rate is 50%.
- **H₁:** The chase win rate is different from 50%.

### Test
Binomial test.

### Result
- Decisive matches: **1,187**
- Successful chases: **647**
- Chase win rate: **54.51%**
- Difference from 50%: **4.51 percentage points**
- p-value: **0.0021**
- 95% Wilson confidence interval: **51.66%–57.32%**

### Verdict
**SIGNIFICANT.**

The p-value is less than 0.05, so we reject H₀. There is evidence that the chase win rate differs from 50%, with the observed rate being above 50%.