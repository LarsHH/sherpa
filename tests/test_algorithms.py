from __future__ import absolute_import
import collections
import pandas
import sherpa
import logging
from test_sherpa import get_test_trial


logging.basicConfig(level=logging.DEBUG)
testlogger = logging.getLogger(__name__)


def test_median_stopping_rule():
    results_df = pandas.DataFrame(collections.OrderedDict(
        [('Trial-ID', [1]*3 + [2]*3 + [3]*3),
         ('Status', ['INTERMEDIATE']*9),
         ('Iteration', [1, 2, 3]*3),
         ('a', [1, 1, 1]*3),
         ('b', [2, 2, 2]*3),
         ('Objective', [0.1]*3 + [0.2]*3 + [0.3]*3)]
    ))

    stopper = sherpa.algorithms.MedianStoppingRule(min_iterations=2,
                                                   min_trials=1)

    t = get_test_trial(id=3)

    assert stopper.should_trial_stop(trial=t, results=results_df,
                                     lower_is_better=True)

    stopper = sherpa.algorithms.MedianStoppingRule(min_iterations=4,
                                                   min_trials=1)
    assert not stopper.should_trial_stop(trial=t, results=results_df,
                                         lower_is_better=True)

    stopper = sherpa.algorithms.MedianStoppingRule(min_iterations=2,
                                                   min_trials=4)
    assert not stopper.should_trial_stop(trial=t, results=results_df,
                                         lower_is_better=True)


def test_local_search():
    parameters, results, lower_is_better = sherpa.algorithms.get_sample_results_and_params()

    previous_configs = [{'param_a': row['param_a'], 'param_b': row['param_b']}
                        for _, row in results.iterrows()]

    best_params = results.loc[42, ['param_a', 'param_b']].to_dict()

    num_random_seeds = 3
    num_seeds_configs = 5
    num_test_steps = 10

    rs = sherpa.algorithms.RandomSearch(num_random_seeds)

    seed_configs = [rs.get_suggestion(parameters, results, lower_is_better)
                    for _ in range(num_seeds_configs)]

    alg = sherpa.algorithms.LocalSearch(num_random_seeds=num_random_seeds,
                                        seed_configurations=seed_configs)

    # one parameter is continuous so we can assume we don't sample same value
    # twice

    # seed configs
    for seed in seed_configs:
        p = alg.get_suggestion(parameters, results, lower_is_better)

        assert p == seed

    # random seeds
    for _ in range(num_random_seeds):
        p = alg.get_suggestion(parameters, results, lower_is_better)

        assert p not in seed_configs
        assert p not in previous_configs

    # hill climb
    for _ in range(num_test_steps):
        p = alg.get_suggestion(parameters, results, lower_is_better)

        assert (best_params['param_a'] == p['param_a']
                or best_params['param_b'] == p['param_b'])


def test_grid_search():
    parameters = sherpa.Parameter.grid({'a': [1, 2],
                                        'b': ['a', 'b']})

    alg = sherpa.algorithms.GridSearch()

    suggestion = alg.get_suggestion(parameters)
    seen = set()

    while suggestion:
        seen.add((suggestion['a'], suggestion['b']))
        suggestion = alg.get_suggestion(parameters)

    assert seen == {(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')}


def test_random_search_without_repetition_choice_parameter():
    parameters = sherpa.Parameter.grid({'a': [1, 2, 3], 
                                        'b': ['a', 'b', 'c']})

    alg = sherpa.algorithms.RandomSearch(max_num_trials=9, repeat_suggestions=False)

    suggestion = alg.get_suggestion(parameters)
    seen = set()
    while suggestion:
        seen.add((suggestion['a'], suggestion['b']))
        suggestion = alg.get_suggestion(parameters)
    assert seen == {(1, 'a'), (1, 'b'), (1, 'c'), (2, 'a'), (2, 'b'), (2, 'c'), (3, 'a'), (3, 'b'), (3, 'c')}, seen

def test_random_search_without_repetition_continuous_parameter():
    """
    Checks that the stopping criteria for continuous parameters works
    """
    parameters = [sherpa.core.Parameter.from_dict({'name': 'a', 'type': 'continuous', 'range': [0, 1]}),
                  sherpa.core.Parameter.from_dict({'name': 'b', 'type': 'choice', 'range': [0, 1, 2]})]

    alg = sherpa.algorithms.RandomSearch(max_num_trials=9, repeat_suggestions=False)

    suggestion = alg.get_suggestion(parameters)
    seen = set()
    while suggestion:
        seen.add((suggestion['a'], suggestion['b']))
        suggestion = alg.get_suggestion(parameters)
    assert len(seen) == 9, seen
