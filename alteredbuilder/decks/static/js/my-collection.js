
const CARD_SETS = { CORE: { hero_count: 18, common_count: 162, rare_count: 324, total_count: 504 } };

class CollectionStats {
    constructor() {
        this.stats = {};
        this.cards = {};
        this.collection = {};
        Object.keys(CARD_SETS).forEach(set => {
            this.stats[set] = {
                total_count: 0,
                common_playset_count: 0,
                rare_playset_count: 0,
                hero_count: 0,
                common_count: 0,
                rare_count: 0,
                unique_count: 0
            };
            this.cards[set] = [];
            this.collection[set] = {};
        });
    }

    add(reference, quantity) {
        let [alt, set, product, faction, nif, rarity] = reference.split("_");
        let id = [faction, nif, rarity].join("_");
        if (set == "COREKS") {
            set = "CORE";
        }
        if (!CARD_SETS[set]) {
            return;
        }
        let allowCount = !this.cards[set].includes(id);
        if (allowCount) this.stats[set].total_count += 1;
        this.collection[set][id] = quantity + (this.collection[set][id] || 0);
        if (this.#isHero(nif)) {
            if (allowCount) this.stats[set].hero_count += 1;
        } else if (this.#isCommon(rarity)) {
            if (allowCount) this.stats[set].common_count += 1;
            if (this.collection[set][id] >= 3 && (this.collection[set][id] - quantity) < 3) {
                this.stats[set].common_playset_count += 1;
            }
        } else if (this.#isRare(rarity)) {
            if (allowCount) this.stats[set].rare_count += 1;
            if (this.collection[set][id] >= 3 && (this.collection[set][id] - quantity) < 3) {
                this.stats[set].rare_playset_count += 1;
            }
        }

        this.cards[set].push(id);
    }

    getTotalCount(set) {
        return this.stats[set].total_count;
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
    getCardChance(set) {
        let heroChance = this.stats[set].hero_count / CARD_SETS[set].hero_count;
        let commonChance = this.stats[set].common_count / CARD_SETS[set].common_count;
        let rareChance = this.stats[set].rare_count / CARD_SETS[set].rare_count;
        return 7 / 8 * (1 - heroChance * (commonChance ** 8) * (rareChance ** 3)) + 1 / 8;
    }

    getCommonPlaysetChance(set) {
        return 1 - (this.stats[set].common_playset_count / CARD_SETS[set].common_count) ** 8
    }
    getRarePlaysetChance(set) {
        return 1 - (this.stats[set].rare_playset_count / CARD_SETS[set].rare_count) ** 3
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

    for (let [reference, quantity] of Object.entries(collection)) {
        if (!reference.includes("_U_") && !reference.includes("_P_")) {
            stats.add(reference, quantity);
        }
    }
    return stats;
}

function drawStats(stats) {

    Object.keys(CARD_SETS).forEach(set => {
        let totalCount = stats.getTotalCount(set);
        let newHeroChance = stats.getHeroChance(set);
        let newCommonChance = stats.getCommonChance(set);
        let newRareChance = stats.getRareChance(set);
        let newCardChance = stats.getCardChance(set);
        let playsetCommonChance = stats.getCommonPlaysetChance(set);
        let playsetRareChance = stats.getRarePlaysetChance(set);

        document.getElementById(`${set}-count`).textContent = totalCount;
        document.getElementById(`${set}-total-count`).textContent = CARD_SETS[set].total_count;
        drawChanceStat(set, "new", "card", newCardChance);
        drawChanceStat(set, "new", "hero", newHeroChance);
        drawChanceStat(set, "new", "common", newCommonChance);
        drawChanceStat(set, "new", "rare", newRareChance);

        drawChanceStat(set, "playset", "common", playsetCommonChance);
        drawChanceStat(set, "playset", "rare", playsetRareChance);
    });
}

function drawChanceStat(set, target, stat, chance) {
    document.getElementById(`${set}-${target}-${stat}-chance`).textContent = (chance * 100).toFixed(2);
    if (chance > 0) {
        document.getElementById(`${set}-${target}-${stat}-booster`).textContent = Math.round(1 / chance);
        document.getElementById(`${set}-${target}-${stat}-booster-block`).classList.remove("d-none");
    }
}

// IMPORT COLLECTION
document.getElementById("save-collection").addEventListener("click", () => {

    const collectionListEl = document.getElementById("collection-list");

    let cardEntries = textCollectionToEntries(collectionListEl.value);
    let collection = parseCardEntries(cardEntries);

    saveCollection(collection);
    
    let stats = generateStats(collection);
    drawStats(stats);
    printCollection(collection);
});
function printCollection(collection) {
    document.getElementById("collection-list").value = collectionToText(collection);
}
