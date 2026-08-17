"""Statistical confirmation layer — a BADGE, and only a badge.

Invariant 5: this module contributes ZERO to the score. engine/score.py does
not import it, does not know it exists, and must never learn. The score is
fired rule weights plus the complaint bonus; everything here is a second
opinion an officer can read next to that number, not a term inside it.

What it answers: "is this shop unusual, or is this just what the district looks
like?" A rulebook threshold says a shop crossed a line. A z-score says how far
from its peers it stands. The two disagree often, and when they do, the
disagreement is worth showing rather than resolving.

Moved here from routers/cases.py: engine/ holds domain computation, routers/
holds endpoints. The logic is unchanged — same population, same exclusions,
same rounding.
"""

from statistics import mean, pstdev

# A z-score at or beyond this is called "confirming". Not tuned to the demo:
# #4521 lands at 1.66 against it and its badge reads "does not confirm".
Z_CONFIRMS_AT = 2.0


def worst_variance(features):
    """The variance at the located gap — how much this shop lost at its worst hop."""
    measured = [
        v
        for v in (
            features.get("variance_dispatch_to_receipt"),
            features.get("variance_receipt_to_counter"),
        )
        if v is not None
    ]
    return min(measured) if measured else None


def z_scores(worst_by_shop: dict):
    """How far each shop's worst hop sits from the district-wide norm.

    Signed so that a WORSE shop scores higher: variances are negative, so the
    distance is measured as (population mean - this shop), which puts an
    unusually large shortfall at a positive z.

    Shops with no measurable variance are excluded from the population rather
    than counted as zero — F5 again. A shop whose scale was offline is not a
    shop with no shortfall, and folding it in as 0.0% would drag the mean
    toward clean and inflate everyone else's z. It gets None back and does not
    vote on where the norm sits.

    Confirming badge only. Nothing here reaches the score.
    """
    values = [v for v in worst_by_shop.values() if v is not None]
    if len(values) < 2:
        return {shop_id: None for shop_id in worst_by_shop}

    population_mean = mean(values)
    spread = pstdev(values)
    if not spread:
        return {shop_id: None for shop_id in worst_by_shop}

    return {
        shop_id: (round((population_mean - value) / spread, 2) if value is not None else None)
        for shop_id, value in worst_by_shop.items()
    }


def z_scores_from_features(features_by_shop: dict):
    """z-score per shop, straight from the feature dicts reconcile() produced."""
    return z_scores({shop_id: worst_variance(f) for shop_id, f in features_by_shop.items()})


def confirms(z_score):
    """Does the statistical layer back the rulebook up on this case?

    None is not confirmation. A shop we could not place against its peers is
    unconfirmed, the same way an unevaluated rule is not a passed rule.
    """
    return z_score is not None and z_score >= Z_CONFIRMS_AT
