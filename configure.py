import json
from pathlib import Path


def main():
    template_path = Path(__file__).with_name("config_template.json")
    with template_path.open(encoding="utf-8") as template:
        settings = json.load(template)

    created_config = {}
    for item in settings["config-items"]:
        options = item["available"]
        print(f"Choose a {item['name']}.")
        for number, option in enumerate(options, start=1):
            print(f"  {number}. {option['name']} {option['warning']}".rstrip())
        while True:
            choice = input(f"Enter a number from 1 to {len(options)}: ").strip()
            if choice in {str(number) for number in range(1, len(options) + 1)}:
                break
            print("Please choose one of the numbers in the list.")

        chosen = options[int(choice) - 1]
        print(f"\nYou chose {chosen['name']}. {chosen['notice']}\n")
        created_config[item["name"]] = chosen["name"]
        for option in chosen["module-specific-config"]:
            created_config[option["name"]] = option["value"]

    config_path = Path("local-config.json")
    config_path.write_text(json.dumps(created_config, indent=4) + "\n", encoding="utf-8")
    print(f"Saved your settings to {config_path}.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nSetup cancelled.") from None
