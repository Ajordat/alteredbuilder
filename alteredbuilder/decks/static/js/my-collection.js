
const CARD_SETS = {
    CORE: { hero_count: 18, common_count: 162, rare_count: 324, unique_count: 109, total_count: 504 },
    ALIZE: { hero_count: 12, common_count: 90, rare_count: 180, unique_count: 52, total_count: 282 },
};

class CollectionStats {
    constructor() {
        this.stats = {};
        this.cards = {};
        this.uniqueCards = {};
        this.collection = {};
        Object.keys(CARD_SETS).forEach(set => {
            this.stats[set] = {
                total_count: 0,
                common_playset_count: 0,
                rare_playset_count: 0,
                unique_playset_count: 0,
                hero_count: 0,
                common_count: 0,
                rare_count: 0,
                unique_count: 0
            };
            this.cards[set] = [];
            this.uniqueCards[set] = [];
            this.collection[set] = {};
        });
    }

    add(reference, quantity) {
        let [alt, set, product, faction, nif, rarity] = reference.split("_");
        let cardId = [faction, nif, rarity].join("_");
        if (set == "COREKS") {
            set = "CORE";
        }
        if (!CARD_SETS[set]) {
            return;
        }
        let allowCount = !this.cards[set].includes(cardId);
        if (allowCount) this.stats[set].total_count += 1;
        this.collection[set][cardId] = quantity + (this.collection[set][cardId] || 0);
        if (this.#isHero(nif)) {
            if (allowCount) this.stats[set].hero_count += 1;
        } else if (this.#isCommon(rarity)) {
            if (allowCount) this.stats[set].common_count += 1;
            if (this.collection[set][cardId] >= 3 && (this.collection[set][cardId] - quantity) < 3) {
                this.stats[set].common_playset_count += 1;
            }
        } else if (this.#isRare(rarity)) {
            if (allowCount) this.stats[set].rare_count += 1;
            if (this.collection[set][cardId] >= 3 && (this.collection[set][cardId] - quantity) < 3) {
                this.stats[set].rare_playset_count += 1;
            }
        }

        this.cards[set].push(cardId);
    }

    addPromo(reference, quantity) {
        this.add(reference + "_C", quantity);
    }

    addUnique(reference) {
        let [alt, set, product, faction, nif, rarity, id] = reference.split("_");
        let cardId = [faction, nif].join("_");
        if (set == "COREKS") {
            set = "CORE";
        }
        if (!CARD_SETS[set]) {
            return;
        }
        if (!this.uniqueCards[set].includes(cardId)) {
            this.uniqueCards[set].push(cardId);
            this.stats[set].unique_count += 1;
            this.stats[set].unique_playset_count += 1;
        }
    }

    getTotalCount(set) {
        return this.stats[set].total_count;
    }
    getHeroCount(set) {
        return this.stats[set].hero_count;
    }
    getCommonCount(set) {
        return this.stats[set].common_count;
    }
    getRareCount(set) {
        return this.stats[set].rare_count;
    }
    getUniqueCount(set) {
        return this.stats[set].unique_count;
    }

    getHeroChance(set) {
        return 1 - (this.stats[set].hero_count / CARD_SETS[set].hero_count);
    }
    getCommonChance(set) {
        return 1 - (this.stats[set].common_count / CARD_SETS[set].common_count) ** 8;
    }
    getRareChance(set) {
        let rareChance = this.stats[set].rare_count / CARD_SETS[set].rare_count;
        return 1 - 7 / 8 * (rareChance) ** 3 - 1 / 8 * (rareChance) ** 2;
    }
    getUniqueChance(set) {
        return (1 - this.stats[set].unique_playset_count / CARD_SETS[set].unique_count) / 8;
    }
    getCardChance(set) {
        let heroChance = this.stats[set].hero_count / CARD_SETS[set].hero_count;
        let commonChance = this.stats[set].common_count / CARD_SETS[set].common_count;
        let rareChance = this.stats[set].rare_count / CARD_SETS[set].rare_count;
        return 7 / 8 * (1 - heroChance * (commonChance ** 8) * (rareChance ** 3)) + 1 / 8;
    }

    getRareChanceNoUnique(set) {
        return 1 - (this.stats[set].rare_count / CARD_SETS[set].rare_count) ** 3;
    }
    getCardChanceNoUnique(set) {
        let heroChance = this.stats[set].hero_count / CARD_SETS[set].hero_count;
        let commonChance = this.stats[set].common_count / CARD_SETS[set].common_count;
        let rareChance = this.stats[set].rare_count / CARD_SETS[set].rare_count;
        return 1 - heroChance * (commonChance ** 8) * (rareChance ** 3);
    }

    getCommonPlaysetChance(set) {
        return 1 - (this.stats[set].common_playset_count / CARD_SETS[set].common_count) ** 8;
    }
    getRarePlaysetChance(set) {
        let rareBooster = (this.stats[set].rare_playset_count / CARD_SETS[set].rare_count) ** 3;
        let uniqueBooster = (this.stats[set].rare_playset_count / CARD_SETS[set].rare_count) ** 2;
        return 1 - 7 / 8 * rareBooster - 1 / 8 * uniqueBooster;
    }
    getCardPlaysetChance(set) {
        let commonChance = (this.stats[set].common_playset_count / CARD_SETS[set].common_count) ** 8;
        let rareBooster = (this.stats[set].rare_playset_count / CARD_SETS[set].rare_count) ** 3;
        let uniqueBooster = (this.stats[set].rare_playset_count / CARD_SETS[set].rare_count) ** 2;
        let uniqueChance = this.stats[set].unique_playset_count / CARD_SETS[set].unique_count;
        return 1 - (7 / 8 * rareBooster + 1 / 8 * uniqueBooster) * commonChance * (uniqueChance / 8);
    }

    #isHero(nif) {
        nif = parseInt(nif);
        return 1 <= nif && nif <= 3;
    }
    #isCommon(rarity) {
        return rarity == "C";
    }
    #isRare(rarity) {
        return rarity == "R1" || rarity == "R2";
    }
}

document.addEventListener("DOMContentLoaded", () => {

    let collection = fetchCollection();
    let stats = generateStats(collection);
    drawStats(stats);
    printCollection(collection);

});

function generateStats(collection) {
    let stats = new CollectionStats();
    if (!collection) {
        return stats;
    }
    for (let [reference, quantity] of Object.entries(collection)) {
        if (reference.includes("_U_")) {
            stats.addUnique(reference);
        } else if (reference.includes("_P_")) {
            stats.addPromo(reference, quantity);
        } else {
            stats.add(reference, quantity);
        }
    }
    return stats;
}

function drawStats(stats) {

    Object.keys(CARD_SETS).forEach(set => {

        document.getElementById(`${set}-owned-count`).textContent = stats.getTotalCount(set);
        document.getElementById(`${set}-total-count`).textContent = CARD_SETS[set].total_count;

        let heroChance = stats.getHeroChance(set);
        let commonChance = stats.getCommonChance(set);
        drawChanceStat(set, "new", "hero", heroChance);
        drawChanceStat(set, "new", "common", commonChance);
        drawChanceStat(set, "new", "rare", stats.getRareChance(set));
        drawChanceStat(set, "new", "card", stats.getCardChance(set));

        drawChanceStat(set, "new-no-unique", "hero", heroChance);
        drawChanceStat(set, "new-no-unique", "common", commonChance);
        drawChanceStat(set, "new-no-unique", "rare", stats.getRareChanceNoUnique(set));
        drawChanceStat(set, "new-no-unique", "card", stats.getCardChanceNoUnique(set));

        drawChanceStat(set, "playset", "common", stats.getCommonPlaysetChance(set));
        drawChanceStat(set, "playset", "rare", stats.getRarePlaysetChance(set));
        drawChanceStat(set, "playset", "unique", stats.getUniqueChance(set));
        drawChanceStat(set, "playset", "card", stats.getCardPlaysetChance(set));

        drawCountStat(set, "owned", "hero", stats.getHeroCount(set));
        drawCountStat(set, "owned", "common", stats.getCommonCount(set));
        drawCountStat(set, "owned", "rare", stats.getRareCount(set));
        drawCountStat(set, "owned", "unique", stats.getUniqueCount(set));

        drawCountStat(set, "total", "hero", CARD_SETS[set].hero_count);
        drawCountStat(set, "total", "common", CARD_SETS[set].common_count);
        drawCountStat(set, "total", "rare", CARD_SETS[set].rare_count);
        drawCountStat(set, "total", "unique", CARD_SETS[set].unique_count);

        drawProgressStat(set, "hero", stats.getHeroCount(set), CARD_SETS[set].hero_count);
        drawProgressStat(set, "common", stats.getCommonCount(set), CARD_SETS[set].common_count);
        drawProgressStat(set, "rare", stats.getRareCount(set), CARD_SETS[set].rare_count);
        drawProgressStat(set, "unique", stats.getUniqueCount(set), CARD_SETS[set].unique_count);
        drawProgressStat(set, "all", stats.getTotalCount(set), CARD_SETS[set].total_count);
    });
}

function drawChanceStat(set, target, stat, chance) {
    document.getElementById(`${set}-${target}-${stat}-chance`).textContent = (chance * 100).toFixed(2);
    try {
        if (chance > 0) {
            document.getElementById(`${set}-${target}-${stat}-booster`).textContent = Math.round(1 / chance);
            document.getElementById(`${set}-${target}-${stat}-booster-block`).classList.remove("d-none");
            document.getElementById(`${set}-${target}-${stat}-booster-zero-block`).classList.add("d-none");
        } else {
            document.getElementById(`${set}-${target}-${stat}-booster-block`).classList.add("d-none");
            document.getElementById(`${set}-${target}-${stat}-booster-zero-block`).classList.remove("d-none");
        }
    } catch (e) { }
}
function drawCountStat(set, target, stat, count) {
    document.getElementById(`${set}-${target}-${stat}-count`).textContent = count;
}
function drawProgressStat(set, target, owned, total) {
    let progressEl = document.getElementById(`${set}-${target}-progress`);
    let percentage = owned / total * 100;
    progressEl.style.width = `${percentage}%`;
    progressEl.setAttribute("aria-valuenow", percentage.toFixed(2));
    progressEl.textContent = `${percentage.toFixed(2)}%`;
}

// IMPORT COLLECTION
document.getElementById("save-collection").addEventListener("click", () => {

    const collectionListEl = document.getElementById("collection-list");

    let cardEntries = textCollectionToEntries(collectionListEl.value);
    let collection = parseCardEntries(cardEntries);
    let previousCollection = fetchCollection();

    saveCollection(collection);
    importUniqueCards(previousCollection, collection);

    let stats = generateStats(collection);
    drawStats(stats);
    printCollection(collection);
});
function printCollection(collection) {
    document.getElementById("collection-list").value = collectionToText(collection);
}
