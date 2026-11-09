"""框架存档验证：保存 / 加载 / 往返一致 / 删除。"""

import tempfile
from pathlib import Path

from core.modeling.builder import build_framework
from core.storage.frameworks import (
    delete_saved,
    list_saved,
    load_framework,
    save_framework,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)

        print("== 保存 ==")
        framework = build_framework("苍梧纪", 60, "东方玄幻", game_type="rpg")
        path = save_framework(framework, directory)
        print(f"  已保存：{path.name}（{path.stat().st_size} 字节）")

        print("\n== 列表 ==")
        files = list_saved(directory)
        print(f"  {len(files)} 个存档：{[item.name for item in files]}")

        print("\n== 加载与往返一致 ==")
        loaded = load_framework(path)
        checks = [
            ("标题", loaded.title == framework.title),
            ("属性数", len(loaded.attributes) == len(framework.attributes)),
            ("等级上限", loaded.level_cap == framework.level_cap),
            (
                "装备部位",
                len(loaded.equipment.slots) == len(framework.equipment.slots),
            ),
            ("抽卡池", len(loaded.gacha) == len(framework.gacha)),
            (
                "投放段",
                len(loaded.investment.bands) == len(framework.investment.bands),
            ),
            (
                "突破点",
                len(loaded.progression.breakthroughs)
                == len(framework.progression.breakthroughs),
            ),
            (
                "经验分段",
                len(loaded.exp_curve.segments)
                == len(framework.exp_curve.segments),
            ),
        ]
        for label, ok in checks:
            print(f"  {label}: {'OK' if ok else 'FAIL'}")
        identical = loaded.model_dump() == framework.model_dump()
        print(f"  完整一致: {'OK' if identical else 'FAIL'}")

        print("\n== 中文不被转义 ==")
        raw = path.read_text(encoding="utf-8")
        print(f"  含「苍梧纪」: {'OK' if '苍梧纪' in raw else 'FAIL'}")

        print("\n== 删除 ==")
        delete_saved(path)
        print(f"  删除后剩余：{len(list_saved(directory))} 个")

        print("\n== 边界 ==")
        print(f"  不存在的目录：{list_saved(directory / 'nope')}")
        delete_saved(path)
        print("  重复删除不报错：OK")


if __name__ == "__main__":
    main()
