"""M2 验证：模板模式生成数值框架 + ccswitch 供应商读取。"""

from core.modeling.builder import build_framework
from llm.ccswitch import read_ccswitch_providers


def main() -> None:
    framework = build_framework("苍梧纪", level_cap=60, theme="东方玄幻")
    print(framework.to_json())

    providers = read_ccswitch_providers()
    print(f"\nccswitch 可导入供应商：{len(providers)} 个")
    for provider in providers[:5]:
        print(
            f"  - {provider.name} | {provider.protocol} | "
            f"{provider.model} | {provider.masked_key()}"
        )


if __name__ == "__main__":
    main()
