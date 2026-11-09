# Game Data Agent

面向数值策划的桌面工具：从「游戏类型」生成数值框架，推演成长曲线与平衡关系，最后一键导出可用的 Luban 配表。

完全本地运行，不联网、无遥测，数据只在你自己的机器上。

---

## 能做什么

| 模块 | 说明 |
|---|---|
| 框架搭建 | 按游戏类型生成属性、等级、装备、词条、套装、进阶、职业、抽卡、经济、投放等骨架 |
| 工作台 | 汇总当前方案的关键指标，一眼看出成长节奏是否合理 |
| 分析 | 成长曲线、经济收支、投放产出、PVP 平衡、职业对比、进阶收益 |
| 导出 | 生成 16 张 `cfg_*.xlsx`，支持差异预览、写入前备份、调用 luban 出代码与数据 |
| 方案对比 | 多套变体并列比较，参数改动后指标同步刷新 |
| 模型接入 | 可接自定义 LLM，用于生成初始框架或给出调整建议 |

## 快速开始

要求 Python 3.11 以上（开发环境为 3.14）。

```bash
pip install -e ".[core,llm]"
python run.py
```

`run.py` 会先弹出启动屏（logo 旋转 + 进度条），随后拉起主界面。调试时也可以直接：

```bash
python -m app.main
```

## 目录结构

```
app/                 界面层（flet）
  pages/             工作台 / 分析 / 框架编辑 / 导出 / 设置
  splash.py          启动屏：旋转动画、进度条、淡出
core/                业务核心
  schema/            数值模型与表结构定义
  exporter/          生成 xlsx、差异预览、备份、调用 luban
  analysis/          成长节奏、经济、投放平衡等分析
llm/                 模型接入（ccswitch / 自定义接口）
scripts/             23 个自检脚本 + 图标生成
tools/luban/         配表工具链
assets/              图标（png / ico）与启动图
run.py               打包入口：先启动屏，再 flet
```

## 导出的表

```
cfg_Attribute.xlsx       属性定义
cfg_Role_Level.xlsx      角色等级
cfg_Role_Attribute.xlsx  角色属性成长
cfg_Power.xlsx           战力换算
cfg_Profession.xlsx      职业
cfg_EquipSlot.xlsx       装备部位
cfg_EquipQuality.xlsx    装备品质
cfg_Enhance.xlsx         强化
cfg_Affix.xlsx           词条
cfg_EquipSet.xlsx        套装
cfg_Breakthrough.xlsx    突破
cfg_Talent.xlsx          天赋
cfg_Gacha.xlsx           抽卡池
cfg_Economy.xlsx         经济产出与回收
cfg_Investment.xlsx      投放
cfg_Drop.xlsx            掉落
```

导出流程是：**预览差异 → 备份旧表 → 写入新表 →（可选）执行 luban**。没有配置 luban 工程时只产出表格文件。

## 打包

```bash
python -m PyInstaller --noconfirm --windowed --name GameDataAgent ^
  --icon assets/icon.ico ^
  --add-data "assets;assets" ^
  --add-data "build/flet_app/flet-windows.zip;flet_desktop/app" ^
  --collect-all flet --collect-all flet_desktop --collect-all flet_platform_assets ^
  run.py
```

`build/flet_app/flet-windows.zip` 是 flet 桌面客户端（约 43MB），需要先从本机缓存打一次包：

```python
import flet_desktop, os, zipfile

src = flet_desktop.ensure_client_cached()
with zipfile.ZipFile("build/flet_app/flet-windows.zip", "w", zipfile.ZIP_DEFLATED, 6) as z:
    for root, _, files in os.walk(src):
        for name in files:
            if name == ".last-used":
                continue
            full = os.path.join(root, name)
            z.write(full, os.path.relpath(full, src))
```

分发时把整个 `dist/GameDataAgent` 目录一起发出去，`exe` 不能单独拿出来。首次运行会把客户端解压到用户缓存（约 5 秒），之后正常。

## 自检

`scripts/` 下每个 `*_check.py` 都可以单独跑，用来验证对应模块的计算结果：

```bash
python -m scripts.export_check
python -m scripts.growth_check
```

## 数据位置

```
saved/     方案存档
output/    导出的表格
```

两个目录都生成在程序旁边，整个文件夹搬到别处，数据跟着走。

## 说明

- 界面使用 flet 1.x，桌面窗口由内嵌的 Flutter 客户端渲染
- 图标由 `scripts/make_icon.py` 生成（六个镂空菱形 + 中心六芒星），改完重跑即可同时更新 png 与 ico
- 打包版没有代码签名，Windows 首次运行可能提示「未知发布者」
