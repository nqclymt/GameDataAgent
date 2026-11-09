"""M4 验证：方案 A（独立输出）与方案 C（写入工程 + luban 导出）。"""

import shutil
from pathlib import Path

from core.exporter.config import ExportConfig
from core.exporter.service import export_framework
from core.modeling.builder import build_framework

USER_PROJECT = Path(r"E:\MyUnityProject\SwordCultivationClientByTE6\Configs\GameConfig")
TEST_PROJECT = Path("tools/m4_test_project")


def main() -> None:
    framework = build_framework("苍梧纪", level_cap=60)

    cfg_a = ExportConfig()
    result_a = export_framework(framework, cfg_a)
    print(f"[A] 写入 {len(result_a.files)} 个文件 -> {cfg_a.datas_dir()}")
    print(f"[A] luban 调用: {'无（未设置工程）' if result_a.code_dir is None else '有'}")

    _prepare_test_project()
    cfg_c = ExportConfig(project_dir=TEST_PROJECT, backup_dir=TEST_PROJECT / "backup")
    result_c = export_framework(framework, cfg_c)
    print(f"[C] 写入 {len(result_c.files)} 个文件 -> {cfg_c.datas_dir()}")
    print(f"[C] 代码输出 -> {result_c.code_dir}")
    print(f"[C] 数据输出 -> {result_c.data_dir}")
    assert (result_c.code_dir / "role" / "TbAttr.cs").exists(), "缺少 TbAttr.cs"
    assert (result_c.data_dir / "role_tbattr.bytes").exists(), "缺少 role_tbattr.bytes"
    print("[C] 产物校验通过")

    export_framework(framework, cfg_c)
    backups = list(cfg_c.backup_dir.glob("*.xlsx"))
    assert backups, "重复导出未产生备份"
    print(f"[C] 备份校验通过：{len(backups)} 个文件 -> {cfg_c.backup_dir}")


def _prepare_test_project() -> None:
    if TEST_PROJECT.exists():
        shutil.rmtree(TEST_PROJECT)
    (TEST_PROJECT / "Defines").mkdir(parents=True)
    (TEST_PROJECT / "Datas").mkdir(parents=True)
    shutil.copy2(USER_PROJECT / "Defines" / "builtin.xml", TEST_PROJECT / "Defines")
    for name in ("__beans__.xlsx", "__enums__.xlsx"):
        shutil.copy2(USER_PROJECT / "Datas" / name, TEST_PROJECT / "Datas")
    shutil.copy2(USER_PROJECT / "luban.conf", TEST_PROJECT)


if __name__ == "__main__":
    main()
