"""Shared plain-English glossary — single source of truth for the
Dictionary page and the "?" tooltips across the app.
"""

GLOSSARY = {
    "Fund types": {
        "Combined fund": (
            "A fund that invests across both the 50 US equities and the 10 "
            "cryptocurrencies, so a single holding gives you a mix of the two "
            "asset classes in one place."
        ),
        "Equity fund": (
            "A fund that holds only the 50 US equities — the choice for "
            "investors who want to stay in the stock market without any "
            "crypto exposure."
        ),
        "Crypto fund": (
            "A fund that invests only in the 10 cryptocurrencies. It can "
            "deliver very high growth, but its value swings far more wildly "
            "than an equity or combined fund."
        ),
        "Max-Sharpe": (
            "A fund built to maximise the return earned for each unit of risk "
            "it takes — in other words, the best 'reward-for-risk' it can find."
        ),
        "Min-Variance": (
            "A fund built to keep its value swings as small as possible; it "
            "accepts lower growth in exchange for the smoothest ride."
        ),
        "Risk-Parity": (
            "A fund that spreads risk evenly across everything it holds, so no "
            "single asset or sector can dominate how bumpy the fund is."
        ),
    },
    "How funds are built": {
        "Portfolio": (
            "The full collection of investments held together as one fund."
        ),
        "Asset class": (
            "A broad family of investments that behave similarly — here, US "
            "equities (stocks) and cryptocurrencies."
        ),
        "Weight": (
            "The share of a fund's money placed in a particular asset. The "
            "weights of all assets always add up to 100%."
        ),
        "Optimiser": (
            "A computer method that searches for the best combination of "
            "weights for a stated goal, such as lowest risk or best "
            "reward-for-risk."
        ),
        "Rebalance": (
            "Periodically resetting a fund's weights back to their targets so "
            "that its risk profile does not drift away over time."
        ),
        "Diversification": (
            "Spreading money across many different assets so that a fall in "
            "one can be offset by gains in others, smoothing the overall ride."
        ),
        "Correlation": (
            "How closely two assets move together. Low correlation between "
            "assets is what makes diversification reduce a fund's risk."
        ),
        "Out-of-sample": (
            "A result measured on data the fund was not tuned against. It is "
            "a fairer test of how a fund might behave in the future."
        ),
        "Annualised": (
            "Expressed as the average per year, which lets you compare "
            "investments of different lengths on an equal footing."
        ),
    },
    "Risk & return": {
        "Return": (
            "The gain (or loss) an investment makes, usually shown as a "
            "percentage of what you put in."
        ),
        "Annualised return": (
            "The average return per year over a period, so different funds "
            "can be compared like for like."
        ),
        "Volatility": (
            "How much a fund's value swings up and down over time. Higher "
            "volatility means a bumpier ride and a wider range of outcomes."
        ),
        "Sharpe ratio": (
            "A single score of how much return you get for each unit of risk "
            "— the 'reward-for-risk' number. Higher is better."
        ),
        "Max drawdown": (
            "The worst peak-to-trough fall a fund suffered over the period — "
            "a sense of how bad a loss could get if you bought at the worst "
            "possible moment."
        ),
        "Risk": (
            "The chance that an investment loses money or behaves less "
            "predictably than hoped."
        ),
    },
    "News & sentiment": {
        "Sentiment": (
            "The overall mood of the news about a sector — positive, negative "
            "or neutral — as judged from the words used in headlines."
        ),
        "VADER": (
            "A rule-based tool that reads the words in a news headline and "
            "scores how positive or negative the tone is."
        ),
        "Compound score": (
            "VADER's single score for a headline, ranging from −1 (very "
            "negative) to +1 (very positive)."
        ),
        "Rolling mean": (
            "An average taken over a moving window of the most recent days, "
            "used to smooth out the day-to-day noise in a sentiment series."
        ),
    },
    "Investing basics": {
        "Compounding": (
            "Earning returns on your earlier returns, which is why money "
            "grows faster the longer it is left invested."
        ),
        "Monte Carlo simulation": (
            "Re-running the same investment scenario thousands of times with "
            "random ups and downs to map the range of possible outcomes."
        ),
        "Percentile": (
            "A point on a ranked list of outcomes: the 10th percentile means "
            "only 1 in 10 simulated results ended below it."
        ),
        "Median": (
            "The middle outcome of a ranked list — half of all results end "
            "above it and half below."
        ),
        "Initial investment": (
            "The lump sum you put into an investment at the very start."
        ),
        "Monthly contribution": (
            "A set amount of money you add to your investment each month."
        ),
        "Horizon": (
            "How long you plan to keep your money invested, usually measured "
            "in years."
        ),
        "Total contributed": (
            "The money you actually put in — the initial investment plus all "
            "monthly contributions."
        ),
    },
}

TERMS = {term: definition
         for category in GLOSSARY.values()
         for term, definition in category.items()}
