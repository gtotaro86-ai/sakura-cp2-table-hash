---
license: mit
base_model: peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF
base_model_relation: quantized
pipeline_tag: text-generation
tags:
  - gguf
  - deepseek
  - mixture-of-experts
  - engram
  - q3_k
  - project-maya
---

# Sakura DeepSeek V4.1 Flash 1017 — Engram Q3_K

**Maya-S mit kleineren Engram-Tabellen: 262,68 GB statt 339,48 GB.** Die beiden N-Gram-/Engram-Tabellen wurden von **Q6_K nach Q3_K** umgerechnet. Die vier Dateien des Modellrumpfs wurden unverändert aus Maya-S übernommen.

| Ergebnis | Wert |
| --- | ---: |
| Vollständiger GGUF-Hauptmodellsatz | **262,676 GB / 244,636 GiB** |
| Ersparnis gegenüber Maya-S | **76,802 GB / 22,62 %** |
| Engram-Tabellenpayload | **84,483 GB statt 161,285 GB** |
| Ersparnis bei den Tabellen | **47,62 %** |
| Vollständiger Cloud-Bau einschließlich Veröffentlichung | **1 h 27 min 29 s** |

**Es wurde kein vollständiger Inferenztest durchgeführt.**

## Herkunft und genaue Quantisierungsquelle

| Stufe | Modell / Repository | Rolle |
| --- | --- | --- |
| Ursprüngliches Modell | [deepseek-ai/DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) | DeepSeek-Checkpoint und Architektur |
| Direkte Eingabe dieses Builds | [peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF), Ordner **Maya-S** | Bereits quantisierter Modellrumpf und zwei Q6_K-Engram-Tabellen |
| Dieses Repository | **webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF** | Unveränderter Maya-S-Rumpf plus neu kodierte Q3_K-Tabellen |

Die direkte Eingabe für die Tabellenquantisierung waren **Shards 5 und 6 von Maya-S**, gepinnt auf Revision `b9e25f34b53806b24e5b18085de6ed5967ad9ed5`. Jede Q6_K-Zeile wurde zu Float32 dequantisiert und anschließend mit dem ggml-Q3_K-Quantizer neu kodiert. Es handelt sich um eine **Requantisierung der vorhandenen Q6_K-Tabellen**; die Tabellen wurden für diesen Sakura-Build nicht erneut aus DeepSeeks FP8-Originalgewichten erzeugt.

Die ersten vier Maya-S-Shards wurden serverseitig übernommen. Ihre Größen und LFS-SHA256 stimmen mit der gepinnten Quelle überein. Es wurden keine Experten entfernt und keine Rumpfgewichte neu quantisiert.

## Vergleich: DeepSeek-Original, Maya-S und Sakura

| Merkmal | DeepSeek-Original | Maya-S von peasantsmith | Sakura Engram Q3_K |
| --- | --- | --- | --- |
| Dateiformat | Safetensors | GGUF | GGUF |
| Expertengewichte | FP4 laut Originalkonfiguration | Gemischte IQ2-/IQ3-Formate | Unverändert aus Maya-S |
| Dense-/Attention-Gewichte | FP8 und weitere Originaltypen | Überwiegend Q8_0; weitere Typen bleiben erhalten | Unverändert aus Maya-S |
| Engram-Tabellen | FP8 | Q6_K | **Q3_K** |
| Anzahl der Engram-Zeilen | 768.022.850 | 768.022.850 | **768.022.850** |
| Große Engram-Tabellen verändert | Referenz | Von peasantsmith quantisiert | **Nur diese beiden Tabellen neu kodiert** |
| Runtime-Bezug | DeepSeek-Referenz / passende Frameworks | Project Maya | **Project Maya mit mitgeliefertem Q3_K-Engram-Patch** |

### Dateigrößen und Vergleichsumfang

| Paket / Bestandteil | Bytes | GB | GiB |
| --- | ---: | ---: | ---: |
| Offizielles Checkpoint-Paket, Summe aller 48 Safetensors-Dateien | 510.296.708.312 | 510,297 | 475,251 |
| Maya-S, sechs Hauptmodell-GGUFs | 339.477.953.988 | 339,478 | 316,163 |
| **Sakura, sechs Hauptmodell-GGUFs** | **262.675.668.988** | **262,676** | **244,636** |
| Unveränderter Maya-S-/Sakura-Modellrumpf, Shards 1–4 | 178.193.155.104 | 178,193 | 165,955 |
| Maya-S-Tabellenpayload, Q6_K | 161.284.798.500 | 161,285 | 150,208 |
| **Sakura-Tabellenpayload, Q3_K** | **84.482.513.500** | **84,483** | **78,680** |

**GB = 10⁹ Bytes; GiB = 2³⁰ Bytes.** Die beiden Tabellenheader belegen zusammen weitere 384 Bytes. Kleine README-, Patch-, Lizenz- und Manifestdateien sind in den GGUF-Summen nicht enthalten.

Der direkte Größenvergleich mit identischem Hauptmodellumfang ist **Maya-S gegen Sakura**. Die 510,297 GB des Originals sind das gesamte veröffentlichte 48-Dateien-Safetensors-Paket; daraus wird hier keine bereinigte Hauptmodell-Ersparnis abgeleitet. Sakura enthält den sechsteiligen GGUF-Hauptmodellsatz; zusätzliche Vision-/DSpark-Dateien werden hier nicht mitgeliefert. Dateigrößen sind keine RAM-/VRAM-Bedarfsangaben.

### Welche Maya-S-Quantisierung bleibt erhalten?

| Tensorgruppe | Übernommene Maya-S-Typen |
| --- | --- |
| Routed Experts, Gate/Up | IQ2_XXS; IQ2_S in den ersten/letzten vier Layern |
| Routed Experts, Down | IQ3_XXS; IQ3_S in den ersten/letzten vier Layern |
| Attention, Shared Experts, Embeddings, Output, Engram-Value-Projektion | Q8_0 |
| Router, Normen, Hyper-Connection-Mixing, Attention Sinks | F32 |
| Kleine Indexer-Projektionen | BF16 |
| Große Engram-Embedding-Tabellen | **Q6_K → Q3_K; einzige neu quantisierte Tensorgruppe** |

Damit bezeichnet **Q3_K in diesem Repository die Engram-Tabellen**. Der Modellrumpf behält die gemischte Quantisierung von Maya-S.

## Architektur und Tabellenlayout

Die geprüfte Originalkonfiguration nennt 40 Text-Layer, Hidden Size 5.120, 384 geroutete Experten pro Layer, 6 ausgewählte Experten pro Token und einen Shared Expert. Die Engram-Tabellen liegen in den GGUF-Layern 1 und 14. Konfiguriert sind N-Gramme bis Länge 4 und 256 Werte pro Tabellenzeile.

| Tabelle | Zeilen | Werte pro Zeile | Q3_K-Payload |
| --- | ---: | ---: | ---: |
| `blk.1.engram_embd.weight` | 384.006.168 | 256 | 42.240.678.480 Bytes |
| `blk.14.engram_embd.weight` | 384.016.682 | 256 | 42.241.835.020 Bytes |
| **Summe** | **768.022.850** | — | **84.482.513.500 Bytes** |

| Formatdetail | Maya-S-Eingabe | Sakura-Ausgabe |
| --- | ---: | ---: |
| GGML-Typ | Q6_K / 14 | Q3_K / 11 |
| Werte pro Block / Zeile | 256 | 256 |
| Bytes pro Zeile einschließlich Blockskalen | 210 | 110 |
| Effektive Bits pro Wert einschließlich Blockskalen | 6,5625 | 3,4375 |

Namen, Dimensionen, Zeilenanzahl und Tabellenadressierung bleiben erhalten. Der GGUF-Tensortyp wird korrekt auf **11 / Q3_K** gesetzt; die neuen Daten werden nicht als Q6_K etikettiert.

Die Originalkonfiguration sieht bis zu 1.048.576 Kontextpositionen vor. Das ist eine Architekturangabe; für diesen Sakura-Build wurde kein Kontext- oder Speicherbenchmark durchgeführt.

## Dateien und Prüfsummen

Alle sechs GGUF-Dateien liegen unter [Maya-S/](tree/main/Maya-S). Der gemeinsame Dateinamensanfang lautet `DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-`.

| Dateiendung | Inhalt | Größe in Bytes |
| --- | --- | ---: |
| `00001-of-00006.gguf` | Unveränderter Rumpf | 47.887.697.312 |
| `00002-of-00006.gguf` | Unveränderter Rumpf | 47.669.578.400 |
| `00003-of-00006.gguf` | Unveränderter Rumpf | 47.103.347.360 |
| `00004-of-00006.gguf` | Unveränderter Rumpf | 35.532.532.032 |
| `00005-of-00006.gguf` | Engram, Layer 1, **Q3_K** | 42.240.678.672 |
| `00006-of-00006.gguf` | Engram, Layer 14, **Q3_K** | 42.241.835.212 |

Die ursprünglichen Shardnamen bleiben für die Split-Zuordnung erhalten. Auch wenn der Dateiname weiterhin `IQ2_XXS` enthält, sind die Tabellen in Shards 5/6 **Q3_K**; maßgeblich ist der geprüfte GGUF-Header.

Das [Buildmanifest](resolve/main/build-manifest.json) enthält alle sechs Dateigrößen und SHA256 sowie Quellrevision, Patchhash und die beiden vollständigen Tabellen-Bauberichte. Die separaten Berichte stehen unter [build/shard5.json](resolve/main/build/shard5.json) und [build/shard6.json](resolve/main/build/shard6.json).

## Tatsächlicher Cloud-Bau

| Schritt / Messwert | Ergebnis |
| --- | --- |
| Ausführungsumgebung | Öffentliche Standard-`ubuntu-24.04`-CPU-Runner; zwei Tabellenjobs parallel |
| Gesamter Workflow | **1 h 27 min 29 s** |
| Tabelle 5, Hashbildung/Kodierung und Uploadprüfung | 5.179,107 s / ca. 86 min 19 s |
| Tabelle 6, Hashbildung/Kodierung und Uploadprüfung | 4.780,244 s / ca. 79 min 40 s |
| Gelesene Q6_K-Quelldaten auf den Runnern | 322.569.597.000 Bytes, genau zwei Payload-Durchläufe |
| Neue Q3_K-Tabellen | 84.482.513.500 Bytes Payload plus 384 Headerbytes |
| Modellrumpf | Vier Dateien serverseitig kopiert; Quell-LFS-SHA256 erhalten |
| Abschluss | Alle sechs Größen und Remote-LFS-SHA256 gegen das Manifest geprüft |
| Ressourcen | CPU; keine GPU, kostenpflichtigen Runner oder Inferenz-API |

Die Tabellen wurden als deterministischer, seekbarer Quantisierungsstrom mit begrenzten RAM-Blöcken erstellt. Für Hashbildung und Upload wurden dieselben Quelldaten erneut gelesen und kodiert. Es wurde keine vollständige 42-GB-Ausgabetabelle auf der Runner-Disk materialisiert. Der Nutzer-PC war am Vollbau nicht beteiligt.

## Runtime und Nutzung

Erforderlich ist der enthaltene [Maya-Q3_K-Engram-Patch](resolve/main/runtime/maya-q3k.patch) für [Project Maya](https://github.com/mw00/project-maya), geprüft gegen Revision `451f9cb6a21ea65673bdde2e57b4a670ae2b8859`.

Der Patch ergänzt Q3_K ausdrücklich im Engram-Reader und in den zugehörigen Decodern. Eine allgemeine Q3_K-Unterstützung eines Packers oder einer anderen Runtime reicht für diesen speziellen Tabellenpfad nicht aus.

Der Patch wird als Quellcode mitgeliefert. Er wurde gegen den angegebenen Maya-Stand entwickelt; es liegt kein vorgebauter Sakura-Windows-/HIP-Starter bei. Die geänderten CUDA-Übersetzungseinheiten wurden kompiliert und der GPU-Paritätstest verlinkt. GPU-Ausführung, ein vollständiger Maya-Programm-Link sowie HIP-/Windows-Betrieb wurden nicht nachgewiesen. Vision und DSpark benötigen gegebenenfalls die separaten Upstream-Komponenten.

## Prüfstand und Qualitätsvergleich

| Eigene Prüfung | Ergebnis |
| --- | --- |
| Realer CPU-Pilot | 98.304 Q6_K-Zeilen aus Anfang, Mitte und Ende beider Tabellen |
| Wiederholte Quantisierung der Pilotblöcke | Identische Q3_K-SHA256 in drei Durchläufen pro Probe |
| Q3_K-CPU-Decoder gegen ggml | Bitgenaue Parität auf 192 realen quantisierten Zeilen, 4.096 Zufallsblöcken und 63.488 endlichen FP16-Skalen |
| Maya-Reader/Cache | 64-Bit-Offsets, Token-Slots, Duplikate, Eviction und Short Reads geprüft |
| GGUF-Streaming / HF-Kompatibilität | Seek-/Blockgrenzen, wiederholte Hashbildung und Multipart-Zusammensetzung geprüft |
| Vollständige Ausgabedateien | Größen und Remote-LFS-SHA256 geprüft |
| Zusätzliche Headerkontrolle nach Release | Beide 192-Byte-Header stimmen mit dem erwarteten Q3_K-Layout überein |

Im CPU-Pilot lagen die RRMSE-Werte der sechs Probenblöcke gegenüber der **vorhandenen Q6_K-Eingabe** zwischen etwa **15,209 % und 15,233 %**. Das misst numerische Abweichung der Tabellenwerte. Es ist kein Vergleich mit den ursprünglichen FP8-Tabellen und kein PPL-, Coding-, Antwortqualitäts- oder Inferenzgeschwindigkeitstest.

Die [Maya-S-Modellkarte an der Quellrevision](https://huggingface.co/peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF/blob/b9e25f34b53806b24e5b18085de6ed5967ad9ed5/README.md) berichtet separat folgende Messung gegenüber DeepSeeks Referenz, auf 10 zurückgehaltenen Sequenzen zu jeweils 2.047 Tokens:

| Upstream-Messung von peasantsmith | Gleicher Top-Token | KL-Divergenz |
| --- | ---: | ---: |
| Originalgewichte durch Mayas Engine | 96,4 % | 0,047 |
| Maya-S mit Q6_K-Tabellen | 92,6 % | 0,120 |
| **Sakura mit Q3_K-Tabellen** | **Nicht gemessen** | **Nicht gemessen** |

Die beiden Upstream-Werte wurden hier nicht neu gemessen und werden nicht als Sakura-Ergebnis übernommen. Sie beziehen sich auf die dort beschriebene Tokenvergleichsmethode; sie sind keine allgemeinen Aufgaben-Scores. Für Sakura werden keine unveränderte Modellqualität oder zusätzlichen Tokens/s behauptet.

**Es wurde kein vollständiger Inferenztest durchgeführt.**

## Reproduzierbare Quellen

| Bestandteil | Gepinnter Stand |
| --- | --- |
| Direktes Maya-S-Eingabemodell | `b9e25f34b53806b24e5b18085de6ed5967ad9ed5` |
| Offizielles DeepSeek-Checkpoint, Konfiguration und Größeninventar | `1bae0e1088993b9b82de08f59de5be5a34e42170` |
| Maya-Engine vor Sakura-Patch | `451f9cb6a21ea65673bdde2e57b4a670ae2b8859` |
| llama.cpp / ggml-CPU-Quantizer | `c7fc5094179bf8a9c73c18593db714f8da41a402` |
| SHA256 des mitgelieferten Runtime-Patches | `e5e2c5d50633fcf1fb57478656e6bce4d7453d06ea43b2381c9da6fe395f0cfd` |

Architekturangaben und das Originalformat stammen aus der [gepinnten DeepSeek-Konfiguration](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/config.json). Die Originalpaketgröße wurde aus den Dateimetadaten der 48 Safetensors-Dateien dieser Revision summiert. Dafür wurden keine Originalgewichte heruntergeladen.

## Lizenz und Danksagung

Modell und Quantisierung: **MIT**, entsprechend der Original- und Maya-S-Veröffentlichung. Die mitgelieferten Lizenztexte stehen unter [LICENSE.DeepSeek](resolve/main/LICENSE.DeepSeek), [LICENSE.Maya](resolve/main/LICENSE.Maya) und [LICENSE.llama.cpp](resolve/main/LICENSE.llama.cpp).

Basismodell: **DeepSeek-AI**. Maya-S-Quantisierung und Tabellenquelle: **peasantsmith**. Runtime: **Project Maya**. CPU-Quantizer: **ggml / llama.cpp**. Sakura ändert ausschließlich die beiden großen Engram-Tabellen und ergänzt den dafür benötigten Maya-Decoderpfad.
