# Groundedness calibration

Hand-label each claim below as GROUNDED or NOT GROUNDED against the
context shown, **before** looking at the judge's verdicts (kept in a
separate results file specifically so this stays blind). Edit this file
in place: replace each `[ ]` with `[grounded]` or `[not grounded]`.

A claim is GROUNDED only if the context directly supports it - not if it
sounds plausible or matches general personal-finance knowledge.

(6 of 18 judged questions - a representative subset
chosen for tractability, not all of them. See docs/DECISIONS.md.)

## vec-001
**Question:** What is the 50/30/20 budgeting rule?

<details><summary>Context (click to expand)</summary>

```
[budgeting-50-30-20] The 50/30/20 rule
The 50/30/20 rule is a simple way to split take-home (post-tax) income into
three buckets:

- **50% needs** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, and anything else you'd struggle to live
  without in the short term.
- **30% wants** — dining out, entertainment, subscriptions, travel, shopping
  beyond necessities. Discretionary by definition: cutting these doesn't
  threaten your basic stability.
- **20% savings and debt paydown** — building an emergency fund, investing
  toward goals, and paying down debt faster than the required minimum.

It's a starting heuristic, not a law. Someone in a high cost-of-living city
may find needs run closer to 60-65%, and someone with no dependents and low
fixed costs might comfortably push savings well past 20%. The value of the
framework is less the exact split and more that it forces every rupee of
income into one of three explicit buckets, which makes it obvious when
"wants" has quietly swallowed room that should belong to "savings."

[essential-vs-discretionary] Essential vs. discretionary spending
For the purposes of affordability and emergency-fund sizing, spending splits
into two categories:

- **Essential** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, medicine, and transport needed to get to
  work. Cutting these has an immediate, direct cost to stability.
- **Discretionary** — dining out, food delivery, entertainment,
  subscriptions, shopping beyond replacement needs, travel. These can be
  reduced quickly in a downturn without an immediate crisis.

The line isn't always clean — a subscription might be a genuine essential
for someone's work, and "groceries" can include a fair amount of
discretionary premium spending. A reasonable default is to treat a spending
category as essential only if stopping it within a month would create a
real problem (losing housing, utilities being cut off, missing debt
payments), and discretionary otherwise. When drawing this line for a real
person's transactions, the specific categorisation used should be stated
explicitly rather than left implicit, since it changes the answer.

[foir-affordability] Home loan affordability (FOIR)
Lenders commonly use FOIR (Fixed Obligation to Income Ratio) to decide how
large a loan someone can take on: it's total fixed monthly obligations
(all existing EMIs, plus the proposed new EMI) divided by gross monthly
income. Lenders typically cap FOIR somewhere in the **40-50% range**,
though the exact cap varies by lender and by the borrower's income level.

Working backward from a target loan amount to "can I afford this" requires
assumptions — the interest rate and tenure that will actually apply, which
directly determine the EMI (see EMI calculation) and therefore the FOIR.
Because those assumptions are estimates until a lender actually underwrites
the loan, any affordability answer should be framed as **indicative**, not
as a guarantee of loan approval — actual eligibility also depends on
credit score, employment type, and lender-specific policy that a rule of
thumb can't capture.

[emergency-fund-framework] How big should an emergency fund be
The standard rule of thumb is **3 to 6 months of essential expenses** held in
something safe and immediately accessible — a savings account, a sweep-in
fixed deposit, or a liquid mutual fund — not equity, and not locked away in
something with an exit penalty.

Where you land in that range depends on:

- **Job stability.** A salaried role at a large, stable employer leans
  toward 3 months. Freelance or commission-based income, or a role in a
  volatile industry, pushes toward 6 months or more.
- **Dependents.** Supporting parents, children, or a non-earning spouse
  raises the bar — there's more than one income's worth of risk to cover.
- **Other safety nets.** Family who could lend money quickly, or a spouse
  with independent stable income, can justify sitting lower in the range.

The fund is sized against *essential* expenses, not total spending — see
essential vs. discretionary spending below. Sizing it against total spending
overstates what's actually needed to survive an income gap.

[healthy-debt-to-income] What counts as a healthy debt-to-income ratio
As a rule of thumb:

- **Under 20%** is generally considered comfortable — debt is a minor claim
  on income.
- **20-36%** is manageable for most people but leaves less room to absorb an
  income shock or take on a large new loan (like a home loan) without
  strain.
- **Above 36-40%** is the range where lenders start getting cautious, and
  where a single missed paycheck or emergency expense can cascade into
  missed payments.

These are guidelines, not hard cutoffs — someone with a large, stable income
and strong savings can carry a higher ratio comfortably, while someone with
irregular income should target lower than the rule of thumb suggests. The
ratio only counts payments that actually appear as outflows; it can't see
debt that isn't visible in transaction data.
```
</details>

**Full answer:** The 50/30/20 budgeting rule is a framework that suggests splitting post-tax income into three buckets: 50% for needs, 30% for wants, and 20% for savings and debt paydown. However, some may find that needs run closer to 60-65% in a high-cost-of-living city, while others may comfortably push savings well past 20%. This framework forces every rupee of income into one of three explicit buckets.

1. [ ] The 50/30/20 budgeting rule is a framework that suggests splitting post-tax income into three buckets
2. [ ] The three buckets are 50% for needs, 30% for wants, and 20% for savings and debt paydown
3. [ ] Some may find that needs run closer to 60-65% in a high-cost-of-living city
4. [ ] Others may comfortably push savings well past 20%
5. [ ] This framework forces every rupee of income into one of three explicit buckets

## vec-002
**Question:** How much life insurance coverage do I actually need?

<details><summary>Context (click to expand)</summary>

```
[insurance-adequacy] Is your insurance coverage adequate
"Adequate" insurance is best thought of per risk rather than as one number:
life cover should replace lost income for dependents, health cover should
absorb a plausible worst-case medical bill without derailing other goals,
and neither should be judged by the premium being "affordable" alone, since
a cheap policy that pays out too little on a real claim isn't actually
providing protection.

A useful gut check across any policy: what specific bad scenario is this
meant to cover, and does the payout actually cover it at today's costs (not
the costs from when the policy was bought)? Health cover in particular
tends to be under-bought relative to real hospitalisation costs, which rise
faster than general inflation.

[term-insurance-coverage] How much life insurance coverage is needed
The standard rule of thumb for term life insurance is coverage of roughly
**10 to 15 times annual income**, adjusted by:

- **Dependents** — more dependents, or younger dependents with a longer
  runway of expenses ahead of them, push the multiple higher.
- **Existing debt** — outstanding loans (especially a home loan) that
  shouldn't become a burden on survivors add directly to the coverage
  needed, since the payout should be able to clear them.
- **Existing assets and savings** — significant savings, investments, or
  other insurance already in place reduce how much new coverage is needed,
  since those assets already provide some of the same protection.

The multiple is a starting point for a conversation, not a precise
calculation — the more defensible version is: sum up what dependents would
actually need (years of expenses, outstanding debt, future goals like
education) and subtract what's already covered by existing assets and
policies. Term insurance (pure protection, no savings component) is
generally the most cost-effective way to buy a given amount of coverage
compared to policies that bundle in an investment component.

[emergency-fund-framework] How big should an emergency fund be
The standard rule of thumb is **3 to 6 months of essential expenses** held in
something safe and immediately accessible — a savings account, a sweep-in
fixed deposit, or a liquid mutual fund — not equity, and not locked away in
something with an exit penalty.

Where you land in that range depends on:

- **Job stability.** A salaried role at a large, stable employer leans
  toward 3 months. Freelance or commission-based income, or a role in a
  volatile industry, pushes toward 6 months or more.
- **Dependents.** Supporting parents, children, or a non-earning spouse
  raises the bar — there's more than one income's worth of risk to cover.
- **Other safety nets.** Family who could lend money quickly, or a spouse
  with independent stable income, can justify sitting lower in the range.

The fund is sized against *essential* expenses, not total spending — see
essential vs. discretionary spending below. Sizing it against total spending
overstates what's actually needed to survive an income gap.

[budgeting-50-30-20] The 50/30/20 rule
The 50/30/20 rule is a simple way to split take-home (post-tax) income into
three buckets:

- **50% needs** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, and anything else you'd struggle to live
  without in the short term.
- **30% wants** — dining out, entertainment, subscriptions, travel, shopping
  beyond necessities. Discretionary by definition: cutting these doesn't
  threaten your basic stability.
- **20% savings and debt paydown** — building an emergency fund, investing
  toward goals, and paying down debt faster than the required minimum.

It's a starting heuristic, not a law. Someone in a high cost-of-living city
may find needs run closer to 60-65%, and someone with no dependents and low
fixed costs might comfortably push savings well past 20%. The value of the
framework is less the exact split and more that it forces every rupee of
income into one of three explicit buckets, which makes it obvious when
"wants" has quietly swallowed room that should belong to "savings."

[essential-vs-discretionary] Essential vs. discretionary spending
For the purposes of affordability and emergency-fund sizing, spending splits
into two categories:

- **Essential** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, medicine, and transport needed to get to
  work. Cutting these has an immediate, direct cost to stability.
- **Discretionary** — dining out, food delivery, entertainment,
  subscriptions, shopping beyond replacement needs, travel. These can be
  reduced quickly in a downturn without an immediate crisis.

The line isn't always clean — a subscription might be a genuine essential
for someone's work, and "groceries" can include a fair amount of
discretionary premium spending. A reasonable default is to treat a spending
category as essential only if stopping it within a month would create a
real problem (losing housing, utilities being cut off, missing debt
payments), and discretionary otherwise. When drawing this line for a real
person's transactions, the specific categorisation used should be stated
explicitly rather than left implicit, since it changes the answer.
```
</details>

**Full answer:** To determine how much life insurance coverage you need, you should consider factors such as dependents, existing debt, and existing assets to calculate the sum of what dependents would actually need (years of expenses, outstanding debt, future goals like education) and subtract what's already covered by existing assets and policies. A general starting point is 10 to 15 times annual income, but this is not a precise calculation [term-insurance-coverage].

It's helpful to consider the specific bad scenario the insurance is meant to cover and ensure the payout can actually cover it at today's costs [insurance-adequacy]. The more dependents you have, especially younger dependents, the more coverage you may need. If you have significant existing assets and savings, you may need less coverage.

You should compare life insurance with other essential expenses under the 50/30/20 rule, where 50% of your income goes toward needs, 30% toward wants, and 20% toward savings and debt paydown [budgeting-50-30-20]. You can also assess your essential expenses and see if there's any room for reduction in non-essential expenses like dining out and entertainment [essential-vs-discretionary].

1. [ ] To determine how much life insurance coverage you need, you should consider factors such as dependents, existing debt, and existing assets to calculate the sum of what dependents would actually need (years of expenses, outstanding debt, future goals like education) and subtract what's already covered by existing assets and policies.
2. [ ] A general starting point is 10 to 15 times annual income, but this is not a precise calculation.
3. [ ] It's helpful to consider the specific bad scenario the insurance is meant to cover and ensure the payout can actually cover it at today's costs.
4. [ ] The more dependents you have, especially younger dependents, the more coverage you may need.
5. [ ] If you have significant existing assets and savings, you may need less coverage.
6. [ ] You should compare life insurance with other essential expenses under the 50/30/20 rule, where 50% of your income goes toward needs, 50% toward wants, and 20% toward savings and debt paydown.
7. [ ] You can also assess your essential expenses and see if there's any room for reduction in non-essential expenses like dining out and entertainment.

## vec-005
**Question:** Is it better to rent or buy a home?

<details><summary>Context (click to expand)</summary>

```
[rent-vs-buy] Renting vs. buying a home
This is genuinely a trade-off, not a question with a universally correct
answer, and it depends on several factors specific to the person and the
local market:

- **Time horizon.** Buying carries large upfront transaction costs (down
  payment, registration, brokerage) that only get "paid back" through
  years of not having to move. A short expected time in one city or home
  favours renting; a long, settled horizon favours buying.
- **Opportunity cost of the down payment.** A home down payment is often a
  household's largest single investment. That same money, invested instead,
  would compound over time — a full comparison has to weigh the home's
  price appreciation and the value of not paying rent against what the down
  payment could have earned invested elsewhere.
- **Local price-to-rent ratio.** In markets where purchase prices are high
  relative to achievable rent, renting and investing the difference can
  come out ahead financially; in markets where rent is high relative to
  purchase prices, buying tends to look better. This ratio varies a lot by
  city and even by neighbourhood.
- **Non-financial factors.** Stability, control over the property, and
  flexibility to relocate for work or family reasons are real
  considerations that don't show up in a spreadsheet, and reasonably
  outweigh the purely financial comparison for many people.

Because of how much these factors vary by individual situation and local
market, a responsible answer states the trade-off and what it depends on,
rather than asserting rent or buy is definitively better.

[budgeting-50-30-20] The 50/30/20 rule
The 50/30/20 rule is a simple way to split take-home (post-tax) income into
three buckets:

- **50% needs** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, and anything else you'd struggle to live
  without in the short term.
- **30% wants** — dining out, entertainment, subscriptions, travel, shopping
  beyond necessities. Discretionary by definition: cutting these doesn't
  threaten your basic stability.
- **20% savings and debt paydown** — building an emergency fund, investing
  toward goals, and paying down debt faster than the required minimum.

It's a starting heuristic, not a law. Someone in a high cost-of-living city
may find needs run closer to 60-65%, and someone with no dependents and low
fixed costs might comfortably push savings well past 20%. The value of the
framework is less the exact split and more that it forces every rupee of
income into one of three explicit buckets, which makes it obvious when
"wants" has quietly swallowed room that should belong to "savings."

[essential-vs-discretionary] Essential vs. discretionary spending
For the purposes of affordability and emergency-fund sizing, spending splits
into two categories:

- **Essential** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, medicine, and transport needed to get to
  work. Cutting these has an immediate, direct cost to stability.
- **Discretionary** — dining out, food delivery, entertainment,
  subscriptions, shopping beyond replacement needs, travel. These can be
  reduced quickly in a downturn without an immediate crisis.

The line isn't always clean — a subscription might be a genuine essential
for someone's work, and "groceries" can include a fair amount of
discretionary premium spending. A reasonable default is to treat a spending
category as essential only if stopping it within a month would create a
real problem (losing housing, utilities being cut off, missing debt
payments), and discretionary otherwise. When drawing this line for a real
person's transactions, the specific categorisation used should be stated
explicitly rather than left implicit, since it changes the answer.

[term-insurance-coverage] How much life insurance coverage is needed
The standard rule of thumb for term life insurance is coverage of roughly
**10 to 15 times annual income**, adjusted by:

- **Dependents** — more dependents, or younger dependents with a longer
  runway of expenses ahead of them, push the multiple higher.
- **Existing debt** — outstanding loans (especially a home loan) that
  shouldn't become a burden on survivors add directly to the coverage
  needed, since the payout should be able to clear them.
- **Existing assets and savings** — significant savings, investments, or
  other insurance already in place reduce how much new coverage is needed,
  since those assets already provide some of the same protection.

The multiple is a starting point for a conversation, not a precise
calculation — the more defensible version is: sum up what dependents would
actually need (years of expenses, outstanding debt, future goals like
education) and subtract what's already covered by existing assets and
policies. Term insurance (pure protection, no savings component) is
generally the most cost-effective way to buy a given amount of coverage
compared to policies that bundle in an investment component.

[healthy-debt-to-income] What counts as a healthy debt-to-income ratio
As a rule of thumb:

- **Under 20%** is generally considered comfortable — debt is a minor claim
  on income.
- **20-36%** is manageable for most people but leaves less room to absorb an
  income shock or take on a large new loan (like a home loan) without
  strain.
- **Above 36-40%** is the range where lenders start getting cautious, and
  where a single missed paycheck or emergency expense can cascade into
  missed payments.

These are guidelines, not hard cutoffs — someone with a large, stable income
and strong savings can carry a higher ratio comfortably, while someone with
irregular income should target lower than the rule of thumb suggests. The
ratio only counts payments that actually appear as outflows; it can't see
debt that isn't visible in transaction data.
```
</details>

**Full answer:** The decision to rent or buy a home involves key trade-offs based on your personal situation and local market conditions:

1. **Time horizon**: Buying requires significant upfront costs (down payment, fees) that only make sense if you plan to stay in the home for many years. If you expect to move or relocate soon, renting avoids these costs and allows flexibility [rent-vs-buy].

2. **Opportunity cost of the down payment**: The money tied up in a down payment could instead be invested, potentially growing over time. A financial comparison must weigh the home’s future appreciation and the savings from not paying rent against what the down payment could earn elsewhere [rent-vs-buy].

3. **Local price-to-rent ratio**: In some markets, renting and investing the difference (e.g., the rent savings) might outperform buying financially. In others, where purchase prices are lower relative to rent, buying could be more advantageous. This varies widely by city and neighborhood [rent-vs-buy].

4. **Non-financial factors**: Stability, control over the property, and flexibility to relocate are important considerations that don’t appear in financial calculations. For many people, these factors may outweigh purely financial trade-offs [rent-vs-buy].

No single answer applies universally—your choice depends on balancing these factors with your priorities.

1. [ ] Buying requires significant upfront costs (down payment, fees) that only make sense if you plan to stay in the home for many years.
2. [ ] If you expect to move or relocate soon, renting avoids these costs and allows flexibility.
3. [ ] The money tied up in a down payment could instead be invested, potentially growing over time.
4. [ ] A financial comparison must weigh the home’s future appreciation and the savings from not paying rent against what the down payment could earn elsewhere.
5. [ ] In some markets, renting and investing the difference (e.g., the rent savings) might outperform buying financially.
6. [ ] In other markets, where purchase prices are lower relative to rent, buying could be more advantageous.
7. [ ] This (price-to-rent ratio) varies widely by city and neighborhood.
8. [ ] Stability, control over the property, and flexibility to relocate are important considerations that don’t appear in financial calculations.
9. [ ] For many people, these (non-financial) factors may outweigh purely financial trade-offs.
10. [ ] No single answer applies universally—your choice depends on balancing these factors with your priorities.

## hyb-001
**Question:** Should I prepay my home loan or invest the surplus?

<details><summary>Context (click to expand)</summary>

```
User's actual data:
I couldn't identify a specific category or place from your question, and I don't have location data to work from - could you name the category or merchant?

Knowledge corpus context:
[prepay-vs-invest] Prepaying a loan vs. investing the surplus
When someone has surplus money and an existing loan, the classic framework
is to compare the loan's interest rate against the expected return of
investing instead:

- Prepaying a loan delivers a **guaranteed, risk-free return equal to the
  loan's interest rate** — every rupee of prepayment saves exactly that
  much interest, no market risk involved.
- Investing the surplus (e.g. in equity) offers a **higher expected return
  over the long run, but it isn't guaranteed** — see expected equity
  returns below for the reasoning behind that number, and its uncertainty.

The trade-off usually comes down to: if the loan's interest rate is high
(unsecured personal loans, most credit card debt), prepayment tends to win
because the guaranteed saving is hard to beat. If the loan's rate is low
(some subsidised or long-tenure secured loans) and the person has a long
investment horizon and the risk tolerance for it, investing the surplus can
plausibly come out ahead — but "plausibly" and "guaranteed" are doing very
different work in those two sentences, and that distinction should always
be part of the answer, not a footnote.

[healthy-debt-to-income] What counts as a healthy debt-to-income ratio
As a rule of thumb:

- **Under 20%** is generally considered comfortable — debt is a minor claim
  on income.
- **20-36%** is manageable for most people but leaves less room to absorb an
  income shock or take on a large new loan (like a home loan) without
  strain.
- **Above 36-40%** is the range where lenders start getting cautious, and
  where a single missed paycheck or emergency expense can cascade into
  missed payments.

These are guidelines, not hard cutoffs — someone with a large, stable income
and strong savings can carry a higher ratio comfortably, while someone with
irregular income should target lower than the rule of thumb suggests. The
ratio only counts payments that actually appear as outflows; it can't see
debt that isn't visible in transaction data.

[parking-short-term-funds] Where to park money needed in the near term
Money that will be needed within roughly the next 6-12 months — an
upcoming expense, a down payment, savings toward a near-term goal —
generally shouldn't sit in equity — a market downturn right before the
money is needed could force selling at a loss. Better options for this
kind of near-term money:

- **Savings account / sweep-in FD** — fully liquid, principal-safe, modest
  return.
- **Short-term fixed deposits** — principal-safe, slightly better return
  than a savings account, but breaking one early may cost a small penalty.
- **Liquid or short-duration mutual funds** — generally more liquid than a
  fixed deposit and historically more stable than equity, though (unlike a
  bank deposit) they aren't principal-guaranteed.

The trade-off across all of these is the same shape: safety and easy access
in exchange for giving up the higher, but uncertain and less liquid,
returns that longer-horizon investments like equity can offer.

[budgeting-50-30-20] The 50/30/20 rule
The 50/30/20 rule is a simple way to split take-home (post-tax) income into
three buckets:

- **50% needs** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, and anything else you'd struggle to live
  without in the short term.
- **30% wants** — dining out, entertainment, subscriptions, travel, shopping
  beyond necessities. Discretionary by definition: cutting these doesn't
  threaten your basic stability.
- **20% savings and debt paydown** — building an emergency fund, investing
  toward goals, and paying down debt faster than the required minimum.

It's a starting heuristic, not a law. Someone in a high cost-of-living city
may find needs run closer to 60-65%, and someone with no dependents and low
fixed costs might comfortably push savings well past 20%. The value of the
framework is less the exact split and more that it forces every rupee of
income into one of three explicit buckets, which makes it obvious when
"wants" has quietly swallowed room that should belong to "savings."

[foir-affordability] Home loan affordability (FOIR)
Lenders commonly use FOIR (Fixed Obligation to Income Ratio) to decide how
large a loan someone can take on: it's total fixed monthly obligations
(all existing EMIs, plus the proposed new EMI) divided by gross monthly
income. Lenders typically cap FOIR somewhere in the **40-50% range**,
though the exact cap varies by lender and by the borrower's income level.

Working backward from a target loan amount to "can I afford this" requires
assumptions — the interest rate and tenure that will actually apply, which
directly determine the EMI (see EMI calculation) and therefore the FOIR.
Because those assumptions are estimates until a lender actually underwrites
the loan, any affordability answer should be framed as **indicative**, not
as a guarantee of loan approval — actual eligibility also depends on
credit score, employment type, and lender-specific policy that a rule of
thumb can't capture.
```
</details>

**Full answer:** To help you decide whether to prepay your home loan or invest the surplus, let's consider the context provided [prepay-vs-invest]. 

Prepaying your home loan offers a **guaranteed, risk-free return equal to the loan's interest rate**, saving you that much interest every time you prepay. On the other hand, investing the surplus in equity offers a **higher expected return over the long run, but it isn't guaranteed**. 

If your loan's interest rate is high (e.g., unsecured personal loans, most credit card debt), prepayment tends to win because the guaranteed saving is hard to beat. However, if your loan's rate is low (e.g., some subsidised or long-tenure secured loans) and you have a long investment horizon and the risk tolerance for it, investing the surplus can plausibly come out ahead.

Consider your loan's interest rate and your overall financial situation before making a decision.

1. [ ] "Prepaying your home loan offers a **guaranteed, risk-free return equal to the loan's interest rate**, saving you that much interest every time you prepay."
2. [ ] "On the other hand, investing the surplus in equity offers a **higher expected return over the long run, but it isn't guaranteed**."
3. [ ] "If your loan's interest rate is high (e.g., unsecured personal loans, most credit card debt), prepayment tends to win because the guaranteed saving is hard to beat."
4. [ ] "However, if your loan's rate is low (e.g., some subsidised or long-tenure secured loans) and you have a long investment horizon and the risk tolerance for it, investing the surplus can plausibly come out ahead."

## hyb-006
**Question:** How much am I actually saving each month?

<details><summary>Context (click to expand)</summary>

```
User's actual data:
I couldn't identify a specific category or place from your question, and I don't have location data to work from - could you name the category or merchant?

Knowledge corpus context:
[savings-rate-definition] What counts as savings
Savings rate is typically defined as (income minus expenses) divided by
income — the share of what comes in that isn't spent. Two distinctions
matter for computing this correctly from real transaction data:

- **Saving vs. investing.** Money sitting in a savings account and money
  put into a SIP or mutual fund are both "not spent," but they're not the
  same thing — investing carries market risk that plain savings doesn't.
  A complete answer about "how much am I saving" is more useful when it
  separates the two rather than lumping them into one figure.
- **Transfers are not savings.** Moving money between your own accounts —
  a transfer from a savings account to a separate account used for
  investing, or between a joint and individual account — is not income
  being saved; it's the same money changing location. Counting inter-account
  transfers as new savings (or, on the other side, as new spending)
  double-counts money that never actually left the household, and inflates
  both figures. Getting a savings rate right depends on correctly
  identifying and excluding these transfers, not just summing every credit
  and debit.

[emergency-fund-framework] How big should an emergency fund be
The standard rule of thumb is **3 to 6 months of essential expenses** held in
something safe and immediately accessible — a savings account, a sweep-in
fixed deposit, or a liquid mutual fund — not equity, and not locked away in
something with an exit penalty.

Where you land in that range depends on:

- **Job stability.** A salaried role at a large, stable employer leans
  toward 3 months. Freelance or commission-based income, or a role in a
  volatile industry, pushes toward 6 months or more.
- **Dependents.** Supporting parents, children, or a non-earning spouse
  raises the bar — there's more than one income's worth of risk to cover.
- **Other safety nets.** Family who could lend money quickly, or a spouse
  with independent stable income, can justify sitting lower in the range.

The fund is sized against *essential* expenses, not total spending — see
essential vs. discretionary spending below. Sizing it against total spending
overstates what's actually needed to survive an income gap.

[essential-vs-discretionary] Essential vs. discretionary spending
For the purposes of affordability and emergency-fund sizing, spending splits
into two categories:

- **Essential** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, medicine, and transport needed to get to
  work. Cutting these has an immediate, direct cost to stability.
- **Discretionary** — dining out, food delivery, entertainment,
  subscriptions, shopping beyond replacement needs, travel. These can be
  reduced quickly in a downturn without an immediate crisis.

The line isn't always clean — a subscription might be a genuine essential
for someone's work, and "groceries" can include a fair amount of
discretionary premium spending. A reasonable default is to treat a spending
category as essential only if stopping it within a month would create a
real problem (losing housing, utilities being cut off, missing debt
payments), and discretionary otherwise. When drawing this line for a real
person's transactions, the specific categorisation used should be stated
explicitly rather than left implicit, since it changes the answer.

[budgeting-50-30-20] The 50/30/20 rule
The 50/30/20 rule is a simple way to split take-home (post-tax) income into
three buckets:

- **50% needs** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, and anything else you'd struggle to live
  without in the short term.
- **30% wants** — dining out, entertainment, subscriptions, travel, shopping
  beyond necessities. Discretionary by definition: cutting these doesn't
  threaten your basic stability.
- **20% savings and debt paydown** — building an emergency fund, investing
  toward goals, and paying down debt faster than the required minimum.

It's a starting heuristic, not a law. Someone in a high cost-of-living city
may find needs run closer to 60-65%, and someone with no dependents and low
fixed costs might comfortably push savings well past 20%. The value of the
framework is less the exact split and more that it forces every rupee of
income into one of three explicit buckets, which makes it obvious when
"wants" has quietly swallowed room that should belong to "savings."

[term-insurance-coverage] How much life insurance coverage is needed
The standard rule of thumb for term life insurance is coverage of roughly
**10 to 15 times annual income**, adjusted by:

- **Dependents** — more dependents, or younger dependents with a longer
  runway of expenses ahead of them, push the multiple higher.
- **Existing debt** — outstanding loans (especially a home loan) that
  shouldn't become a burden on survivors add directly to the coverage
  needed, since the payout should be able to clear them.
- **Existing assets and savings** — significant savings, investments, or
  other insurance already in place reduce how much new coverage is needed,
  since those assets already provide some of the same protection.

The multiple is a starting point for a conversation, not a precise
calculation — the more defensible version is: sum up what dependents would
actually need (years of expenses, outstanding debt, future goals like
education) and subtract what's already covered by existing assets and
policies. Term insurance (pure protection, no savings component) is
generally the most cost-effective way to buy a given amount of coverage
compared to policies that bundle in an investment component.
```
</details>

**Full answer:** Based on the provided context, here’s how you might approach calculating your **monthly savings** while accounting for trade-offs:

1. **Separate savings from investing**
   - If you’re tracking money moved into a savings account *and* investments (e.g., SIPs or mutual funds), these are distinct categories. Savings (e.g., liquid funds, fixed deposits) are safer but less growth-oriented, while investing carries market risk but can grow faster. The context suggests lumping them together could misrepresent your true savings rate [savings-rate-definition].

2. **Exclude inter-account transfers**
   - Moving money between your own accounts (e.g., from savings to a separate investment account) doesn’t count as new savings. It’s the same money changing locations, so counting it as savings would inflate your rate. Focus on **new income minus expenses**—not just reallocations [savings-rate-definition].

3. **Define "savings" as residual income**
   - Your savings rate = (income – expenses) / income. To compute this accurately, you’d need to:
     - **Sum all income** (salary, freelance, etc.).
     - **Subtract all expenses** (essential *and* discretionary).
     - **Exclude transfers** between your own accounts.
   - Without explicit transaction data, you can’t calculate an exact number, but the framework implies you’d need to categorize spending first [savings-rate-definition, essential-vs-discretionary].

4. **Trade-offs in categorization**
   - If you include discretionary spending (e.g., dining out, subscriptions) as part of "expenses," your savings rate will appear lower. Conversely, if you exclude some discretionary costs (e.g., treating a work-related subscription as essential), your savings rate could seem higher—but this might understate flexibility in a downturn [essential-vs-discretion

1. [ ] "If you’re tracking money moved into a savings account *and* investments (e.g., SIPs or mutual funds), these are distinct categories."
2. [ ] "Savings (e.g., liquid funds, fixed deposits) are safer but less growth-oriented, while investing carries market risk but can grow faster."
3. [ ] "Lumping them together could misrepresent your true savings rate."
4. [ ] "Moving money between your own accounts (e.g., from savings to a separate investment account) doesn’t count as new savings."
5. [ ] "Counting it as savings would inflate your rate."
6. [ ] "Focus on **new income minus expenses**—not just reallocations."
7. [ ] "Your savings rate = (income – expenses) / income."
8. [ ] "To compute this accurately, you’d need to sum all income (salary, freelance, etc.)."
9. [ ] "You’d need to subtract all expenses (essential *and* discretionary)."
10. [ ] "You’d need to exclude transfers between your own accounts."
11. [ ] "Without explicit transaction data, you can’t calculate an exact number, but the framework implies you’d need to categorize spending first."
12. [ ] "If you include discretionary spending (e.g., dining out, subscriptions) as part of 'expenses,' your savings rate will appear lower."
13. [ ] "If you exclude some discretionary costs (e.g., treating a work-related subscription as essential), your savings rate could seem higher—but this might understate flexibility in a downturn."

## hyb-007
**Question:** Can I afford a 50 lakh home loan?

<details><summary>Context (click to expand)</summary>

```
User's actual data:
I couldn't identify a specific category or place from your question, and I don't have location data to work from - could you name the category or merchant?

Knowledge corpus context:
[foir-affordability] Home loan affordability (FOIR)
Lenders commonly use FOIR (Fixed Obligation to Income Ratio) to decide how
large a loan someone can take on: it's total fixed monthly obligations
(all existing EMIs, plus the proposed new EMI) divided by gross monthly
income. Lenders typically cap FOIR somewhere in the **40-50% range**,
though the exact cap varies by lender and by the borrower's income level.

Working backward from a target loan amount to "can I afford this" requires
assumptions — the interest rate and tenure that will actually apply, which
directly determine the EMI (see EMI calculation) and therefore the FOIR.
Because those assumptions are estimates until a lender actually underwrites
the loan, any affordability answer should be framed as **indicative**, not
as a guarantee of loan approval — actual eligibility also depends on
credit score, employment type, and lender-specific policy that a rule of
thumb can't capture.

[budgeting-50-30-20] The 50/30/20 rule
The 50/30/20 rule is a simple way to split take-home (post-tax) income into
three buckets:

- **50% needs** — rent or home loan EMI, groceries, utilities, insurance
  premiums, minimum debt payments, and anything else you'd struggle to live
  without in the short term.
- **30% wants** — dining out, entertainment, subscriptions, travel, shopping
  beyond necessities. Discretionary by definition: cutting these doesn't
  threaten your basic stability.
- **20% savings and debt paydown** — building an emergency fund, investing
  toward goals, and paying down debt faster than the required minimum.

It's a starting heuristic, not a law. Someone in a high cost-of-living city
may find needs run closer to 60-65%, and someone with no dependents and low
fixed costs might comfortably push savings well past 20%. The value of the
framework is less the exact split and more that it forces every rupee of
income into one of three explicit buckets, which makes it obvious when
"wants" has quietly swallowed room that should belong to "savings."

[healthy-debt-to-income] What counts as a healthy debt-to-income ratio
As a rule of thumb:

- **Under 20%** is generally considered comfortable — debt is a minor claim
  on income.
- **20-36%** is manageable for most people but leaves less room to absorb an
  income shock or take on a large new loan (like a home loan) without
  strain.
- **Above 36-40%** is the range where lenders start getting cautious, and
  where a single missed paycheck or emergency expense can cascade into
  missed payments.

These are guidelines, not hard cutoffs — someone with a large, stable income
and strong savings can carry a higher ratio comfortably, while someone with
irregular income should target lower than the rule of thumb suggests. The
ratio only counts payments that actually appear as outflows; it can't see
debt that isn't visible in transaction data.

[rent-vs-buy] Renting vs. buying a home
This is genuinely a trade-off, not a question with a universally correct
answer, and it depends on several factors specific to the person and the
local market:

- **Time horizon.** Buying carries large upfront transaction costs (down
  payment, registration, brokerage) that only get "paid back" through
  years of not having to move. A short expected time in one city or home
  favours renting; a long, settled horizon favours buying.
- **Opportunity cost of the down payment.** A home down payment is often a
  household's largest single investment. That same money, invested instead,
  would compound over time — a full comparison has to weigh the home's
  price appreciation and the value of not paying rent against what the down
  payment could have earned invested elsewhere.
- **Local price-to-rent ratio.** In markets where purchase prices are high
  relative to achievable rent, renting and investing the difference can
  come out ahead financially; in markets where rent is high relative to
  purchase prices, buying tends to look better. This ratio varies a lot by
  city and even by neighbourhood.
- **Non-financial factors.** Stability, control over the property, and
  flexibility to relocate for work or family reasons are real
  considerations that don't show up in a spreadsheet, and reasonably
  outweigh the purely financial comparison for many people.

Because of how much these factors vary by individual situation and local
market, a responsible answer states the trade-off and what it depends on,
rather than asserting rent or buy is definitively better.

[prepay-vs-invest] Prepaying a loan vs. investing the surplus
When someone has surplus money and an existing loan, the classic framework
is to compare the loan's interest rate against the expected return of
investing instead:

- Prepaying a loan delivers a **guaranteed, risk-free return equal to the
  loan's interest rate** — every rupee of prepayment saves exactly that
  much interest, no market risk involved.
- Investing the surplus (e.g. in equity) offers a **higher expected return
  over the long run, but it isn't guaranteed** — see expected equity
  returns below for the reasoning behind that number, and its uncertainty.

The trade-off usually comes down to: if the loan's interest rate is high
(unsecured personal loans, most credit card debt), prepayment tends to win
because the guaranteed saving is hard to beat. If the loan's rate is low
(some subsidised or long-tenure secured loans) and the person has a long
investment horizon and the risk tolerance for it, investing the surplus can
plausibly come out ahead — but "plausibly" and "guaranteed" are doing very
different work in those two sentences, and that distinction should always
be part of the answer, not a footnote.
```
</details>

**Full answer:** Based on the provided context, here’s how the trade-offs around a **50 lakh home loan** might apply to your situation:

1. **FOIR (Fixed Obligation to Income Ratio) Consideration**
   - Lenders typically cap FOIR at **40–50%** of your gross monthly income. To assess affordability, you’d need to estimate the EMI for a 50 lakh loan (which depends on the interest rate and tenure) and compare it to your existing fixed obligations (e.g., other EMIs, utilities, insurance). Since the exact EMI isn’t provided, this is an **indicative** check rather than a guarantee [foir-affordability].
   - If your current FOIR is already near the upper limit (e.g., 40–50%), adding a new EMI could strain your budget, especially if you lack flexibility in other expenses.

2. **Debt-to-Income Ratio (DTI) Impact**
   - A home loan EMI would increase your DTI. If your current DTI is **above 36–40%**, lenders may view this as risky, and a missed payment (e.g., due to an emergency) could worsen financial strain [healthy-debt-to-income].
   - If your DTI is **under 20%**, you’d have more room to absorb the new loan without significant disruption.

3. **Budgeting Trade-offs (50/30/20 Rule)**
   - The home loan EMI would likely fall under **"needs"** (50% of take-home income). If your current "needs" already consume 50%, the loan could push you toward the **60–65% range** for high-cost areas, reducing flexibility in "wants" (e.g., travel, entertainment) or "savings" (e.g., emergency funds) [budgeting-50-

1. [ ] Lenders typically cap FOIR at **40–50%** of your gross monthly income.
2. [ ] To assess affordability, you’d need to estimate the EMI for a 50 lakh loan (which depends on the interest rate and tenure) and compare it to your existing fixed obligations.
3. [ ] This is an **indicative** check rather than a guarantee.
4. [ ] If your current FOIR is already near the upper limit (e.g., 40–50%), adding a new EMI could strain your budget, especially if you lack flexibility in other expenses.
5. [ ] A home loan EMI would increase your DTI.
6. [ ] If your current DTI is **above 36–40%**, lenders may view this as risky.
7. [ ] If your current DTI is **under 20%**, you’d have more room to absorb the new loan without significant disruption.
8. [ ] The home loan EMI would likely fall under **"needs"** (50% of take-home income).
9. [ ] If your current "needs" already consume 50%, the loan could push you toward the **60–65% range** for high-cost areas.
