
class CardSet {
    constructor(code, booster, gift, ignoredIds, boosterType) {
        this.code = code;

        this.booster = booster;
        this.gift = gift;
        if (this.gift === undefined || this.gift === null) {
            this.gift = { common_count: 0, rare_count: 0 };
        }
        this.total = {
            hero_count: this.booster.hero_count,
            common_count: this.booster.common_count + this.gift.common_count,
            rare_count: this.booster.rare_count + this.gift.rare_count,
            unique_count: this.booster.unique_count,
            exalt_count: this.booster.exalt_count || 0,
        };
        this.total.total_count = this.total.hero_count + this.total.common_count + this.total.rare_count + this.total.exalt_count;
        this.ignoredIds = ignoredIds;

        this.cards = [];
        this.uniqueCards = [];
        this.collection = {};
        this.stats = {
            total_count: 0,
            
            common_playset_count: 0,
            rare_playset_count: 0,
            unique_playset_count: 0,
            exalt_playset_count: 0,

            hero_count: 0,
            common_count: this.gift.common_count,
            rare_count: this.gift.rare_count,
            unique_count: 0,
            exalt_count: 0,
        };
        this.boosterType = new boosterType(this);
    }

    add(cardId, nif, rarity, quantity) {
        if (this.isIgnored(cardId)) {
            return;
        }
        let isNewCard = this.isNewCard(cardId);
        this.collection[cardId] = quantity + (this.collection[cardId] || 0);

        if (isNewCard) {
            this.stats.total_count += 1;
            if (this.isHero(nif)) {
                this.stats.hero_count += 1;
            } else if (this.isCommon(rarity)) {
                this.stats.common_count += 1;
            } else if (this.isRare(rarity)) {
                this.stats.rare_count += 1;
            } else if (this.isExalt(rarity)) {
                this.stats.exalt_count += 1;
            }
        }
        if (!this.isHero(nif) && this.isCommon(rarity)) {
            if (this.collection[cardId] >= 3 && (this.collection[cardId] - quantity) < 3) {
                this.stats.common_playset_count += 1;
            }
        } else if (this.isRare(rarity)) {
            if (this.collection[cardId] >= 3 && (this.collection[cardId] - quantity) < 3) {
                this.stats.rare_playset_count += 1;
            }
        } else if (this.isExalt(rarity)) {
            if (this.collection[cardId] >= 3 && (this.collection[cardId] - quantity) < 3) {
                this.stats.exalt_playset_count += 1;
            }
        }

        this.cards.push(cardId);
    }
    addUnique(cardId) {
        if (!this.uniqueCards.includes(cardId)) {
            this.uniqueCards.push(cardId);
            this.stats.unique_count += 1;
            this.stats.unique_playset_count += 1;
        }
    }
    isIgnored(cardId) {
        return !!this.ignoredIds.includes(cardId);
    }
    isNewCard(cardId) {
        return !this.cards.includes(cardId);
    }
    isHero(nif) {
        nif = parseInt(nif);
        return (1 <= nif && nif <= 3) || nif === 65;
    }
    isCommon(rarity) {
        return rarity == "C";
    }
    isRare(rarity) {
        return rarity == "R1" || rarity == "R2";
    }
    isExalt(rarity) {
        return rarity == "E";
    }

    getTotalCount() {
        return this.stats.total_count;
    }
    getHeroCount() {
        return this.stats.hero_count;
    }
    getCommonCount() {
        return this.stats.common_count;
    }
    getRareCount() {
        return this.stats.rare_count;
    }
    getExaltCount() {
        return this.stats.exalt_count;
    }
    getUniqueCount() {
        return this.stats.unique_count;
    }

    getHeroTotal() {
        return this.total.hero_count;
    }
    getCommonTotal() {
        return this.total.common_count;
    }
    getRareTotal() {
        return this.total.rare_count;
    }
    getExaltTotal() {
        return this.total.exalt_count;
    }
    getUniqueTotal() {
        return this.total.unique_count;
    }
    getTotalAggregation() {
        return this.total.total_count;
    }

    getHeroPercentage() {
        return this.stats.hero_count / this.booster.hero_count;
    }
    getCommonPercentage() {
        return (this.stats.common_count - this.gift.common_count) / this.booster.common_count;
    }
    getRarePercentage() {
        return (this.stats.rare_count - this.gift.rare_count) / this.booster.rare_count;
    }
    getUniquePercentage() {
        return this.stats.unique_count / this.booster.unique_count;
    }
    getExaltPercentage() {
        return this.stats.exalt_count / this.booster.exalt_count;
    }

    getCommonPlaysetPercentage() {
        return (this.stats.common_playset_count - this.gift.common_count) / this.booster.common_count;
    }
    getRarePlaysetPercentage() {
        return (this.stats.rare_playset_count - this.gift.rare_count) / this.booster.rare_count;
    }
    getUniquePlaysetPercentage() {
        return this.stats.unique_playset_count / this.booster.unique_count;
    }
    getExaltPlaysetPercentage() {
        return this.stats.exalt_playset_count / this.booster.exalt_count;
    }
}
