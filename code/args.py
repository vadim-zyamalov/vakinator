import argparse


parser = argparse.ArgumentParser(description="Фильтр журналов ВАК")

parser.add_argument(
    "-j",
    "--journals",
    dest="journals_list",
    type=str,
    default="json/VAK.json",
    help="Список журналов",
)
parser.add_argument(
    "-o",
    "--output",
    dest="output_file",
    type=str,
    default="Результат.xlsx",
    help="Итоговый файл (xlsx)",
)
parser.add_argument(
    "-v",
    "--vak",
    dest="vak_codes",
    type=str,
    default="json/VAK_codes_match_full.json",
    help="JSON со списком соотвестсвия старых и новых шифров специальностей",
)
parser.add_argument(
    "-c",
    "--codes",
    dest="needed_codes",
    type=str,
    default="needed_codes.txt",
    help="Список интересующих нас шифров",
)
parser.add_argument(
    "-s",
    "--sep",
    dest="sep",
    type=str,
    default="\n",
    help="Разделитель строк в ячейке",
)
parser.add_argument(
    "-ppm",
    "--preprocess_matches",
    dest="preprocess_matches",
    action="store_true",
    help="Нужна ли предварительная подготовка кодов соответствия",
)
parser.add_argument(
    "-ppmf",
    "--preprocess_matches_file",
    dest="pp_matches_file",
    type=str,
    default="raw/Соответствие ВАК.xlsx",
    help="Соответствие новых и старых специальностей (ExcelX)",
)
parser.add_argument(
    "-ppms",
    "--preprocess_matches_sheet",
    dest="pp_sheet_name",
    type=str,
    default="Full Match",
    help="Имя листа с соответствием",
)
parser.add_argument(
    "-ppj",
    "--preprocess_journals",
    dest="preprocess_journals",
    action="store_true",
    help="Нужна ли предварительная подготовка списка журналов",
)
parser.add_argument(
    "-ppjf",
    "--preprocess_journals_file",
    dest="pp_journals_file",
    type=str,
    default="raw/Перечень ВАК ред.csv",
    help="Список журналов",
)

args = parser.parse_args()
