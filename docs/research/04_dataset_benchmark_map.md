# Dataset and Benchmark Map

Public benchmarks should be the primary source of evidence. Synthetic and custom game-engine data should be used for sanity checks, controlled case studies, or external validation only. Do not overclaim based on toy data.

| Dataset / Benchmark | Source | Data modality | Label type | Temporal labels? | Access status | Planned use | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| World of Bugs | WOB project / GitHub submodule | 3D game observations, assets, bug labels | Bug classes and masks, exact format TBD / verify | Possibly frame/observation-level, verify | Declared submodule but may be uninitialized | Bug taxonomy, controlled game bug examples, possible evaluation source | Unity/platform setup and label adaptation |
| GlitchBench | Project site / Hugging Face | Images from video game glitch scenarios | Image/question-style labels, verify | Mostly no, verify | Optional external dataset; no data committed | Public image-level evidence and feature baseline comparison | Static framing limits temporal claims |
| VideoGlitch / GlitchAgent | Paper/project TBD | Gameplay videos | Open-ended descriptions and temporal spans, verify | Yes, reported | Not integrated | Future temporal benchmark comparison | Likely requires VLM-style evaluation and benchmark access |
| VideoGlitchBench | Paper/project TBD | Gameplay videos | Glitch descriptions and temporal localization, verify | Yes, reported | Not integrated | Strong candidate for future temporal evaluation | New benchmark; access/protocol must be verified |
| TempGlitch | Paper/project TBD | Controlled gameplay videos | Binary/category labels, verify | Yes, designed for temporal glitches | Not integrated | Best-aligned future temporal glitch benchmark | New dataset; exact access and license must be verified |
| Procgen | OpenAI Procgen | Synthetic game frames | Environment state and generated labels if instrumented | Yes if custom logged | Not integrated | Controlled sanity checks for dynamics violations | Synthetic domain; labels require custom instrumentation |
| Atari / ALE | Arcade Learning Environment | Game frames | Scores/actions/states; custom glitch labels needed | Yes if custom logged | Not integrated | External validation on classic game dynamics | Hard to define real glitches without injection |
| Synthetic dynamics datasets in this repo | `scripts/create_*dynamics*` | Generated image frames | Interval labels CSV | Yes | Available through scripts; generated data ignored by git | Sanity checks for pipeline and latent proxy | Toy data; not publishable evidence alone |
| Godot mini dataset | Future custom project | Gameplay videos | Controlled glitch toggles and timestamps | Yes if instrumented | Future only | Controlled case study and demonstration | Could overfit to one engine or scene |
| Unity mini dataset | Future custom project or WOB | Gameplay videos / observations | Controlled bug labels | Yes if instrumented | Future only | External validation and WOB alignment | Setup and reproducibility overhead |

## Evidence policy

- Primary claims should use public benchmarks when possible.
- Synthetic data can test pipeline mechanics and reveal failure modes.
- Custom Godot/Unity data can demonstrate controlled temporal violations.
- A paper should clearly separate "sanity check", "case study", and "benchmark result".
