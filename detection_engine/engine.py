
from rules import run_rules
from statistical import run_statistical
from combiner import combine


def detect(flows, config):
    
    rule_dets = run_rules(flows, config)
    stat_dets = run_statistical(flows, config)
    return {
        "rule": rule_dets,
        "statistical": stat_dets,
        "combined": combine(rule_dets, stat_dets),
    }