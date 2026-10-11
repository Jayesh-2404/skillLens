"""Pure scoring logic: weighted field overlap + phrase/trigger bonus, length-normed. No I/O except load."""
import json
import math
import os
import re

try:
    from skilllens.brand import NAME, TAGLINE
except ImportError:  # pragma: no cover
    try:
        from brand import NAME, TAGLINE
    except ImportError:
        NAME = "SkillLens"
        TAGLINE = "Prompt in, ranked skills out"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
# why: index lives at the repo root (next to cli.py) so it resolves from any cwd
INDEX_PATH = os.path.join(ROOT_DIR, "skills.json")

STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "in", "on", "of", "to", "with",
    "this", "that", "these", "those", "it", "its", "is", "are", "be",
    "before", "then", "while", "use", "using", "into", "from",
    "your", "work", "does", "what", "when", "need", "want", "help",
    "question", "task", "code", "file",
    "my", "me", "i", "should", "which",
}

# Synonym siblings (all lowercase): expand prompt tokens so ask->grill,
# architecture->design, understand->shared-understanding etc. still recall.
# Synonym matches score 0.5x a direct match in every field weight class.
SYNONYMS = {
    "grill": ["ask", "interview", "quiz", "question", "interrogate", "grill"],
    "ask": ["grill", "interview", "quiz", "question"],
    "interview": ["grill", "ask", "quiz", "question"],
    "question": ["ask", "grill", "interview", "quiz"],
    "architecture": ["design", "structure", "layering"],
    "design": ["architecture", "plan", "structure"],
    "understand": ["learn", "comprehend", "onboard", "grasp", "know"],
    "codebase": ["code", "repo", "project", "codebase"],
    "debug": ["diagnose", "fix", "troubleshoot", "bug"],
    "test": ["tdd", "spec", "unit"],
}
SYN_W = 0.5  # synonym match weight relative to a direct match

# Router skills: match almost anything via long summaries; demote unless help intent.
ROUTER_KEYS = ("poteto-help", "poteto-mode", "setup-pstack")
ROUTER_EXEMPT = ("help", "which skill", "pstack", "setup")

DESC_W = 2.0    # description tokens: strongest intentional signal
NAME_W = 1.0    # name tokens: medium
SUMM_W = 0.3    # summary tokens: weak (long docs must not dominate)
NAME_BONUS = 3.0
PHRASE_W = 1.5
TRIG_W = 0.5
ROUTER_PENALTY = 2.0
# Designated triage skill: its description is "picking the skill ... for a task".
# Boosted (not just un-demoted) on help intent so it surfaces for "which skill" questions.
TRIAGE_KEY = "poteto-help"
TRIAGE_BONUS = 2.0
# Ask-me-until-I-understand intent: user wants to be grilled/quizzed on the
# codebase until they understand it. Boosted so grill skills rank first.
GRILL_KEYS = ("grill-me", "grilling")
GRILL_BONUS = 2.0


def load_index(path=INDEX_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def skill_key(skill):
    """Canonical key for dedupe/demotion; works on old indexes without 'key' too."""
    key = skill.get("key")
    if key:
        return key
    return re.sub(r"[\s_]+", "-", (skill.get("name") or "").strip().lower())


def score_prompt(prompt, skills):
    """Return [(skill, score, reason)]; higher = better."""
    ptoks = [t for t in tokenize(prompt) if t not in STOPWORDS]
    pset = set(ptoks)
    # synonym siblings of prompt tokens (excluding direct tokens themselves)
    synset = set()
    for t in pset:
        for s in SYNONYMS.get(t, ()):
            if s not in pset:
                synset.add(s)
    plower = prompt.lower()
    bigrams = {" ".join(ptoks[i:i + 2]) for i in range(len(ptoks) - 1)}
    help_intent = any(e in plower for e in ROUTER_EXEMPT)
    grill_ask = (
        "ask me" in plower
        or "quiz me" in plower
        or "grill me" in plower
        or ("ask" in plower and "question" in plower)
    )
    grill_goal = any(w in plower for w in ("understand", "learn", "explain", "until"))
    grill_intent = grill_ask and grill_goal
    results = []
    for s in skills:
        key = skill_key(s)
        name_toks = set(t for t in tokenize(s.get("name", "")) if t not in STOPWORDS)
        desc_toks = set(t for t in tokenize(s.get("description", "")) if t not in STOPWORDS)
        summ_toks = set(t for t in tokenize(s.get("summary", "")) if t not in STOPWORDS)
        od = pset & desc_toks
        on = pset & name_toks
        os_ = pset & summ_toks
        od_syn = synset & desc_toks
        on_syn = synset & name_toks
        os_syn = synset & summ_toks
        raw = (DESC_W * (len(od) + SYN_W * len(od_syn))
               + NAME_W * (len(on) + SYN_W * len(on_syn))
               + SUMM_W * (len(os_) + SYN_W * len(os_syn)))
        # exact name bonus (why: explicit skill mention = exact intent)
        if s.get("name", "").lower() in pset or (key and "-" in key and key in plower):
            raw += NAME_BONUS
        # phrase bonus: prompt bigram appears verbatim in skill text (why: phrase intent)
        text = f"{s.get('name', '')} {s.get('description', '')} {s.get('summary', '')}".lower()
        phrase_hits = sum(1 for b in bigrams if b in text)
        raw += PHRASE_W * phrase_hits
        # trigger bonus: exact token match only (why: substring favored verbose trigger lists)
        trig_hits = [t for t in s.get("triggers", []) if t.lower() in pset]
        trig_syn = [t for t in s.get("triggers", []) if t.lower() in synset]
        raw += TRIG_W * (len(trig_hits) + SYN_W * len(trig_syn))
        # length normalization (why: long router docs matched everything)
        doc_len = len(set(tokenize(
            f"{s.get('name', '')} {s.get('description', '')} {s.get('summary', '')}")))
        norm = math.log(1 + doc_len)
        score = raw / norm if norm > 0 else raw
        demoted = False
        if key in ROUTER_KEYS and not (help_intent or (key and key in plower)):
            score -= ROUTER_PENALTY
            demoted = True
        if help_intent and key == TRIAGE_KEY:
            score += TRIAGE_BONUS / norm if norm > 0 else TRIAGE_BONUS
        if grill_intent and key in GRILL_KEYS:
            score += GRILL_BONUS
        matched = sorted(od | on | {t for t in trig_hits if t in pset})
        reason = f"matched {len(od)} desc + {len(on)} name + {len(os_)} summary token(s)" + (
            f": {', '.join(matched[:6])}" if matched else "")
        if phrase_hits:
            reason += f" + {phrase_hits} phrase hit(s)"
        if trig_hits:
            reason += f" + {len(trig_hits)} trigger hit(s)"
        syn_hits = od_syn | on_syn | os_syn | {t.lower() for t in trig_syn}
        if syn_hits:
            reason += f" + {len(syn_hits)} synonym hit(s)"
        if demoted:
            reason += " [router demoted]"
        if help_intent and key == TRIAGE_KEY:
            reason += " [triage boost]"
        if grill_intent and key in GRILL_KEYS:
            reason += " [grill-intent boost]"
        results.append((s, score, reason))
    results.sort(key=lambda r: (-r[1], r[0].get("name", "")))
    return results


def suggest(prompt, skills=None, top_k=3):
    if skills is None:
        skills = load_index()
    ranked = score_prompt(prompt, skills)
    return [
        {"skill": s, "score": float(sc), "reason": r}
        for s, sc, r in ranked[:top_k]
    ]
