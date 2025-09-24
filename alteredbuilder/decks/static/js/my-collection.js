
const CARD_SETS = {
    CORE: {
        booster: { hero_count: 18, common_count: 162, rare_count: 324, unique_count: 109 },
        gift: { common_count: 0, rare_count: 0 },
        total: { hero_count: 18, common_count: 162, rare_count: 324, unique_count: 109, total_count: 504 }
    },
    ALIZE: {
        booster: { hero_count: 12, common_count: 90, rare_count: 180, unique_count: 52 },
        gift: { common_count: 1, rare_count: 2 },
        total: { hero_count: 12, common_count: 91, rare_count: 182, unique_count: 52, total_count: 285 }
    },
    BISE: {
        booster: { hero_count: 12, common_count: 90, rare_count: 180, unique_count: 58 },
        gift: { common_count: 1, rare_count: 2 },
        total: { hero_count: 12, common_count: 91, rare_count: 182, unique_count: 58, total_count: 285 }
    },
    CYCLONE: {
        booster: { hero_count: 6, common_count: 102, rare_count: 204, unique_count: 63 },
        gift: { common_count: 0, rare_count: 0 },
        total: { hero_count: 6, common_count: 102, rare_count: 204, unique_count: 63, total_count: 312 }
    },
};

const IGNORED_IDS = {
    CORE: [
        "AX_31_C",  // Brassbug
        "BR_31_C",  // Booda
        "OR_31_C",  // Ordis Recruit
        "YZ_31_C",  // Maw
    ],
    ALIZE: [
        "AX_31_C",  // Brassbug
        "BR_31_C",  // Booda
        "OR_31_C",  // Ordis Recruit
        "YZ_47_C",  // Mana Moth
        "NE_02_C",  // Dragon Shade
    ],
    BISE: [
        "AX_31_C",  // Brassbug
        "OR_31_C",  // Ordis Recruit
        "YZ_47_C",  // Mana Moth
    ],
    CYCLONE: [
        "AX_31_C",  // Brassbug
        "BR_83_C",  // Halua
        "MU_83_C",  // Woollyback
        "YZ_47_C",  // Mana Moth
        "NE_03_C",  // Aerolith
    ]
}

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
        if (nif == "FOILER") {
            return;
        }
        if (set == "COREKS") {
            set = "CORE";
        }
        if (!CARD_SETS[set]) {
            return;
        }
        if (this.isIgnored(set, cardId)) {
            return;
        }
        let isNewCard = this.isNewCard(set, cardId);
        this.collection[set][cardId] = quantity + (this.collection[set][cardId] || 0);

        if (isNewCard) {
            this.stats[set].total_count += 1;
            if (this.#isHero(nif)) {
                this.stats[set].hero_count += 1;
            } else if (this.#isCommon(rarity)) {
                this.stats[set].common_count += 1;
            } else if (this.#isRare(rarity)) {
                this.stats[set].rare_count += 1;
            }
        }
        if (!this.#isHero(nif) && this.#isCommon(rarity)) {
            if (this.collection[set][cardId] >= 3 && (this.collection[set][cardId] - quantity) < 3) {
                this.stats[set].common_playset_count += 1;
            }
        } else if (this.#isRare(rarity)) {
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

    isNewCard(set, cardId) {
        return !this.cards[set].includes(cardId);
    }
    isIgnored(set, cardId) {
        return !!IGNORED_IDS[set].includes(cardId);
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

    getHeroPercentage(set) {
        return this.stats[set].hero_count / CARD_SETS[set].booster.hero_count;
    }
    getCommonPercentage(set) {
        return (this.stats[set].common_count - CARD_SETS[set].gift.common_count) / CARD_SETS[set].booster.common_count;
    }
    getRarePercentage(set) {
        return (this.stats[set].rare_count - CARD_SETS[set].gift.rare_count) / CARD_SETS[set].booster.rare_count;
    }
    getUniquePercentage(set) {
        return this.stats[set].unique_playset_count / CARD_SETS[set].booster.unique_count;
    }

    getCommonPlaysetPercentage(set) {
        return (this.stats[set].common_playset_count - CARD_SETS[set].gift.common_count) / CARD_SETS[set].booster.common_count;
    }
    getRarePlaysetPercentage(set) {
        return (this.stats[set].rare_playset_count - CARD_SETS[set].gift.rare_count) / CARD_SETS[set].booster.rare_count;
    }

    getHeroChance(set) {
        return 1 - this.getHeroPercentage(set);
    }
    getCommonChance(set) {
        return 1 - this.getCommonPercentage(set) ** 8;
    }
    getRareChance(set) {
        let rareChance = this.getRarePercentage(set);
        return 1 - 7 / 8 * (rareChance) ** 3 - 1 / 8 * (rareChance) ** 2;
    }
    getUniqueChance(set) {
        return (1 - this.getUniquePercentage(set)) / 8;
    }
    getCardChance(set) {
        return 7 / 8 * (1 - this.getHeroPercentage(set) * (this.getCommonPercentage(set) ** 8) * (this.getRarePercentage(set) ** 3)) + 1 / 8;
    }

    getRareChanceNoUnique(set) {
        return 1 - this.getRarePercentage(set) ** 3;
    }
    getCardChanceNoUnique(set) {
        return 1 - this.getHeroPercentage(set) * (this.getCommonPercentage(set) ** 8) * (this.getRarePercentage(set) ** 3);
    }

    getCommonPlaysetChance(set) {
        return 1 - this.getCommonPlaysetPercentage(set) ** 8;
    }
    getRarePlaysetChance(set) {
        let rarePercentage = this.getRarePlaysetPercentage(set);
        return 1 - 7 / 8 * (rarePercentage ** 3) - 1 / 8 * (rarePercentage ** 2);
    }
    getCardPlaysetChance(set) {
        let rarePercentage = this.getRarePlaysetPercentage(set);
        return 1 - (7 / 8 * (rarePercentage ** 3) + 1 / 8 * (rarePercentage ** 2)) * (this.getCommonPlaysetPercentage(set) ** 8) * (this.getUniquePercentage(set) / 8);
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
        document.getElementById(`${set}-total-count`).textContent = CARD_SETS[set].total.total_count;

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

        drawCountStat(set, "total", "hero", CARD_SETS[set].total.hero_count);
        drawCountStat(set, "total", "common", CARD_SETS[set].total.common_count);
        drawCountStat(set, "total", "rare", CARD_SETS[set].total.rare_count);
        drawCountStat(set, "total", "unique", CARD_SETS[set].total.unique_count);

        drawProgressStat(set, "hero", stats.getHeroCount(set), CARD_SETS[set].total.hero_count);
        drawProgressStat(set, "common", stats.getCommonCount(set), CARD_SETS[set].total.common_count);
        drawProgressStat(set, "rare", stats.getRareCount(set), CARD_SETS[set].total.rare_count);
        drawProgressStat(set, "unique", stats.getUniqueCount(set), CARD_SETS[set].total.unique_count);
        drawProgressStat(set, "all", stats.getTotalCount(set), CARD_SETS[set].total.total_count);
        drawProgressStat(set, "summary", stats.getTotalCount(set), CARD_SETS[set].total.total_count);
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

    const textCollection = document.getElementById("collection-list").value;

    let collection = textCollectionToEntries(textCollection);

    saveCollectionLocal(collection);
    // We parse again the collection from the entries because there might have been changes
    saveCollectionRemote(collectionToText(collection), true);
    importUniqueCards(collection);

    let stats = generateStats(collection);
    drawStats(stats);
    printCollection(collection);
});

function printCollection(collection) {
    if (!collection) {
        return;
    }
    document.getElementById("collection-list").value = collectionToText(collection);
}
