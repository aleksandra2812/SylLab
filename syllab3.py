import os
import re

#Francuski akcent, bo w jednym wierszu od Ani było stosowane takie e
VOWELS = "aąeęiouyóéAĄEĘIOUYÓÉ"

DIGRAPHS = [
    "ch", "cz", "dz", "dź", "dż", "rz", "sz",
    "Ch", "Cz", "Dz", "Dź", "Dż", "Rz", "Sz"
]

# Stoplista do akcentowania - na ten moment tylko jednoliterowe przyimki i spójniki, się, oraz nie
NEVER_STRESS = {
    "w", "z", "i", "a", "o", "się", "nie"
}


def vowel(letter):
    return letter in VOWELS

def join_monographs(text):
    # połączenia przyimków - jeżeli występuje połączenie "w domu", "z łąki", to sylabifikacja będzie wyglądać tak: wdo-mu, złąki
    text = re.sub(r'\b([wzWZ])\s+', r'\1', text)
    return text

def tokenization(word):
    units = []
    i = 0
    while i < len(word):
        matched = False
        for d in DIGRAPHS:
            if word[i:i+len(d)] == d:
                units.append(d)
                i += len(d)
                matched = True
                break
        if not matched:
            units.append(word[i])
            i += 1
    return units

# Sylabizacja - mamy tu typowe zasady z akcentem paroksytonicznym, jest jeszcze kilka mniejszych zasad, które warto byłoby dodać, ale czasem ich implementacja mnie przerastała, np. różnica między "dawać na mszę" oraz "iść na mszę", gdzie to semantyka wpływa na akcentowanie - mogę zrobić na następne spotkanie listę takich zasad do zastanowienia, czy da się to w ogóle jakkolwiek wprowadzić

def split_into_syllables(word):
    units = tokenization(word)
    syllables = []
    current = []

    i = 0
    while i < len(units):
        current.append(units[i])

        if vowel(units[i][0]):

            # wykryj "i" jako zmiękczenie - jeżeli po "i" występuje samogłoska, to nie jest ono ośrodkiem sylaby
            if units[i].lower() == "i":
                if i + 1 < len(units) and vowel(units[i + 1][0]):
                    i += 1
                    continue

            j = i + 1
            cluster = []

            while j < len(units) and not vowel(units[j][0]):
                cluster.append(units[j])
                j += 1

            # Zapobieganie dzielenia na wyłącznie sylaby otwarte - tutaj można się zastanowić, czy nie wprowadzić jeszcze jakichś funkcji z zasadą sonorności i pierwszeństwa nagłosu, ale za każdym razem, jak próbowałam wcześniej, to właśnie nie umiałam tego zrobić tak, żeby na siłę nie były sylaby otwarte wymuszane
            if j >= len(units):
                current.extend(cluster)
                syllables.append("".join(current))
                return syllables

            if len(cluster) == 0:
                syllables.append("".join(current))
                current = []

            elif len(cluster) == 1:
                syllables.append("".join(current))
                current = []

            else:
                syllables.append("".join(current + cluster[:-1]))
                current = []
                i = j - len(cluster) + len(cluster[:-1]) - 1

        i += 1

    if current:
        syllables.append("".join(current))

    return syllables

def penultimate_stress(word, syllables):
    n = len(syllables)
    pattern = ["s"] * n
    word_lower = word.lower()

    if word_lower in NEVER_STRESS:
        return pattern

    if n == 1:
        pattern[0] = "S"
        return pattern

    penultimate = n - 2
    pattern[penultimate] = "S"

    i = penultimate - 2
    while i >= 0:
        pattern[i] = "(S)"
        i -= 2

    return pattern

def multiple_monosyllables(chain):
    results = []
    lexical_counter = 0

    for word, syllables in chain:
        word_lower = word.lower()
        pattern = ["s"]

        if word_lower not in NEVER_STRESS:
            if lexical_counter % 2 == 0:
                pattern = ["S"]
            lexical_counter += 1

        results.append(pattern)

    return results


def mark_stress_in_line(words_data):
    stress_results = []
    monosyllable_chain = []

    for word, syllables in words_data:

        if syllables is None:
            stress_results.append(None)
            continue

        if len(syllables) == 1:
            monosyllable_chain.append((word, syllables))
        else:
            if monosyllable_chain:
                stress_results.extend(
                    multiple_monosyllables(monosyllable_chain)
                )
                monosyllable_chain = []

            stress_results.append(
                penultimate_stress(word, syllables)
            )

    if monosyllable_chain:
        stress_results.extend(
            multiple_monosyllables(monosyllable_chain)
        )

    return stress_results


def highlight_stress(syllables, stress_pattern):
    result = []
    for syl, st in zip(syllables, stress_pattern):
        if st == "S":
            result.append(syl.upper())
        elif st == "(S)":
            result.append(f"({syl})")
        else:
            result.append(syl)
    return "-".join(result)

def process_text(text):

    text = join_monographs(text)
    text = text.lower()

    syllable_text = []
    stress_text = []
    highlight_text = []

    lines = text.split("\n")

    for line in lines:

        tokens = re.findall(r'\w+|[^\w\s]', line, re.UNICODE)

        words_data = []
        for token in tokens:
            if re.match(r'\w+', token):
                syllables = split_into_syllables(token)
                words_data.append((token, syllables))
            else:
                words_data.append((token, None))

        stress_patterns = mark_stress_in_line(words_data)

        syll_line = []
        stress_line = []
        highlight_line = []

        for (token, syllables), stress_pattern in zip(words_data, stress_patterns):

            if syllables is None:
                syll_line.append(token)
                highlight_line.append(token)
            else:
                syll_line.append("-".join(syllables))

                if stress_pattern is not None:
                    stress_line.append(" ".join(stress_pattern))
                    highlight_line.append(
                        highlight_stress(syllables, stress_pattern)
                    )
                else:
                    stress_line.append("")
                    highlight_line.append("-".join(syllables))

        syllable_text.append(" ".join(syll_line))
        stress_text.append(" | ".join(p for p in stress_line if p))
        highlight_text.append(" ".join(highlight_line))

    return (
        "\n".join(syllable_text),
        "\n".join(stress_text),
        "\n".join(highlight_text),
    )

# Tutaj też jest łopatologicznie - przetwarzam sobie pliki po folderach, potem zwykły podział na sylaby dostaje rozszerzenie _syllables, podział z akcentowanymi sylabami CAPSLOCKIEM _highlighted, a plik _stress pokazuje akcengtowaną sylabę jako duże S, nieakcentowaną jako małe s, mam też osobny skrypt do zamieniania tych szeregów "Sss" na liczby "100"

def process_folder(folder_path):

    for filename in os.listdir(folder_path):

        if filename.endswith(".txt"):

            full_path = os.path.join(folder_path, filename)

            with open(full_path, "r", encoding="utf-8") as f:
                text = f.read()

            syll, stress, highlight = process_text(text)

            base = os.path.splitext(full_path)[0]

            with open(base + "_syllables.txt", "w", encoding="utf-8") as f:
                f.write(syll)

            with open(base + "_stress.txt", "w", encoding="utf-8") as f:
                f.write(stress)

            with open(base + "_highlighted.txt", "w", encoding="utf-8") as f:
                f.write(highlight)

            print(f"Done: {filename}")

    print("\n Wszystko zanalizowane.")


if __name__ == "__main__":

    folder = input("Podaj ścieżkę do folderu: ").strip()

    if not os.path.isdir(folder):
        print("Ups. Zła ścieżka.")
    else:
        process_folder(folder)