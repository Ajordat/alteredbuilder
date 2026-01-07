
class BoosterTypeBase {
    constructor(set) {
        this.set = set;
    }

    getDescription() {
        _notImplemented();
    }

    getHeroChance() {
        _notImplemented();
    }
    getCommonChance() {
        _notImplemented();
    }
    getRareChance() {
        _notImplemented();
    }
    getExaltChance() {
        return 0;
    }
    getUniqueChance() {
        _notImplemented();
    }
    getNewCardChance() {
        _notImplemented();
    }

    getHeroChanceNoUnique() {
        return this.getHeroChance();
    }
    getRareChanceNoUnique() {
        _notImplemented();
    }
    getCardChanceNoUnique() {
        _notImplemented();
    }

    getCommonPlaysetChance() {
        _notImplemented();
    }
    getRarePlaysetChance() {
        _notImplemented();
    }
    getExaltPlaysetChance() {
        return 0;
    }
    getUniquePlaysetChance() {
        return this.getUniqueChance();
    }
    getCardPlaysetChance() {
        _notImplemented();
    }
}


function _notImplemented() {
    throw new Error('not implemented');
}
