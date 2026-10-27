# Architecture

The implemented bootstrap consists of `TextService`, provider-independent data contracts, protocols and explicit settings. The following diagrams show the intended direction and are **proposals**, except for the existing text service and interfaces. No prior architecture reference was found. Arrows indicate conceptual flow, not implemented integrations or approved internal dependencies.

## 1. General architecture

```mermaid
flowchart LR
    Input[Text / future documents] --> Core[Core orchestration]
    Core --> Contracts[Provider-independent contracts]
    Core --> Classifier[Classifier interface]
    Core --> LLM[LLM interface]
    Core --> TTS[TTS interface]
    Core --> Context[Context and storage]
    Classifier -. future .-> Laya[Laya]
    LLM -. future .-> Models[Local or remote LLM]
    TTS -. future .-> Engine[TTS engine]
```

## 2. Core internals

```mermaid
flowchart LR
    Text --> Validate[Validate]
    Validate --> Split[Split lines preserving text]
    Split --> Plan[NarrationPlan]
    Plan -. future .-> Orchestrate[Expressive orchestration]
```

## 3. Expressive narration

```mermaid
flowchart LR
    Text --> Segments --> Interpretation[Context interpretation]
    Interpretation --> Classification[Expressive classification]
    Classification --> VocalPlan[Vocal planning]
    VocalPlan --> Synthesis[TTS synthesis] --> Playback
```

Only text segmentation exists today.

## 4. Interchangeable LLMs

```mermaid
flowchart LR
    Core --> Interface[LLMProvider protocol]
    Interface -. future .-> Local[Local adapter]
    Interface -. future .-> Remote[Explicitly configured remote adapter]
```

## 5. Expressive classification with Laya

```mermaid
flowchart LR
    Segment --> Interface[ExpressiveClassifier protocol]
    Interface -. future .-> Adapter[Laya adapter]
    Adapter --> Labels[Emotion and style]
```

Laya is the intended initial classifier; neither adapter nor integration exists yet. Speaker identification remains future work.

## 6. TTS adaptation

```mermaid
flowchart LR
    Plan[Narration plan] --> Interface[TTSProvider protocol]
    Interface -. future .-> Adapter[TTS adapter]
    Adapter --> Audio[Audio for playback]
```

The current protocol accepts a text segment and returns bytes; audio encoding and expressive mapping are undecided.

## 7. Memory and context

```mermaid
flowchart LR
    Content --> Context[Context management]
    Context <--> Memory[Memory / storage]
    Context --> Interpretation
```

Scope, persistence, retention and interfaces are undecided.

## 8. Conversation during playback

```mermaid
flowchart LR
    Playback --> Question[User question]
    Question --> Context[Relevant content context]
    Context --> LLM[LLM provider]
    LLM --> Response[Response]
    Response --> Playback
```

Playback interruption and resumption behavior remain undecided.

## 9. SDD workflow

```mermaid
flowchart LR
    Define[Owner defines feature] --> Discuss[Discuss design]
    Discuss --> Draft[Draft SPEC] --> Approve[Owner approves SPEC]
    Approve --> Implement[Implement approved scope] --> Test[Automated checks]
    Test --> Review[Owner reviews changes]
    Review -->|Revise| Draft
    Review -->|Owner approves integration| Main[Integrate into main]
```

## 10. Implemented content ingestion (SPEC-002)

```mermaid
flowchart LR
    File[File] --> Validator[Validator and size limits]
    Validator --> Registry[Importer registry]
    Registry --> Extractor[Format-specific extractor]
    Extractor --> IR[Document / sections / elements]
    IR --> Segmenter[Character segmenter]
    Segmenter --> Check[Structural validation]
    Check --> JSON[Structured JSON]
```

The content service and importers are separate from `TextService` and provider contracts. Importers only parse local bytes. Format-specific extraction cannot guarantee layout or byte-for-byte fidelity of an EPUB, PDF or DOCX. See [SPEC-002](../specs/SPEC-002-content-ingestion.md) for exact behavior and limitations. Other diagrams above describe future narration work, not an implemented pipeline.
