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
    if args.preprocess:
        prepare_branches_matches(
            file=args.pp_file,
            output_file=args.vak_codes,
            sheet_name=args.pp_sheet_name,
        )

        VAKcodes_full, new_codes, old_codes = load_vak_codes()

        data = pd.read_csv(args.journals_list, sep=";")
        data = data.drop([f"Unnamed: {i}" for i in range(5, 11)], axis=1)
        data.Branches = data.Branches.apply(normalize_line)
        data.head()

        data_fin = process_journal_data(
            data, old_codes, new_codes, VAKcodes_full
        )

        with open(args.pp_journals, "w", encoding="utf8") as jf:
            json.dump(data_fin, jf, ensure_ascii=False)

    else:
        VAKcodes_full, new_codes, old_codes = load_vak_codes()

        with open(args.pp_journals, "r", encoding="utf8") as jf:
            data_fin = json.load(jf)

    # %%
    VAKsets, VAKwhole = gen_filter_dicts(needed_codes, data_fin, VAKcodes_full)

    # %%
    with pd.ExcelWriter(args.output_file, engine="xlsxwriter") as writer:
        cell_format = writer.book.add_format({"text_wrap": True})
        opts = {"width": 50, "cell_format": cell_format}

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
