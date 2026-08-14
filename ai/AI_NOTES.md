# AI_NOTES

This note describes, in my own words, how I used an AI coding agent during Part B
and how I checked its work. The full record of prompts and outputs is in
`ai/prompt_log.md`.

## How I directed the AI
I worked one task at a time. For each part of the app or the analysis I wrote a
specific prompt that stated the goal, the constraints, and how to check the result,
then I ran it, read the output, and either accepted it or sent a correction. I did
not let the agent run open ended. I directed it this way to build the nine fund grid
(three universes by three methods), the Streamlit pages, the figures, the sentiment
index, and the drafts of the report.

## Where the AI helped
The AI was fastest at scaffolding. It set up the walk forward backtest, the fact
sheet and comparison pages, the Monte Carlo simulator, and first drafts of the
figures and the writing. That saved time on boilerplate and let me focus on whether
the results were correct and whether the app was clear for a beginner.

## Where it was wrong, and what I did about it
A few catches mattered.
- The efficient frontier optimiser silently returned equal weights near the top of
  the curve, which drew a fake dip in the volatility. I noticed the frontier was not
  smooth and had the solver changed so it came out correct.
- The sentiment gauge read very positive almost all the time. I worked out that VADER
  has a positive baseline, so I directed the AI to standardise each sector against its
  own history with a z score. After that the gauge reads about normal, which is honest.
- The Monte Carlo chart looked too optimistic because the smooth median hid the
  downside. I had it redrawn as four labelled lines, best, likely, worst, and what you
  put in, so a possible loss shows as clearly as a gain.
- After the sentiment change added new columns to a data file, one chart broke. I
  traced it to the app reading those extra columns and had them filtered out.
- The first deployment failed because the requirements file was missing plotly. I
  added it and deployed again.

## How I checked the work
I ran the app locally and on the live deployment and clicked through every page. I ran
`scripts/check_handin.py`. I checked the reported numbers against the metrics table by
hand. I read the code changes rather than accepting them blind, and I confirmed there
was no look ahead in the backtest.

## On honesty
The clearest example is the sentiment result. Tilting the funds towards positive
sentiment sectors did not improve performance. Rather than hide this, I report it as a
finding and explain it through market efficiency. The credit is for testing the idea
and reporting the result, not for a result that flatters the project.
