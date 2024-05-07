import json
import pandas as pd
import re

from .args import args


RUALPHA = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя()"
TRANS = ("Перевод", "перевод")
TILL = ("по", "По", "до", "До")

SEP = args.sep

# REGEX_TRANS0 = rf"([^{SEP[-1]}])\s+(\([^\)]*(П|п)еревод)"
# REGEX_TRANS1 = rf"([^{SEP[-1]}])\s+(\([^\)]*наименование в Перечне)"
# SUB_TRANS = rf"\1{SEP}\2"
#
# REGEX_CHUNKS = rf"(\([^\)]*){SEP}([^\)]*\))"
# SUB_CHUNKS = r"\1 \2"

REGEX_TRANS0 = rf"([^{SEP}])\s+(\([^\)]*(П|п)еревод)"
REGEX_TRANS1 = rf"([^{SEP}])\s+(\([^\)]*наименование в Перечне)"
SUB_TRANS = rf"\1{SEP}\2"

REGEX_CHUNKS = rf"(\([^\)]*){SEP}([^\)]*\))"
SUB_CHUNKS = r"\1 \2"


def load_vak_codes():
    with open(args.vak_codes, "r", encoding="utf8") as jf:
        VAKcodes_full = json.load(jf)

    new_codes = set()
    old_codes = set()
    for k, v in VAKcodes_full.items():
        for name in v["name"]:
            new_codes.add((k, name))
        for ok, ov in v["old"].items():
            for name in ov:
                old_codes.add((ok, name))

    new_codes = sorted(list(new_codes))
    old_codes = sorted(list(old_codes))

    return VAKcodes_full, new_codes, old_codes


def noempty(x: str, end="") -> str:
    if x != "":
        return x + end
    return ""


def normalize_line(line) -> str:
    if pd.isna(line):
        return ""
    if not isinstance(line, str):
        return str(line)
    res = re.sub(r"\s+,", ", ", line)
    res = re.sub(r"\s\s+", " ", res)
    res = re.sub(r"([^\s])– ", r"\1 – ", res)
    res = re.sub(r" –([^\s])", r" – \1", res)
    res = re.sub(r"–", "-", res)
    return res


def process_branch_line(line: str, rm=False) -> tuple[str, str]:
    line = normalize_line(line)
    if line == "":
        return "", ""
    if line.startswith(tuple("0123456789")):
        chunks = line.split()
        code = chunks[0].strip(".")
        name = " ".join(chunks[1:]).strip("- ")
    else:
        code = ""
        name = line.strip("- ")
    if rm:
        name = re.sub(r" \([^\)]*\)$", "", name)
    return code, name


def prepare_branches_matches(file: str, output_file: str, sheet_name: str):
    data = pd.read_excel(file, sheet_name=sheet_name)
    for col in data.columns:
        data[col] = data[col].apply(normalize_line)
    data.head()

    N, _ = data.shape
    new_cols = [col for col in data.columns if col.startswith("New") and col != "New"]
    old_cols = [col for col in data.columns if col.startswith("Old") and col != "Old"]

    [el for el in list(data.loc[0, new_cols]) if el != ""]

    result = {}

    for i in range(N):
        new_spec, old_spec = data.loc[i, ["New", "Old"]]
        new_specs = [el for el in list(data.loc[i, new_cols]) if el != ""]
        old_specs = [el for el in list(data.loc[i, old_cols]) if el != ""]

        new_code, new_name = process_branch_line(new_spec)

        if new_code not in result:
            new_names = [new_name]
            for spec in new_specs:
                _, new_name = process_branch_line(spec)
                new_names.append(new_name)

            result[new_code] = {"name": new_names, "old": {}}

        old_code, old_name = process_branch_line(old_spec, True)
        if old_code == "":
            continue
        if old_code not in result[new_code]["old"]:
            old_names = [old_name]
            for spec in old_specs:
                _, old_name = process_branch_line(spec)
                old_names.append(old_name)
            result[new_code]["old"][old_code] = old_names

    with open(output_file, "w", encoding="utf8") as jf:
        json.dump(result, jf, ensure_ascii=False)


def process_title_line(title: str) -> tuple[str, str, str]:
    new_title = ""
    new_alttitle = ""
    new_oldtitle = ""

    title = re.sub(REGEX_TRANS0, SUB_TRANS, title)
    title = re.sub(REGEX_TRANS1, SUB_TRANS, title)

    chunks = re.sub(REGEX_CHUNKS, SUB_CHUNKS, title).split(SEP)
    for i in range(len(chunks)):
        if (chunks[i] != "") and (chunks[i][0] == "(") and (chunks[i][-1] == ")"):
            chunks[i] = chunks[i].strip("()")

    new_title = chunks[0]

    for chunk in chunks[1:]:
        if chunk.startswith(TRANS):
            try:
                new_alttitle = chunk.split(":")[1].strip()
            except IndexError:
                try:
                    new_alttitle = chunk.split("Федерации ")[1].strip()
                except IndexError:
                    new_alttitle = "!!!ERROR!!!"
        else:
            new_oldtitle = chunk
    return new_title, new_alttitle, new_oldtitle


def process_entry(
    title, issn, branches, old_codes: list, new_codes: list, vak_codes: dict
) -> dict:
    new_title, new_alttitle, new_oldtitle = process_title_line(title)

    new_issn = "; ".join([el for el in issn.split(SEP) if el != ""])

    new_branches = []
    for dd, bb in branches:
        cur_dates = [None, None]
        for el in dd.split(SEP):
            if el.startswith(("с", "С")):
                cur_dates[0] = el.split()[1]
            elif el.startswith(TILL):
                cur_dates[1] = el.split()[1]
            else:
                cur_dates[0] = dd
        cur_branches = [ss.strip(",") for ss in bb.split(SEP)]
        cur_new_branches = set()
        cur_old_branches = set()
        for cur_branch in cur_branches:
            cur_code, cur_name = process_branch_line(cur_branch, True)
            for new_code, new_name in new_codes:
                if (new_code == cur_code) or (new_name in cur_name):
                    cur_new_branches.add(new_code + ". " + new_name)
                    for old_code, old_names in vak_codes[new_code]["old"].items():
                        for old_name in old_names:
                            cur_old_branches.add(old_code + " - " + old_name)
            for old_code, old_name in old_codes:
                if (old_code == cur_code) or (old_name in cur_name):
                    cur_old_branches.add(old_code + " - " + old_name)
        new_branches.append(
            {
                "dates": cur_dates,
                "new_branches": sorted(list(cur_new_branches)),
                "old_branches": sorted(list(cur_old_branches)),
            }
        )

    return {
        "title": new_title,
        "ISSN": new_issn,
        "alttitle": new_alttitle,
        "oldtitle": new_oldtitle,
        "branches": new_branches,
    }


def process_journal_data(
    data: pd.DataFrame, old_codes: list, new_codes: list, vak_codes: dict
) -> dict:
    data_fin = {}

    cur_no = 0
    new_title = ""
    new_branches: list[tuple[str, str]] = [("", "")]
    new_issn = ""

    N, _ = data.shape

    for i in range(N):
        tmp_no, tmp_title, tmp_issn, tmp_branches, tmp_dates = data.iloc[i, :]

        tmp_title = tmp_title.strip() if not pd.isna(tmp_title) else ""
        tmp_issn = tmp_issn.strip() if not pd.isna(tmp_issn) else ""
        tmp_branches = tmp_branches.strip() if not pd.isna(tmp_branches) else ""

        fst = not pd.isna(tmp_no)

        if fst and (cur_no != 0):
            data_fin[cur_no] = process_entry(
                new_title,
                new_issn,
                new_branches,
                old_codes,
                new_codes,
                vak_codes,
            )

        if fst:
            cur_no = int(tmp_no)
            new_title = tmp_title
            new_issn = tmp_issn
            new_branches = [(tmp_dates, tmp_branches)]
            continue

        if (new_title != "") and (new_title[-1] == "-") and (tmp_title != ""):
            new_title += tmp_title
        elif (new_title != "") and (new_title[-1] == ",") and (tmp_title != ""):
            new_title += " " + tmp_title
        elif tmp_title != "":
            new_title = noempty(new_title, SEP) + tmp_title
        new_issn = noempty(new_issn, SEP) + tmp_issn

        if not pd.isna(tmp_dates):
            new_branches.append((tmp_dates, tmp_branches))
        else:
            prev_dates, prev_branches = new_branches[-1]
            if (prev_branches[-1] == ",") or (
                tmp_branches and tmp_branches[0] in RUALPHA
            ):
                prev_branches += " " + tmp_branches
            elif prev_branches[-1] == "-":
                prev_branches += tmp_branches
            else:
                prev_branches += SEP + tmp_branches
            new_branches[-1] = (prev_dates, prev_branches)

    data_fin[cur_no] = process_entry(
        new_title, new_issn, new_branches, old_codes, new_codes, vak_codes
    )

    return data_fin


def gen_branch_patterns(code: str, codes: dict) -> list[str]:
    patterns = []
    cur_codes = codes[code]

    p_code = re.sub(r"\.", r"\.", code)
    patterns.append(p_code)
    patterns.extend(cur_codes["name"])
    patterns.extend([p_code + r"\s+" + v for v in cur_codes["name"]])
    patterns.extend([p_code + r"\.\s+" + v for v in cur_codes["name"]])
    patterns.extend([p_code + r"\s+-\s+" + v for v in cur_codes["name"]])
    patterns.extend([p_code + r"\.\s+-\s+" + v for v in cur_codes["name"]])

    for k, v in cur_codes["old"].items():
        p_code = re.sub(r"\.", r"\.", k)
        patterns.append(p_code)
        patterns.extend(v)
        patterns.extend([p_code + r"\s+" + vv for vv in v])
        patterns.extend([p_code + r"\.\s+" + vv for vv in v])
        patterns.extend([p_code + r"\s+-\s+" + vv for vv in v])
        patterns.extend([p_code + r"\.\s+-\s+" + vv for vv in v])

    return patterns


def search_for_branch(item: dict, pats: list[str]) -> bool:
    branches = item["branches"]
    for branch in branches:
        if branch["dates"][1] is not None:
            continue
        for br in branch["new_branches"]:
            for pat in pats:
                res = re.search(pat, br)
                if res is not None:
                    return True
        for br in branch["old_branches"]:
            for pat in pats:
                res = re.search(pat, br)
                if res is not None:
                    return True
    return False


def pd_from_dict(jdata: dict, keys: list | None = None) -> pd.DataFrame:
    if keys is None:
        keys = list(jdata.keys())

    result = {}

    for k in keys:
        entry = {}
        cur_item = jdata[k]
        entry["Название"] = cur_item["title"]
        entry["Название (перевод)"] = cur_item["alttitle"]
        entry["ISSN"] = cur_item["ISSN"]

        br_str = ""
        for br in cur_item["branches"]:
            if br["dates"][1] is not None:
                continue
            br_str = noempty(br_str, "\n") + "\n".join(br["new_branches"])
        entry["Специальности (новые)"] = br_str

        br_str = ""
        for br in cur_item["branches"]:
            if br["dates"][1] is not None:
                continue
            br_str = noempty(br_str, "\n") + "\n".join(br["old_branches"])
        entry["Специальности (старые)"] = br_str

        result[k] = entry
    return pd.DataFrame.from_dict(result, orient="index")


def gen_filter_dicts(needed_codes: list, journals: dict, vak_codes: dict):
    VAKsets = {}
    VAKpatterns = {}

    for k in needed_codes:
        VAKsets[k] = []
        VAKpatterns[k] = gen_branch_patterns(k, vak_codes)

    for jk, jv in journals.items():
        for k in needed_codes:
            if search_for_branch(jv, VAKpatterns[k]):
                VAKsets[k].append(jk)

    VAKwhole = set()
    for k, v in VAKsets.items():
        print(f"{k}: {len(v)}")
        VAKwhole.update(v)

    VAKwhole = sorted(list(VAKwhole))
    print(f"Всего: {len(VAKwhole)}")

    return VAKsets, VAKwhole
