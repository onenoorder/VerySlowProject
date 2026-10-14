# WaterSim – the very slow water flow calculator 🐌💧

WaterSim is a small Python toolkit used by a (fictional) water board to calculate
how water flows through pipes, rivers, the ground, catchments and reservoirs.

The engineers love the results… but they hate waiting for them. A full run takes
**minutes** on a modern laptop. Your job: **use AI to find out why WaterSim is so slow
and fix it — without changing the results.**

## The cases

| Case          | What it calculates                                                                  | Module                                                 |
|---------------|-------------------------------------------------------------------------------------|--------------------------------------------------------|
| `pipes`       | Flow and pressure in a looped drinking-water network (Hardy Cross, Darcy-Weisbach)  | [pipe_network.py](watersim/pipe_network.py)            |
| `river`       | Daily water depth, velocity and flow regime in river reaches (Manning)              | [river.py](watersim/river.py)                          |
| `groundwater` | Groundwater levels around pumping wells (2D finite differences)                     | [groundwater.py](watersim/groundwater.py)              |
| `watershed`   | Where rain water flows over the terrain and where streams form (D8)                 | [watershed.py](watersim/watershed.py)                  |
| `runoff`      | River discharge from 5 years of hourly rainfall (SCS curve number, unit hydrograph) | [runoff.py](watersim/runoff.py)                        |
| `reservoir`   | How a reservoir dampens a flood wave (modified Puls)                                | [reservoir.py](watersim/reservoir.py)                  |
| `sensors`     | Cleaning and reporting of water level / discharge sensor logs                       | [sensors.py](watersim/sensors.py)                      |

All input data is generated synthetically by [data.py](watersim/data.py), so every
run produces exactly the same numbers.

## Setup

Requires Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```powershell
python main.py                 # run all cases (takes a few minutes!)
python main.py river sensors   # run only some cases
python main.py --list          # list the cases
python -m pytest               # run the tests (~10 s)
```

Each case prints its key results and its runtime; a summary is printed at the end.

### Running with Docker

No local Python needed. Only Docker (with Compose v2) is required. The project folder is
mounted into the container, so your code changes are picked up straight away without
rebuilding.

```powershell
docker compose build                           # build the image once
docker compose up                              # run all cases
docker compose run --rm watersim river sensors # run only some cases
docker compose run --rm watersim --list        # list the cases
docker compose run --rm tests                  # run the tests
docker compose run --rm tests -k river -v      # extra pytest arguments are passed through
```

Only rebuild (`docker compose build`) after changing `requirements.txt`. Keep in mind that
timings inside Docker can differ a little from a local run, so always compare like with like.

## The exercise

1. **Measure first.** Run `python main.py > baseline.txt` (or
   `docker compose run --rm watersim > baseline.txt`) and keep this file. It holds the
   reference results and runtimes.
2. **Find the bottlenecks with AI.** Ask your AI assistant to help you find out *where* the
   time goes. Don't guess — let it help you measure (profilers, timing, reasoning about
   complexity).
3. **Fix them with AI.** Let the AI propose and implement improvements, one case at a time.
4. **Verify.** After each change:
   - `python -m pytest` must stay green, and
   - the results printed by `python main.py <case>` must match `baseline.txt`
     (tiny differences in the last decimal are fine).
5. **Score.** Compare your total runtime with the baseline. How big is your speed-up?

### Rules

- Do **not** change the input sizes in [main.py](main.py) or the tests in [tests/](tests).
- Do **not** change *what* is calculated — the physics and the outputs must stay the same.
- Everything else is allowed: algorithms, data structures, libraries already in
  `requirements.txt`, refactoring, …

### Tips for working with AI

- Give the AI context: tell it what the code does, that results must not change, and
  that there are tests.
- Ask it to *explain* why something is slow before you let it change the code.
- Make one change at a time and re-run the tests. Don't accept a "fix" you can't verify.
- Be critical: is the AI's suggestion really faster? Measure it!
- Bonus: ask the AI for the time complexity (Big-O) before and after a fix.

### Scoreboard

| Team | Baseline total (s) | Final total (s) | Speed-up | Cases fixed |
|------|-------------------:|----------------:|---------:|------------:|
|      |                    |                 |          |             |
