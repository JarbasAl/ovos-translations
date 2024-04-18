import os
import shutil
import subprocess

from ovos_utils import flatten_list
from ovos_utils.bracket_expansion import expand_options

README_TEMPLATE = """
url: {url}

repo_id: {skill_id}

TOTAL_STRINGS:  - string count from all resource files

TOTAL_STRINGS_EXPANDED: - same as above, but each line is expanded, eg, 'test (a|b)' -> ['test a', 'test b']

TOTAL_INTENTS: - intent files for padatious engine (STT transcriptions)

TOTAL_VOCABS: - intent files for adapt engine or self.voc_match (STT keywords)

TOTAL_DIALOGS: - spoken TTS responses


# String Counts

reference language: en-us

TOTAL_STRINGS: {n_total_unexpanded}  

TOTAL_STRINGS_EXPANDED: {n_total_expanded}  

TOTAL_INTENTS: {n_intents}  

TOTAL_VOCABS: {n_vocs}  

TOTAL_DIALOGS: {n_dialogs}  

# Supported Languages

{langs}
"""

TOTAL_INTENTS = 0
TOTAL_DIALOGS = 0
TOTAL_VOCS = 0

TOTAL_UNEXPANDED = 0
TOTAL_EXPANDED = 0
LANGS = []


def get_lang_counts(locale_f, lang="en-us"):
    n_intents = 0
    n_dialogs = 0
    n_vocs = 0

    n_total_unexpanded = 0
    n_total_expanded = 0

    langs = os.listdir(locale_f)
    for root, _, files in os.walk(f"{locale_f}/{lang}"):
        for f in files:
            if not any(f.endswith(x) for x in [".dialog", ".voc", ".intent"]):
                continue
            if f.endswith(".dialog"):
                n_dialogs += 1
            if f.endswith(".intent"):
                n_intents += 1
            if f.endswith(".voc"):
                n_vocs += 1
            with open(f"{root}/{f}") as fi:
                lines = fi.read().split("\n")
                lines = [l for l in lines if not l.startswith("#") and l.strip()]
                expanded = flatten_list([expand_options(l) for l in lines])
                n_total_expanded += len(expanded)
                n_total_unexpanded += len(lines)
    return langs, n_intents, n_vocs, n_dialogs, n_total_expanded, n_total_unexpanded


def collect_locales():
    global TOTAL_UNEXPANDED, TOTAL_INTENTS, TOTAL_EXPANDED, TOTAL_DIALOGS, TOTAL_VOCS, LANGS
    clone_folder = "/tmp/ovos_clones"
    os.makedirs(clone_folder, exist_ok=True)

    with open("official_skills.txt") as f:
        for url in f.read().split("\n"):
            if not url.startswith("http"):
                continue
            p = url.split("/")
            repo = p[-1]
            author = p[-2]
            repo_id = f"{repo}.{author}".lower().replace("skill-ovos",
                                                         "ovos-skill")
            print(url, repo_id)

            if not os.path.isdir(f"{clone_folder}/{repo_id}"):
                subprocess.call(f"git clone {url} {clone_folder}/{repo_id}", shell=True)

            for r, _, _ in os.walk(f"{clone_folder}/{repo_id}"):
                if r.endswith("/locale"):
                    locale_f = r
                    break
            else:
                locale_f = f"{clone_folder}/{repo_id}/locale"

            tx_base = f"{os.path.dirname(__file__)}/{repo_id}"

            if os.path.isdir(locale_f):
                shutil.move(locale_f, f"{tx_base}/locale")

            langs, n_intents, n_vocs, n_dialogs, n_total_expanded, n_total_unexpanded = get_lang_counts(
                f"{tx_base}/locale")
            TOTAL_VOCS += n_vocs
            TOTAL_DIALOGS += n_dialogs
            TOTAL_INTENTS += n_intents
            TOTAL_EXPANDED += n_total_expanded
            TOTAL_UNEXPANDED += n_total_unexpanded
            LANGS += langs
            with open(f"{tx_base}/README.md", "w") as f:
                f.write(README_TEMPLATE.format(skill_id=repo_id,
                                               url=url,
                                               langs="\n".join(langs),
                                               n_vocs=n_vocs,
                                               n_dialogs=n_dialogs,
                                               n_total_unexpanded=n_total_unexpanded,
                                               n_total_expanded=n_total_expanded,
                                               n_intents=n_intents))


def collect_core():
    blacklist = ["mycroft", "test"]
    clone_folder = "/tmp/ovos_clones"
    os.makedirs(clone_folder, exist_ok=True)

    with open("core_repos.txt") as f:
        for url in f.read().split("\n"):
            if not url.startswith("http"):
                continue
            p = url.split("/")
            repo = p[-1]
            repo_id = repo.lower()
            print(url, repo_id)

            if not os.path.isdir(f"{clone_folder}/{repo_id}"):
                subprocess.call(f"git clone {url} {clone_folder}/{repo_id}", shell=True)

            for r, _, _ in os.walk(f"{clone_folder}/{repo_id}"):
                if any(s in r for s in blacklist):
                    continue
                if r.endswith("/locale"):
                    locale_f = r
                    break
            else:
                locale_f = f"{clone_folder}/{repo_id}/locale"

            tx_base = f"{os.path.dirname(__file__)}/{repo_id}/"

            if os.path.isdir(locale_f):
                print(locale_f)
                shutil.move(locale_f, f"{tx_base}/locale")

            langs, n_intents, n_vocs, n_dialogs, n_total_expanded, n_total_unexpanded = get_lang_counts(
                f"{tx_base}/locale")

            with open(f"{tx_base}/README.md", "w") as f:
                f.write(README_TEMPLATE.format(skill_id=repo_id,
                                               url=url,
                                               langs="\n".join(langs),
                                               n_vocs=n_vocs,
                                               n_dialogs=n_dialogs,
                                               n_total_unexpanded=n_total_unexpanded,
                                               n_total_expanded=n_total_expanded,
                                               n_intents=n_intents))


collect_locales()
collect_core()

with open(f"{os.path.dirname(__file__)}/README.md", "w") as f:
    f.write(README_TEMPLATE.format(skill_id="ovos-translations",
                                   url="https://github.com/JarbasAl/ovos-translations",
                                   langs="\n".join(LANGS),
                                   n_vocs=TOTAL_VOCS,
                                   n_dialogs=TOTAL_DIALOGS,
                                   n_total_unexpanded=TOTAL_UNEXPANDED,
                                   n_total_expanded=TOTAL_EXPANDED,
                                   n_intents=TOTAL_INTENTS))
