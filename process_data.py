import pandas as pd
import json

from code.args import args

from code.funcs import *


# --------- Подготовка ----------
# Создание глобальных переменных,
# потребных для работы фильтра
# -------------------------------
with open(args.needed_codes, "r", encoding="utf8") as nc:
    needed_codes = list(map(lambda x: x.strip(), nc.read().strip().split("\n")))


def main():
    if args.preprocess_matches:
        prepare_branches_matches(
            file=args.pp_matches_file,
            output_file=args.vak_codes,
            sheet_name=args.pp_sheet_name,
        )

    VAKcodes_full, new_codes, old_codes = load_vak_codes()

    if args.preprocess_journals:
        data = pd.read_csv(args.pp_journals_file, sep=";")
        data = data.drop(labels=list(data.columns[5:]), axis=1)
        data.Branches = data.Branches.apply(normalize_line)
        data.head()

        data_fin = process_journal_data(data, old_codes, new_codes, VAKcodes_full)

        with open(args.journals_list, "w", encoding="utf8") as jf:
            json.dump(data_fin, jf, ensure_ascii=False)
    else:
        with open(args.journals_list, "r", encoding="utf8") as jf:
            data_fin = json.load(jf)

    VAKsets, VAKwhole = gen_filter_dicts(needed_codes, data_fin, VAKcodes_full)

    with pd.ExcelWriter(args.output_file, engine="xlsxwriter") as writer:
        cell_format = writer.book.add_format({"text_wrap": True})
        opts = {"width": 50, "cell_format": cell_format}

        j_nums = pd.DataFrame(
            {"Код": needed_codes, "Число": [len(VAKsets[k]) for k in needed_codes]}
        )
        j_nums.to_excel(writer, sheet_name="ИТОГО")

        data_filtered = pd_from_dict(data_fin, VAKwhole)
        data_filtered.to_excel(writer, sheet_name="Всего")

        writer.sheets["Всего"].set_column("B:C", **opts)
        writer.sheets["Всего"].set_column("E:F", **opts)

        for k, v in VAKsets.items():
            data_filtered.loc[data_filtered.index.isin(v), :].to_excel(
                writer, sheet_name=k
            )
            writer.sheets[k].set_column("B:C", **opts)
            writer.sheets[k].set_column("E:F", **opts)


if __name__ == "__main__":
    main()
