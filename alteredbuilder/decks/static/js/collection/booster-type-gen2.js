
class BoosterTypeGen2 {
    constructor(set) {
        this.set = set;
        this.description = "Lorem Ipsum";
    }

    getDescription() {
        return this.description;
    }

    getHeroChance() {
        // Heroes have a 1.25% to be on the 12th slot and a 70% on the 13th
        // (1 - (1-0.7)*(1-0.0125)) * (1 - H)
        return 0.70375 * (1 - this.set.getHeroPercentage());
    }
    getCommonChance() {
        // There are 9 slots for common cards
        // 1 - H^9
        return 1 - this.set.getCommonPercentage() ** 9;
    }
    getRareChance() {
        // There are 3 slots for rare cards except in 1 every 4-5 boosters, where there
        // are two (to make room for a unique, an exalted or a hero)
        // 1 - (0.7715*R^3 + 0.2285*R^2)
        let rarePercentage = this.set.getRarePercentage()
        return 1 - (0.7715 * rarePercentage ** 3 + 0.2285 * rarePercentage ** 2);
    }
    getUniqueChance() {
        // There's 1 slot for a unique card once every 6 boosters
        // 1/6*(1-U)
        return (1 - this.set.getUniquePercentage()) * 0.166;
    }
    getNewCardChance() {
        // There's 1 hero, 9 commons and 3 slots for rare cards except in 1 every 4-5
        // boosters, where there are just two for rares, but one unique
        // 0.7715*(1 - (0.7*H+0.3) * C^8 * R^3) + 0.166*(1 - (0.7*H+0.3) * C^8 * R^2 * U) + 0.05*(1 - (0.7*H+0.3)*C^8*R^2*E) + 0.0125*(1 - (0.7*H+0.3)*C^8*R^2*H)
        // To avoid repeating calculations: x = (0.7*H+0.3)*C^8*R^2
        // Therefore: 0.7715*(1 - x * R) + 0.166*(1 - x * U) + 0.05*(1 - x * E) + 0.0125*(1 - x * H)
        let heroPercentage = this.set.getHeroPercentage();
        let commonPercentage = this.set.getCommonPercentage();
        let rarePercentage = this.set.getRarePercentage();
        let uniquePercentage = this.set.getUniquePercentage();
        let exaltPercentage = this.set.getExaltPercentage();

        let x = commonPercentage ** 9 * rarePercentage ** 2 * (0.7 * heroPercentage + 0.3);
        return 1 - x * (0.7715 * rarePercentage + 0.166 * uniquePercentage + 0.05 * exaltPercentage + 0.0125 * heroPercentage);
    }

    getRareChanceNoUnique() {
        // There are 3 slots for rare cards
        // 1 - R^3
        return 1 - this.set.getRarePercentage() ** 3;
    }
    getCardChanceNoUnique() {
        // There's 1 hero (70%), 9 commons and 3 slots for rare cards
        // 1 - (0.7*H+0.3) * C^9 * R^3
        let heroPercentage = this.set.getHeroPercentage();
        let commonPercentage = this.set.getCommonPercentage();
        let rarePercentage = this.set.getRarePercentage();

        return 1 - (0.7 * heroPercentage + 0.3) * commonPercentage ** 9 * rarePercentage ** 3;
    }

    getCommonPlaysetChance() {
        // There are 9 slots for common cards
        // 1 - CP^9
        return 1 - this.set.getCommonPlaysetPercentage() ** 9;
    }
    getRarePlaysetChance() {
        // There are 3 slots for rare cards except in 1 every 4-5 boosters, where there
        // are two (to make room for a unique or exalt)
        // 1 - 0.7715*RP^3 - (1-0.7715)*RP^2
        let rarePercentage = this.set.getRarePlaysetPercentage();
        return 1 - 0.7715 * (rarePercentage ** 3) - 0.2285 * (rarePercentage ** 2);
    }
    getCardPlaysetChance() {
        let commonPercentage = this.set.getCommonPlaysetPercentage();
        let rarePercentage = this.set.getRarePlaysetPercentage();
        let uniquePercentage = this.set.getUniquePlaysetPercentage();
        let exaltPercentage = this.set.getExaltPlaysetPercentage();

        let x = commonPercentage ** 9 * rarePercentage ** 2;

        return 1 - x * (0.7715 * rarePercentage + 0.166 * uniquePercentage + 0.05 * exaltPercentage);
    }
}
