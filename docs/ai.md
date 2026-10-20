Card-game AI
============

Belote and Contrée
-----------------

Card choices use Monte Carlo samples of unknown hands. Each candidate card is
tested against the same sampled deals. Sampling respects observed suit voids,
the face-up card held by the taker, and publicly announced belote cards. It uses
opponents' hand sizes, not the card values supplied in the server snapshot.
Contrée's permission to discard when unable to overtrump is accounted for when
inferring void suits.

Rollouts use a small tactical policy: win cheaply, avoid unnecessarily overtaking
a partner, preserve trumps, and feed points to a partner only when the trick is
secure from the public evidence. Earlier decisions evaluate the current trick;
when each player has at most three cards left, rollouts play out the hand and
compare the actual awarded team scores. These are tactical continuations, not an
exhaustive endgame solver.

Card selection always chooses the best evaluated action, including when all
choices have negative expected value. The configured win threshold applies only
to bidding. Contrée evaluates legal numeric contracts, pass, contre and surcontre
using the selected scoring mode. Numeric bids in the same suit share a played
rollout, then score its result separately for each contract. Passing without an
existing contract uses a neutral zero baseline; the AI does not model subsequent
players' bidding decisions in that case.

`instance/config_ai.ini` continues to control `number_of_simulations`,
`min_number_simulations`, `wins_thresholds_for_action`, and
`max_thread_number_for_simulation`. No extra samples are required by default.
More samples can improve stability but increase response time. Hidden deals are
sampled with a randomized constraint matcher; this is not a uniform posterior
over possible deals and does not yet infer bidding conventions or trump ceilings.

Run the strategy regressions with:

```sh
venv/bin/python -m pytest tests/test_belote_strategy.py -q
```

Compare two versions with:

```sh
venv/bin/python scripts/benchmark_belote_ai.py \
  --baseline /path/to/baseline-checkout --deals 40 --samples 20 \
  --output /tmp/belote-ai-results.json
```

The baseline directory needs its own importable `romwhist` package and instance
configuration. The harness runs it in a separate process, replays each shuffle
with the teams swapped, checks every move's legality, and reports score margins,
win counts and decision latency. Contracts are fixed to isolate card play; this
does not measure bidding strength. Use fresh seed ranges (`--first-seed`) and
larger samples before drawing conclusions from small improvements.

Whist / Oh Hell
---------------

Whist uses its own target-aware rollout policy. Players try to win tricks while
below their bid, then shed dangerous cards and avoid taking further tricks once
they reach it. Legal follow-suit rules still apply; unlike Belote, a player may
discard instead of cutting when void in the led suit.

Every candidate is simulated through the remaining hand. Evaluation uses the
game's actual scoring: `bonus_win + tricks` for an exact bid, otherwise
`-abs(tricks - bid)`. Card and bid selection compare expected score even when
every choice is unfavorable. The Belote bidding win-percentage cutoff is not
used for Whist. Existing trick counts, the configured bonus, and actual trick
leaders survive snapshot round trips.

Candidate choices share sampled deals. Samples respect known suit voids and
exclude the turned-up trump card from every hand. Opponents' actual card values
in the server snapshot are ignored. Unannounced bids are estimated from sampled
players' own card strength; announced bids are retained, and simulated dealer
bids obey the rule forbidding total bids equal to the hand size. This is a rough
opponent model, not a learned bidding strategy.

The existing simulation-count and worker-count settings apply. Regressions cover
trump and no-trump hands, two through six players, and different deck sizes:

```sh
venv/bin/python -m pytest tests/test_whist_strategy.py -q
venv/bin/python scripts/benchmark_whist_ai.py \
  --baseline /path/to/baseline-checkout --deals 20 --samples 20 \
  --output /tmp/whist-ai-results.json
```

The Whist benchmark includes both bidding and card play. It repeats each shuffle
with the policies' seats swapped, varies hand sizes and trump/no-trump, and
reports average score, exact-bid frequency and decision latency. Whist remains
an individual game: the two players using one policy do not cooperate as a team.
