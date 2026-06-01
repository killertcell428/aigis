# Pending: Lexical Camouflage Detection via Semantic Similarity

## Title
Detection of lexical camouflage jailbreaks using embedding-based semantic similarity

## Motivation
"Anyone Can Jailbreak" (arxiv:2507.21820, July 2025) identifies lexical camouflage — using
alternative terminology to mask prohibited requests — as one of five jailbreak categories and
notes it is the hardest to block with static rules because the vocabulary is unbounded. Attackers
substitute technical synonyms, euphemisms, slang, or domain-specific jargon for blocked keywords:
e.g., "energetic materials" for "explosives", "recreational chemistry" for drug synthesis, or
"grey-hat operations" for malware development.

## Proposed change
Add an optional semantic-similarity detection mode that embeds the input and checks cosine
similarity against a library of known harmful-intent sentence embeddings. Flag inputs whose
semantic centroid falls within a configurable distance of known jailbreak intent clusters even
when no keyword matches.

## Why it was held back
Requires a runtime embedding model or vector store, which violates the zero-runtime-dependency
constraint. Lightweight alternatives (TF-IDF cosine similarity against a harmful intent lexicon)
could work without a neural model but would not generalise well to novel phrasings.

## Which constraint blocked it
Runtime dependency requirement (embedding model or vector store). The zero-dependency philosophy
prohibits this for the core library.

## Research finding
arxiv:2507.21820 (July 2025): https://arxiv.org/abs/2507.21820

## Suggested next step
Implement as an optional `dev`-extra dependency module (`aigis[semantic]`) that adds an optional
`semantic_mode=True` flag to `Guard()`. This keeps the core library dependency-free while making
semantic detection available for users who opt in. A lightweight ONNX-based sentence encoder
(~60 MB) would make this feasible without a full ML stack.
