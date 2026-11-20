# Hyperparameter sweeps

Sweep: living_cost | baseline {'living_cost': -0.04, 'alpha': 0.5, 'gamma': 0.9, 'epsilon': 0.8} | 2000 episodes | seeds [0, 1, 2]

| living_cost | success % | mean steps | return (last 100) | matches VI % |
|---|---|---|---|---|
| -2 | 98 ± 1 | 7.4 | -3.93 | 90 |
| -0.4 | 98 ± 2 | 7.5 | 7.27 | 97 |
| -0.04 | 100 ± 0 | 7.7 | 9.65 | 90 |
| 0 | 100 ± 0 | 7.8 | 9.93 | 87 |
| 1 | 0 ± 0 | 199.0 | 188.20 | 62 |

Sweep: gamma | baseline {'living_cost': -0.04, 'alpha': 0.5, 'gamma': 0.9, 'epsilon': 0.8} | 2000 episodes | seeds [0, 1, 2]

| gamma | success % | mean steps | return (last 100) | matches VI % |
|---|---|---|---|---|
| 0.5 | 98 ± 1 | 7.5 | 9.40 | 90 |
| 0.7 | 97 ± 1 | 7.2 | 9.58 | 100 |
| 0.9 | 100 ± 0 | 7.7 | 9.65 | 90 |
| 0.99 | 100 ± 0 | 7.8 | 9.68 | 90 |

Sweep: alpha | baseline {'living_cost': -0.04, 'alpha': 0.5, 'gamma': 0.9, 'epsilon': 0.8} | 2000 episodes | seeds [0, 1, 2]

| alpha | success % | mean steps | return (last 100) | matches VI % |
|---|---|---|---|---|
| 0.05 | 99 ± 1 | 7.6 | 9.61 | 85 |
| 0.1 | 100 ± 0 | 7.9 | 9.64 | 74 |
| 0.3 | 97 ± 2 | 7.4 | 9.65 | 95 |
| 0.5 | 100 ± 0 | 7.7 | 9.65 | 90 |
| 0.9 | 100 ± 0 | 7.8 | 9.68 | 85 |

Sweep: epsilon | baseline {'living_cost': -0.04, 'alpha': 0.5, 'gamma': 0.9, 'epsilon': 0.8} | 2000 episodes | seeds [0, 1, 2]

| epsilon | success % | mean steps | return (last 100) | matches VI % |
|---|---|---|---|---|
| 0.05 | 91 ± 6 | 7.8 | 8.38 | 69 |
| 0.2 | 100 ± 0 | 7.7 | 9.70 | 72 |
| 0.5 | 100 ± 0 | 7.8 | 9.71 | 79 |
| 0.8 | 100 ± 0 | 7.7 | 9.65 | 90 |
| 1 | 98 ± 2 | 7.7 | 9.62 | 90 |

## Values picked by the step 3 rule

- living_cost = -0.04: success 100%, VI match 90%, 7.7 steps
- gamma = 0.9: success 100%, VI match 90%, 7.7 steps
- alpha = 0.5: success 100%, VI match 90%, 7.7 steps
- epsilon = 0.8: success 100%, VI match 90%, 7.7 steps
