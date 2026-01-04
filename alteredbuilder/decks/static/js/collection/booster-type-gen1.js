
class BoosterTypeGen1 {
    constructor(set) {
        this.set = set;
        this.description = "Includes 1 hero, 8 commons, 3 rares. Once every 8 boosters, a rare slot is replaced with a unique card.";
    }

    getDescription() {
        return this.description;
    }

    getHeroChance() {
        // 1 - H
        return 1 - this.set.getHeroPercentage();
    }
    getCommonChance() {
        // There are 8 slots for common cards
        // 1 - H^8
        return 1 - this.set.getCommonPercentage() ** 8;
    }
    getRareChance() {
        // There are 3 slots for rare cards except in 1 every 8 boosters, where there
        // are two (to make room for a unique)
        // 1 - (7/8*R^3 + 1/8*R^2)
        let rarePercentage = this.set.getRarePercentage()
        return 1 - (0.875 * rarePercentage ** 3 + 0.125 * rarePercentage ** 2);
    }
    getUniqueChance() {
        // There's 1 slot for a unique card once every 8 boosters
        // 1/8*(1-U)
        return (1 - this.set.getUniquePercentage()) * 0.125;
    }
    getNewCardChance() {
        // There's 1 hero, 8 commons and 3 slots for rare cards except in 1 every 8
        // boosters, where there are just two for rares, but one unique
        // 7/8*(1 - H * C^8 * R^3) + 1/8*(1 - H * C^8 * R^2 * U)
        // To avoid repeating calculations: x = H*C^8*R^2
        // Therefore: 7/8*(1 - x * R) + 1/8*(1 - x * U)
        let heroPercentage = this.set.getHeroPercentage();
        let commonPercentage = this.set.getCommonPercentage();
        let rarePercentage = this.set.getRarePercentage();
        let uniquePercentage = this.set.getUniquePercentage();

        let x = heroPercentage * (commonPercentage ** 8) * (rarePercentage ** 2);
        return 0.875 * (1 - x * rarePercentage) + 0.125 * (1 - x * uniquePercentage);
    }

    getRareChanceNoUnique() {
        // There are 3 slots for rare cards
        // 1 - R^3
        return 1 - this.set.getRarePercentage() ** 3;
    }
    getCardChanceNoUnique() {
        // There's 1 hero, 8 commons and 3 slots for rare cards
        // 1 - H * C^8 * R^3
        let heroPercentage = this.set.getHeroPercentage();
        let commonPercentage = this.set.getCommonPercentage();
        let rarePercentage = this.set.getRarePercentage();

        return 1 - heroPercentage * (commonPercentage ** 8) * (rarePercentage ** 3);
    }

    getCommonPlaysetChance() {
        // There are 8 slots for common cards
        // 1 - CP^8
        return 1 - this.set.getCommonPlaysetPercentage() ** 8;
    }
    getRarePlaysetChance() {
        // There are 3 slots for rare cards except in 1 every 8 boosters, where there
        // are two (to make room for a unique)
        // 1 - 7/8*RP^3 - 1/8*RP^2
        let rarePercentage = this.set.getRarePlaysetPercentage();
        return 1 - 0.875 * (rarePercentage ** 3) - 0.125 * (rarePercentage ** 2);
    }
    getCardPlaysetChance() {
        // There are 8 commons and 3 slots for rare cards except in 1 every 8
        // boosters, where there are just two for rares, but one unique
        // 7/8*(1 - CP^8 * RP^3) + 1/8*(1 - CP^8 * RP^2 * UP)
        // To avoid repeating calculations: x = CP^8*RP^2
        // Therefore: 7/8*(1 - x * RP) + 1/8*(1 - x * UP)
        let commonPercentage = this.set.getCommonPlaysetPercentage();
        let rarePercentage = this.set.getRarePlaysetPercentage();
        let uniquePercentage = this.set.getUniquePlaysetPercentage();

        let x = commonPercentage ** 8 * rarePercentage ** 2;
        return 1 - x * (0.875 * rarePercentage + 0.125 * uniquePercentage);
    }
}
