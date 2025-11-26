README – LiCoMemory-Inspired Memory Architecture (Local Overview)

Important:
This document is meant to teach Windsurf about the LiCoMemory-style architecture being used in this project.
Windsurf has no built-in knowledge of “LiCoMemory” because:

The paper is extremely new (2025)

The model’s training cutoff predates it

We do NOT provide Windsurf the PDF directly

Everything Windsurf knows about LiCoMemory must come from this README.

1. What This Memory System Is

This backend includes a custom, lightweight, hierarchical memory system inspired by the LiCoMemory research paper:
“LiCoMemory: Lightweight and Cognitive Agentic Memory for Efficient Long-Term Reasoning” 

LiCoMemory_ Lightweight and Cog…

This system is not a clone of LiCoMemory.
Instead, it adapts LiCoMemory’s three-layer hierarchical graph into a practical, simplified implementation for your FastAPI + Python backend.

The memory graph is used to extract and store:

High-level summaries of each session

Entities and relationships (triples)

Raw conversation chunks as evidence

The goal is to give the backend long-term continuity, reasoning over past conversations, and structured retrieval, without relying on large vector stores or flat RAG.

2. Why LiCoMemory Matters (Local Summary)

The LiCoMemory paper introduces a new idea:

Use a hierarchical graph as a semantic index, not a giant knowledge store.
(See the “Preliminary: CogniGraph Structure” diagram on page 4 of the PDF.) 

LiCoMemory_ Lightweight and Cog…

This allows:

Smaller memory footprint

Faster updates

Better retrieval across long sessions

Retrieval that respects time, hierarchy, and semantic similarity

Our local implementation follows this philosophy.

3. The Three Hierarchical Memory Objects (Our Implementation)

The system implements three layers, aligned with the CogniGraph structure described on page 4 of the LiCoMemory paper. 

LiCoMemory_ Lightweight and Cog…

These objects are stored in the database and form the spine of the memory graph.

3.1 SessionSummary (Top Layer)

Represents one conversation session and acts as the graph’s entry point.

Stores:

Summary text

Keywords

Themes

Start/end timestamps

Link to triples

Link to chunks

Role:

High-level “topic anchor”

Helps rank which sessions are relevant for retrieval

3.2 Entities & Triples (Middle Layer)
Entity

A canonical object, e.g. Oliver, Hazal, work stress, PVM project.

Stores minimal information:

canonical_name

entity_type

timestamps

Triple

A lightweight fact:

(Entity A) —[relation]→ (Entity B)


Example:

Oliver —[feels]→ stressed about sprint deadline

Triples link to:

SessionSummaries

MemoryChunks

This is the semantic indexing layer, exactly as described in the paper (page 4, entity–relation level). 

LiCoMemory_ Lightweight and Cog…

3.3 MemoryChunk (Bottom Layer)

A chunk of raw text from the conversation.

Includes:

The original messages (user + assistant pair or small batch)

Timestamps

Message IDs

Links to triples

These are the “original dialogue chunks” shown in the CogniGraph diagram (page 4). 

LiCoMemory_ Lightweight and Cog…

Chunks provide the evidence for each triple.

4. How the Memory System Works (High Level)

Inspired by the pipeline shown in Figure 2 (pages 4–5). 

LiCoMemory_ Lightweight and Cog…

4.1 Update Pipeline (After Each Turn)

Create a MemoryChunk

Call a lightweight LLM to extract:

summary updates

entities

triples

Deduplicate entities/triples

Link everything across layers

SessionSummary evolves over time

This produces a continuously updating, clean semantic index.

4.2 Retrieval Pipeline (When Answering a Query)

Extract entities from the user query

Rank sessions by summary similarity

Rank triples inside those sessions

Apply temporal weighting (recent memories matter)

Assemble:

session summary

top triples

supporting chunks

Prepend this to the LLM call

This mirrors the hierarchy + temporal reranking described in Section 3.2. 

LiCoMemory_ Lightweight and Cog…

5. Why Windsurf Needs This README

Windsurf will not know anything about LiCoMemory by default:

The paper is from 2025

Windsurf’s training cutoff predates it

The PDF is not automatically loaded into Windsurf’s model context

Windsurf cannot search the internet for it

This document exists so Windsurf can:

Understand the roles of SessionSummary, Entity, Triple, MemoryChunk

Understand how your backend uses these objects

Know the intended retrieval and update behaviour

Have proper architectural context when assisting with coding

6. What Windsurf Should Not Assume

Windsurf should NOT assume LiCoMemory exists in its training data

Windsurf should NOT assume any external definitions of the architecture

Windsurf should NOT expect to see the LiCoMemory paper unless explicitly provided

Windsurf must treat this README as the single source of truth

7. Future Extensions

Potential enhancements:

Automatic graph visualisation (API endpoint)

Multi-session splitting

Temporal reasoning improvements

Vector database hybrid retrieval

Multi-agent memory

Compression of long histories

These map to the future work section in the LiCoMemory paper (page 9). 

LiCoMemory_ Lightweight and Cog…