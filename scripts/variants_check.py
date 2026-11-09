"""方案持久化验证：保存 / 重载 / 删除 / 损坏容错。"""

import tempfile
from pathlib import Path

from core.modeling.builder import build_framework
from core.storage.variants import (
    delete_variant,
    load_variants,
    save_variant,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)

        print("== 保存两个方案 ==")
        plan_a = build_framework("方案A", 60, game_type="rpg")
        plan_b = build_framework("方案B", 40, game_type="card")
        path_a = save_variant("方案A", plan_a, directory)
        save_variant("方案B", plan_b, directory)
        print(f"  {path_a.name} / 方案B.json")

        print("\n== 重载（模拟重启）==")
        loaded = load_variants(directory)
        print(f"  加载 {len(loaded)} 个方案：{sorted(loaded)}")
        for name, framework in sorted(loaded.items()):
            print(
                f"    {name}: {framework.level_cap} 级 / "
                f"{len(framework.attributes)} 属性 / "
                f"{len(framework.equipment.affixes)} 条词条"
            )

        print("\n== 同名覆盖 ==")
        plan_a2 = build_framework("方案A", 30, game_type="rpg")
        save_variant("方案A", plan_a2, directory)
        reloaded = load_variants(directory)
        print(
            f"  方案A 等级上限：{reloaded['方案A'].level_cap}"
            f"（应为 30）"
        )

        print("\n== 删除 ==")
        delete_variant("方案B", directory)
        print(f"  剩余：{sorted(load_variants(directory))}")

        print("\n== 损坏文件容错 ==")
        bad = directory / "坏方案.json"
        bad.write_text("{ 这不是合法 JSON", encoding="utf-8")
        survivors = load_variants(directory)
        print(f"  跳过损坏文件后：{sorted(survivors)}")

        print("\n== 边界 ==")
        print(f"  不存在的目录：{load_variants(directory / 'nope')}")
        delete_variant("不存在", directory)
        print("  删除不存在的方案不报错：OK")


if __name__ == "__main__":
    main()
