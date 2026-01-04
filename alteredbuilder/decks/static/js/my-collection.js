
const CARD_SETS = {
    CORE: {
        booster: { hero_count: 18, common_count: 162, rare_count: 324, unique_count: 109 },
        ignoredIds: [
            "AX_31_C",  // Brassbug
            "BR_31_C",  // Booda
            "OR_31_C",  // Ordis Recruit
            "YZ_31_C",  // Maw
        ],
        boosterType: BoosterTypeGen1
    },
    ALIZE: {
        booster: { hero_count: 12, common_count: 90, rare_count: 180, unique_count: 52 },
        gift: { common_count: 1, rare_count: 2 },
        ignoredIds: [
            "AX_31_C",  // Brassbug
            "BR_31_C",  // Booda
            "OR_31_C",  // Ordis Recruit
            "YZ_47_C",  // Mana Moth
            "NE_02_C",  // Dragon Shade
        ],
        boosterType: BoosterTypeGen1
    },
    BISE: {
        booster: { hero_count: 12, common_count: 90, rare_count: 180, unique_count: 58 },
        gift: { common_count: 1, rare_count: 2 },
        ignoredIds: [
            "AX_31_C",  // Brassbug
            "OR_31_C",  // Ordis Recruit
            "YZ_47_C",  // Mana Moth
        ],
        boosterType: BoosterTypeGen1
    },
    CYCLONE: {
        booster: { hero_count: 6, common_count: 102, rare_count: 204, unique_count: 63 },
        ignoredIds: [
            "AX_31_C",  // Brassbug
            "BR_83_C",  // Halua
            "MU_83_C",  // Woollyback
            "YZ_47_C",  // Mana Moth
            "NE_03_C",  // Aerolith
        ],
        boosterType: BoosterTypeGen1
    },
    DUSTER: {
        booster: { hero_count: 6, common_count: 96, rare_count: 192, unique_count: 59, exalt_count: 6 },
        ignoredIds: [],
        boosterType: BoosterTypeGen2
    },
};

class CollectionManager {
    constructor() {
        this.sets = {};
        Object.keys(CARD_SETS).forEach(code => {
            let set = CARD_SETS[code];
            this.sets[code] = new CardSet(code, set.booster, set.gift, set.ignoredIds, set.boosterType);
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
        if (!this.sets[set]) {
            return;
        }

        this.sets[set].add(cardId, nif, rarity, quantity);
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
        if (!this.sets[set]) {
            return;
        }
        this.sets[set].addUnique(cardId);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    let collection = fetchCollection();
    let manager = generateStats(collection);
    drawStats(manager);
    printCollection(collection);
});

function generateStats(collection) {
    let manager = new CollectionManager();
    if (!collection) {
        return manager;
    }
    for (let [reference, quantity] of Object.entries(collection)) {
        if (reference.includes("_U_")) {
            manager.addUnique(reference);
        } else if (reference.includes("_P_")) {
            manager.addPromo(reference, quantity);
        } else {
            manager.add(reference, quantity);
        }
    }
    return manager;
}

function drawStats(manager) {

    Object.keys(manager.sets).forEach(code => {
        set = manager.sets[code];
        booster = set.boosterType;

        document.getElementById(`${code}-booster-description`).textContent = booster.getDescription();
        document.getElementById(`${code}-owned-count`).textContent = set.getTotalCount();
        document.getElementById(`${code}-total-count`).textContent = set.total.total_count;

        let heroChance = booster.getHeroChance();
        let commonChance = booster.getCommonChance();
        drawChanceStat(code, "new", "hero", heroChance);
        drawChanceStat(code, "new", "common", commonChance);
        drawChanceStat(code, "new", "rare", booster.getRareChance());
        drawChanceStat(code, "new", "unique", booster.getUniqueChance());
        drawChanceStat(code, "new", "card", booster.getNewCardChance());

        drawChanceStat(code, "new-no-unique", "hero", heroChance);
        drawChanceStat(code, "new-no-unique", "common", commonChance);
        drawChanceStat(code, "new-no-unique", "rare", booster.getRareChanceNoUnique());
        drawChanceStat(code, "new-no-unique", "card", booster.getCardChanceNoUnique());

        drawChanceStat(code, "playset", "common", booster.getCommonPlaysetChance());
        drawChanceStat(code, "playset", "rare", booster.getRarePlaysetChance());
        drawChanceStat(code, "playset", "unique", booster.getUniqueChance());
        drawChanceStat(code, "playset", "card", booster.getCardPlaysetChance());

        drawCountStat(code, "owned", "hero", set.getHeroCount());
        drawCountStat(code, "owned", "common", set.getCommonCount());
        drawCountStat(code, "owned", "rare", set.getRareCount());
        drawCountStat(code, "owned", "unique", set.getUniqueCount());

        drawCountStat(code, "total", "hero", set.total.hero_count);
        drawCountStat(code, "total", "common", set.total.common_count);
        drawCountStat(code, "total", "rare", set.total.rare_count);
        drawCountStat(code, "total", "unique", set.total.unique_count);

        drawProgressStat(code, "hero", set.getHeroCount(), set.total.hero_count);
        drawProgressStat(code, "common", set.getCommonCount(), set.total.common_count);
        drawProgressStat(code, "rare", set.getRareCount(), set.total.rare_count);
        drawProgressStat(code, "unique", set.getUniqueCount(), set.total.unique_count);
        drawProgressStat(code, "all", set.getTotalCount(), set.total.total_count);
        drawProgressStat(code, "summary", set.getTotalCount(), set.total.total_count);
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
