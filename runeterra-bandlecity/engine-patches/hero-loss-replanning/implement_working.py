"""Apply the bounded fifth patch to the owned, reconstructed working source only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'ai-turn-lifecycle' / 'src'
BASE = ROOT.parent / 'ai-turn-lifecycle' / 'src-reproduced-final'

def edit(name, before, after):
    path = SRC / name
    data = path.read_bytes()
    old = before.replace('\n', '\r\n').encode()
    new = after.replace('\n', '\r\n').encode()
    assert data.count(old) == 1, (name, data.count(old))
    snapshot = ROOT / 'baseline' / name
    if not snapshot.exists():
        baseline = BASE / name
        assert baseline.read_bytes() == data, name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(data)
    path.write_bytes(data.replace(old, new))

edit('AI/Nullkiller2/AIGateway.h',
     '\tstd::map<ObjectInstanceID, TryMoveHero> lastMovementResults;',
     '\tstd::map<ObjectInstanceID, TryMoveHero> lastMovementResults;\n'
     '\tstd::map<ObjectInstanceID, std::pair<uint64_t, bool>> battleLosses;')
edit('AI/Nullkiller2/AIGateway.h',
     '\tvoid clearLastMovementResult(ObjectInstanceID heroID);',
     '\tvoid recordBattleLoss(ObjectInstanceID heroID);\n'
     '\tvoid recordHeroRemoval(ObjectInstanceID heroID);\n'
     '\tuint64_t battleLossSequence(ObjectInstanceID heroID);\n'
     '\tbool wasRemovedAfterBattleLoss(ObjectInstanceID heroID, uint64_t origin);\n'
     '\tvoid clearLastMovementResult(ObjectInstanceID heroID);')
edit('AI/Nullkiller2/AIGateway.cpp',
     '\t\tlostHero(HeroPtr(cc->getHero(obj->id), cc.get()));',
     '\t\tstatus.recordHeroRemoval(obj->id);\n\t\tlostHero(HeroPtr(cc->getHero(obj->id), cc.get()));')
edit('AI/Nullkiller2/AIGateway.cpp',
     '\tbool won = br->winner == cc->getBattle(battleID)->battleGetMySide();',
     '\tconst auto battle = cc->getBattle(battleID);\n'
     '\tbool won = br->winner == battle->battleGetMySide();\n'
     '\tconst auto * hero = battle->battleGetMyHero();\n'
     '\tif(!won && br->result == EBattleResult::NORMAL && hero && hero->getOwner() == playerID)\n'
     '\t\tstatus.recordBattleLoss(hero->id);')
edit('AI/Nullkiller2/AIGateway.cpp',
     '\tif(heroPtr->isGarrisoned() && heroPtr->getVisitedTown())',
     '\tconst auto movingHeroID = heroPtr->id;\n'
     '\tconst bool ownedAtStart = heroPtr->getOwner() == playerID;\n'
     '\tconst auto battleLossOrigin = status.battleLossSequence(movingHeroID);\n\n'
     '\tif(heroPtr->isGarrisoned() && heroPtr->getVisitedTown())')
edit('AI/Nullkiller2/AIGateway.cpp',
     '\t\t\t\tstatus.setChannelProbing(false);\n\t\t\tthrow cannotFulfillGoalException("Hero was lost!");',
     '\t\t\t\tstatus.setChannelProbing(false);\n'
     '\t\t\tif(ownedAtStart && status.wasRemovedAfterBattleLoss(movingHeroID, battleLossOrigin))\n'
     '\t\t\t\tthrow heroLostInBattleException(movingHeroID);\n'
     '\t\t\tthrow cannotFulfillGoalException("Hero was lost!");')
edit('AI/Nullkiller2/AIGateway.cpp',
     'void AIStatus::clearLastMovementResult(ObjectInstanceID heroID)',
     'void AIStatus::recordBattleLoss(ObjectInstanceID heroID)\n'
     '{\n\tstd::unique_lock<std::mutex> lock(mx);\n'
     '\tauto & loss = battleLosses[heroID];\n\t++loss.first;\n\tloss.second = false;\n}\n\n'
     'void AIStatus::recordHeroRemoval(ObjectInstanceID heroID)\n'
     '{\n\tstd::unique_lock<std::mutex> lock(mx);\n'
     '\tauto loss = battleLosses.find(heroID);\n'
     '\tif(loss != battleLosses.end())\n\t\tloss->second.second = true;\n}\n\n'
     'uint64_t AIStatus::battleLossSequence(ObjectInstanceID heroID)\n'
     '{\n\tstd::unique_lock<std::mutex> lock(mx);\n'
     '\tauto loss = battleLosses.find(heroID);\n'
     '\treturn loss == battleLosses.end() ? 0 : loss->second.first;\n}\n\n'
     'bool AIStatus::wasRemovedAfterBattleLoss(ObjectInstanceID heroID, uint64_t origin)\n'
     '{\n\tstd::unique_lock<std::mutex> lock(mx);\n'
     '\tauto loss = battleLosses.find(heroID);\n'
     '\treturn loss != battleLosses.end() && loss->second.first > origin && loss->second.second;\n}\n\n'
     'void AIStatus::clearLastMovementResult(ObjectInstanceID heroID)')
edit('AI/Nullkiller2/Goals/AbstractGoal.h',
     'class cannotFulfillGoalException : public std::exception',
     'class heroLostInBattleException : public std::exception\n'
     '{\npublic:\n\tconst ObjectInstanceID heroID;\n'
     '\texplicit heroLostInBattleException(ObjectInstanceID heroID) : heroID(heroID) {}\n'
     '\tconst char * what() const noexcept override { return "Moving hero defeated in battle."; }\n};\n\n'
     'class cannotFulfillGoalException : public std::exception')
edit('AI/Nullkiller2/Engine/Nullkiller.cpp',
     '\tcatch(cannotFulfillGoalException & e)',
     '\tcatch(const heroLostInBattleException & e)\n'
     '\t{\n\t\tlastTaskFailureHadPath = rememberActivePathFailure();\n'
     '\t\tinvalidatePathfinderData();\n'
     '\t\tlogAi->info("Hero %d defeated in battle; cancelling its task and replanning.", e.heroID.getNum());\n'
     '\t\treturn false;\n\t}\n'
     '\tcatch(cannotFulfillGoalException & e)')
print('Applied fifth patch only to owned working source.')
