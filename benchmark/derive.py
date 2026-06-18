#!/usr/bin/env python3
"""Verified derivation: turn a modern European-Portuguese sentence into all five norms.

Correct by construction. A word is transformed only via a *verified* per-word map (built
from the QA'd corpus + tugalex + the curated lexicons) or a deterministic rule (nasal
vowel, trema membership, month casing). If a sentence contains a word that *could* vary
orthographically but is NOT covered, or a context-ambiguous differential word, the
sentence is rejected (returns None) — so a derived sentence can never be wrong.

    from derive import build_maps, derive
    M = build_maps()
    cells = derive("O diretor aprovou a coleção em janeiro.", M)   # -> dict or None
"""
from __future__ import annotations

import json
import os
import re

from desacordo_ortografico import rules
from desacordo_ortografico.lexicon import get_lexicon

HERE = os.path.dirname(os.path.abspath(__file__))
_TOK = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")
_CP = ("cç", "ct", "pç", "pt", "pc")               # silent-consonant clusters
_DIFFERENTIAL = {"para", "pára", "pelo", "pêlo", "polo", "pólo", "pera", "pêra",
                 "pera", "coa", "côa"}              # context-ambiguous -> reject
_EEM = {"leem": "lêem", "creem": "crêem", "veem": "vêem", "deem": "dêem",
        "releem": "relêem", "preveem": "prevêem", "reveem": "revêem"}
# Modern reflexes of a possibly-silent European c/p (-cção/-pção -> -ção; -ct-/-pt- -> -t-).
# A word matching one of these but not in the verified map could hide a dropped consonant
# (antárctica->antártica, restrictivas->restritivas), so it is rejected unless verified.
_RISK = re.compile(r"(ç[ãõ]o|ç[õo]es|t[oa]r|t[oa]res|tiv[oa]s?|átic[oa]s?|étic[oa]s?|"
                   r"ártic[oa]s?|ânic[oa]s?|ítim[oa]s?)$", re.I)
_RISK_VT = re.compile(r"[ae]t[oa]s?$", re.I)   # -eto/-ato: Latinate only when long (>=6)


class Maps:
    def __init__(self):
        self.pt = {}   # ao1990-pt word -> (pt_1973, etymological)
        self.br = {}   # ao1990-br word -> br_1971
        self.lex = get_lexicon()
        self.keep = self.lex.cp_keep_pt          # c/p pronounced (kept) in PT
        self.voiced_u = self.lex.voiced_u_words if hasattr(self.lex, "voiced_u_words") else set()


def _align_line(cells, cols):
    """Yield (target_word, *source_words) tuples when the cells share a token count."""
    toks = [_TOK.findall(cells[c]) for c in cols]
    if len({len(t) for t in toks}) != 1:
        return
    for i in range(len(toks[0])):
        yield tuple(toks[j][i] for j in range(len(cols)))


def build_maps():
    M = Maps()
    # 1) verified word forms straight from the QA'd corpus
    for line in open(os.path.join(HERE, "gold_corpus.jsonl"), encoding="utf-8"):
        if not line.strip():
            continue
        c = json.loads(line)["cells"]
        for ao, pt, et in _align_line(c, ["ao1990-pt", "pt_1973", "etymological"]):
            M.pt.setdefault(ao.lower(), (pt.lower(), et.lower()))
        for ao, br in _align_line(c, ["ao1990-br", "br_1971"]):
            M.br.setdefault(ao.lower(), br.lower())
    # 2) augment from tugalex + curated lexicons (modern -> older)
    lex = M.lex
    for new, old in lex.ao_pt_new2old.items():       # ação -> acção (pt_1973)
        M.pt.setdefault(new, (old, lex.reform1911_new2old.get(new, old)))
    for new, old in lex.reform1911_new2old.items():  # farmácia -> pharmacia (etym)
        if new in M.pt:
            pt73 = M.pt[new][0]
            M.pt[new] = (pt73, old)
        else:
            M.pt.setdefault(new, (new, old))
    for new, old in lex.ao_br_new2old.items():        # ideia -> idéia (br_1971)
        M.br.setdefault(new, old)
    # 3) verified at-risk vocabulary (pt_1973/etymological per word) + Brazilian trema
    #    words, classified once by an LLM panel and consolidated into a committed lexicon
    lex_path = os.path.join(HERE, "derived_lexicon.json")
    if os.path.exists(lex_path):
        dl = json.load(open(lex_path, encoding="utf-8"))
        for w, (pt73, et) in dl["pt"].items():
            M.pt[w] = (pt73, et)
        for w, br in dl["br"].items():
            M.br[w] = br
    return M


def _case(form, like):
    if like.isupper() and len(like) > 1:
        return form.upper()
    if like[:1].isupper():
        return form[:1].upper() + form[1:]
    return form


def _varying(word, M):
    """The word's spelling could change across some norm pair (excluding the always-safe
    deterministic nasal-vowel and month transforms)."""
    w = word.lower()
    lex = M.lex
    return (any(c in w for c in _CP) or w in _DIFFERENTIAL or w in M.voiced_u
            or w in lex.dual_pt2br or w in lex.dual_br2pt
            or w in lex.divergence_pt2br or w in lex.divergence_br2pt
            or w in lex.ao_pt_new2old or w in lex.ao_br_new2old)


def _covered(word, M):
    """A varying word is safe only if every norm form is verified."""
    w = word.lower()
    if w in _DIFFERENTIAL:
        return False                                 # verb/prep ambiguity -> reject
    if w not in M.pt and w not in M.keep and (
            _RISK.search(w) or (len(w) >= 6 and _RISK_VT.search(w))):
        return False                                 # could hide a dropped c/p -> reject
    if not _varying(w, M):
        return True                                  # invariant (nasal/months are safe)
    if w not in M.pt:
        return False                                 # no verified PT-line forms
    br_form = M.lex.dual_pt2br.get(w) or M.lex.divergence_pt2br.get(w) \
        or rules.nasal_vowel_to_br(w)
    if (w in M.voiced_u or w in M.lex.ao_br_new2old) and br_form not in M.br:
        return False                                 # trema/diphthong form not verified
    return True


def derive(sentence, M):
    sentence = sentence.strip()
    words = _TOK.findall(sentence)
    if not words or not all(_covered(w, M) for w in words):
        return None

    def map_pt(m):
        w = m.group(0)
        e = M.pt.get(w.lower())
        if e:
            return _case(e[idx], w)
        return _EEM.get(w.lower(), w) if idx == 0 and w.lower() in _EEM else w

    # ao1990-pt is the input; derive the European line by table lookup
    idx = 0
    pt_1973 = _TOK.sub(map_pt, sentence)
    idx = 1
    etymological = _TOK.sub(map_pt, sentence)

    # Brazilian modern: nasal-vowel alternation + dual/divergence (orthography only)
    def to_br(m):
        w = m.group(0)
        low = w.lower()
        repl = M.lex.dual_pt2br.get(low) or M.lex.divergence_pt2br.get(low)
        if repl:
            return _case(repl, w)
        return _case(rules.nasal_vowel_to_br(low), w)

    ao_br = _TOK.sub(to_br, sentence)

    # Brazilian 1971: trema + open-diphthong/oo/-êem accents, from the verified BR map
    def to_br71(m):
        w = m.group(0)
        br = M.br.get(w.lower())
        if br:
            return _case(br, w)
        return w

    br_1971 = _TOK.sub(to_br71, ao_br)

    # month/season casing (text level): pre-AO1990 capitalises months
    pt_1973 = rules.recase_months(pt_1973, lowercase=False)
    etymological = rules.recase_months(etymological, lowercase=False)
    ao1990_pt = rules.recase_months(sentence, lowercase=True)
    ao_br = rules.recase_months(ao_br, lowercase=True)
    br_1971 = rules.recase_months(br_1971, lowercase=True)   # Brazil lowercased months in 1943

    cells = {"etymological": etymological, "pt_1973": pt_1973, "ao1990-pt": ao1990_pt,
             "br_1971": br_1971, "ao1990-br": ao_br}
    if len(set(cells.values())) == 1:
        return None                                  # no orthographic contrast -> useless
    return cells


if __name__ == "__main__":
    M = build_maps()
    print(f"verified PT map: {len(M.pt)} words; BR map: {len(M.br)} words\n")
    for s in ["O diretor aprovou a coleção objetiva em janeiro.",
              "O António é um génio académico muito ativo.",
              "A frequência da linguiça era ótima.",
              "A ideia do voo deu enjoo ao herói.",
              "De facto, o ar estava húmido e o aspeto era péssimo.",
              "O gato preto subiu ao telhado da casa."]:
        d = derive(s, M)
        if d is None:
            print(f"REJECTED: {s}")
        else:
            for n in ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]:
                print(f"  {n:14} {d[n]}")
            print()
