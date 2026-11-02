"""Reproduce the finite clean T2 crest candidate without modifying live recipes."""
from assemble_clean_cohorts import run
from prepare_clean_recipes import prepare
for unit in ('chemJack','reinforcedChemJack'):
 run(unit,'v4')
 prepare(unit,'v4')
