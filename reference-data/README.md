# Manufacturer reference passages

This library contains nine assistant-written summaries from two Raspberry Pi documentation files at commit `9bb5ef62d9d5e32930d5d79ae2e05cf75f0eea4f`. It covers Raspberry Pi 3 Model B+, 4, and 5. It contains no maintenance-event records.

Each passage records its model applicability, source version and SHA-256, section, license, attribution, and source URL. The root manifest fingerprints the JSONL file. Runtime indexing rejects a mismatched corpus. The summaries and applicability metadata remain subject to editorial correction; the original manufacturer text is linked from each retrieved source in the app.

Sources: [frequency management](https://github.com/raspberrypi/documentation/blob/9bb5ef62d9d5e32930d5d79ae2e05cf75f0eea4f/documentation/asciidoc/computers/raspberry-pi/frequency-management.adoc), [power supplies](https://github.com/raspberrypi/documentation/blob/9bb5ef62d9d5e32930d5d79ae2e05cf75f0eea4f/documentation/asciidoc/computers/raspberry-pi/power-supplies.adoc).

Attribution: Raspberry Pi Ltd; summaries by the Frontline project assistant. Distributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), consistent with [Raspberry Pi's documentation terms](https://www.raspberrypi.com/licensing/). This data license does not assign a license to unrelated application code or historical assets.

The two files are a single upstream documentation family. They are development sources already used to design retrieval and examples; they must not later be relabeled as a held-out assessment family.

The application uses only this public library. Fictional controller revisions, private passages, and revoked guidance are created separately by the evaluation code for boundary tests; they do not enter the production reference corpus.
