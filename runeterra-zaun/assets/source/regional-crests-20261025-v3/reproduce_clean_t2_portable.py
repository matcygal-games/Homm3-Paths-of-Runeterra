"""Reproduce the finite portable clean T2 candidate without changing live recipes."""
from assemble_clean_cohorts import run
from prepare_clean_recipes_v2 import prepare
for unit in ('chemJack','reinforcedChemJack'):
 run(unit,'v4')
 prepare(unit,'v4')
