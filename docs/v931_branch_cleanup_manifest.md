# v9.3.1 Branch Cleanup Manifest

> Repository Hygiene H2 execution manifest.
> Baseline: `main@4ac8711049ea2f5a44ee29e2f8e8693ca14ddbec`.
> Current release: `9.3.1`.
> This file is maintenance evidence, not Runtime or modeling Authority.

## 1. Current state

- Enumerated branches (including current H2 working branch): **180**.
- SAFE_DELETE_CANDIDATE: **98**.
- MANUAL_REVIEW — merged PR tip mismatch: **53**.
- MANUAL_REVIEW — closed but unmerged PR: **7**.
- MANUAL_REVIEW — no PR association: **20**.
- KEEP: **2**.

## 2. Deletion safety rule

A branch is in `SAFE_DELETE_CANDIDATE` only when all currently verifiable conditions hold:

1. no open PR targets the branch as a PR head;
2. an associated PR is merged;
3. current branch tip SHA equals that merged PR's final head SHA;
4. the branch is not reported protected by the branch-list API;
5. no explicit provenance-retention exception is registered.

Because this repository commonly uses squash merge, `main...branch` commit ancestry is not used by itself as a deletion veto. Exact PR-head equality is the stronger no-post-merge-advance check used here.

## 3. SAFE_DELETE_CANDIDATE
- `chore/remove-accidental-noop` — PR #100, tip `db963066b70419a4cb602abcedc4b3518ce69b01`, merged 2026-09-02T09:23:04Z
- `docs/mechanism-template-compat-hygiene` — PR #123, tip `86ac6801823e6e536f8cf8d22650e4193ff234f8`, merged 2026-09-05T09:49:36Z
- `docs/semantic-state-runtime-refactor-plan` — PR #124, tip `4c29d1c96a4fc4add632f0526f86e6fe5984b459`, merged 2026-09-06T09:01:34Z
- `docs/v7.17-skill-hygiene` — PR #82, tip `5cecb21ffb25e5ae0ddeeb1a0ee1fc8d371d61f9`, merged 2026-08-29T07:15:01Z
- `docs/v8.7.0-post-merge-verification` — PR #115, tip `8b725073b733841b3d2aa02d20ba635c5812a000`, merged 2026-09-04T17:03:04Z
- `docs/v9.1-matlab-publication-rendering-plan` — PR #151, tip `70f40cf766a755b229dbbd83d8e3dddb89772fab`, merged 2026-09-09T08:13:34Z
- `docs/v9.2.1-p7-semantic-hygiene-plan` — PR #172, tip `004cc61c448caa28f2af7bbb1669b0050563ed2e`, merged 2026-09-16T04:50:35Z
- `docs/v9.3.1-maintenance-status-alignment` — PR #186, tip `3e9acad1c06e60a564f301ea76045d63ac26904a`, merged 2026-09-18T15:32:49Z
- `docs/v9.3.1-postrelease-health-remediation-plan` — PR #181, tip `4766b60868dc8f6e5a476409c4b9917a44410273`, merged 2026-09-18T12:53:24Z
- `docs/v9.3.1-postrelease-verification-closeout` — PR #188, tip `09b2cacf544ca972d903234066e5ae42593088e6`, merged 2026-09-18T16:03:24Z
- `docs/v9.3.1-prb-status-closure` — PR #184, tip `13985060a701702a9519bb950ab8e144f016097a`, merged 2026-09-18T15:03:42Z
- `docs/v9.3.1-repository-hygiene-inventory` — PR #189, tip `78e6106a81ac16694dd8385688d70ee5d743a86c`, merged 2026-09-18T16:23:29Z
- `docs/v801-phase2-governance-doc-cleanup` — PR #93, tip `70de3df06268c1b40cab01ce663e796a0850e97b`, merged 2026-09-02T01:27:34Z
- `docs/v801-skill-health-remediation-plan` — PR #90, tip `36ecb760dd2b8202df425c08e9070daac56dc485`, merged 2026-09-02T01:09:26Z
- `docs/v810-cross-file-chapter-handoff-plan` — PR #99, tip `a1f196de78378a0728c7bb0300419d2a5f87bb65`, merged 2026-09-02T09:09:10Z
- `docs/v820-final-review-compliance-plan` — PR #104, tip `fe40113d09346172fa6ba934918dd40a9f74f4c7`, merged 2026-09-03T01:19:31Z
- `docs/v830-editable-mechanism-diagram-plan` — PR #106, tip `5ef3a830f1a24a276790cae76032921934f44fa9`, merged 2026-09-03T07:49:30Z
- `docs/v900-phase-i-i1-migration-contract-final` — PR #141, tip `806eda49cd57d1a13fe2afe0790f08b90d0bff33`, merged 2026-09-07T05:28:29Z
- `docs/v900-phase-i-i2-writer-retirement-readiness` — PR #142, tip `bf5507b56703cc05a580ee17bde5b393eed75424`, merged 2026-09-07T05:42:30Z
- `docs/v900-phase-i-i5-release-closure` — PR #148, tip `d67d8142d0e25f57686fedc12f09123c98e12837`, merged 2026-09-07T09:03:26Z
- `docs/v900-phase-i-readiness` — PR #137, tip `fe1cfd029ddf12829ff1e603fc4be84a369e838e`, merged 2026-09-07T03:58:01Z
- `docs/v900-postrelease-wording-hygiene` — PR #149, tip `2425f2fc0c22887016e1b6f96ab6453c7ee475b6`, merged 2026-09-07T09:35:26Z
- `feat/v900-semantic-identity-binding` — PR #130, tip `b84d60dd7df8a22d4377ad66a3b5105dec508440`, merged 2026-09-06T11:43:25Z
- `feat/v900-semantic-identity-core` — PR #128, tip `9b5a9e351e469504e740ef11445aab88d76ad4a3`, merged 2026-09-06T09:49:36Z
- `feat/v900-semantic-identity-state` — PR #129, tip `f8eaebb979939fbc0df58da281f963f381035f3f`, merged 2026-09-06T10:07:12Z
- `feature/v810-cross-file-chapter-handoff` — PR #101, tip `740906aa43d31235677f5c4148edb3b5737baddf`, merged 2026-09-02T10:29:50Z
- `fix/v8.3.1-author-reasoning-voice` — PR #108, tip `5692acad9b154b150b993905719af713031a2a79`, merged 2026-09-04T04:20:42Z
- `fix/v8.6.1-active-consistency-semantic-drift` — PR #111, tip `b1207ce37ed2e12451cc8c7999af508f6671bb2e`, merged 2026-09-04T14:29:07Z
- `fix/v8.6.1-delivery-record-stability` — PR #113, tip `9bb956fc3b5aed617637bc6bbf3ba662ec6f08f0`, merged 2026-09-04T14:45:58Z
- `fix/v8.6.1-postmerge-status-closure` — PR #112, tip `673055fa8d9fb2a4d091b5425a40aec95ce24378`, merged 2026-09-04T14:41:14Z
- `fix/v8.7.1-ai-declaration-ci-baseline` — PR #118, tip `52dc66454723d6ade2b326d94131c594d93c5174`, merged 2026-09-05T04:58:22Z
- `fix/v8.7.1-ai-statement-template-index-exclusion` — PR #117, tip `bd6b1fb0573445a3d036f7658dd5b360315ae8b3`, merged 2026-09-05T05:04:39Z
- `fix/v8.7.1-readpath-semantic-state-consistency` — PR #116, tip `ae370bee8fead2c35239ea589a22ff9a76aacee3`, merged 2026-09-05T03:14:41Z
- `fix/v8.7.2-template-readpath-release-consistency` — PR #119, tip `94ddedf138a46a4c710d2fef0c3926e260d53b7c`, merged 2026-09-05T07:10:46Z
- `fix/v8.7.4-active-authority-hygiene` — PR #122, tip `ba430b9b1fd530607d50d8148de205cff029bebf`, merged 2026-09-05T09:37:05Z
- `fix/v9.2.1-p7-consumer-alignment` — PR #174, tip `09116ed8c1da25679ce2342ed524a3156a4cb5ba`, merged 2026-09-16T08:50:54Z
- `fix/v9.2.1-p7-regression-lint` — PR #175, tip `80c3f7d5339ca06d9e5b3b155dae7191236a3061`, merged 2026-09-16T09:50:47Z
- `fix/v9.2.1-p7-runtime-truth` — PR #173, tip `77ac31cbaa9540d7f29f92bcd3cc08d8bd37bced`, merged 2026-09-16T05:56:01Z
- `fix/v9.3.1-model-design-capability-restoration` — PR #182, tip `02d4893c0680a338810c5c8caf0a0f341370c98f`, merged 2026-09-18T13:08:34Z
- `fix/v9.3.1-structural-reduction-surface-alignment` — PR #185, tip `3128dfd9c28841ebb09360ecd7bf7d8c3da6d8c1`, merged 2026-09-18T15:22:19Z
- `fix/v9.3.1-task-pack-budget-closure` — PR #183, tip `f0e2f08a4bccb557e36d626a831c0beea8b906e9`, merged 2026-09-18T13:22:45Z
- `fix/v801-generated-main-hardening` — PR #91, tip `8e536abf12b5ae922e2adc2b8707cd3e1afd8466`, merged 2026-09-02T01:16:53Z
- `fix/v803-final-hygiene-audit` — PR #97, tip `75a703f1f6c1061ccd64a4ff8e64601763d3e629`, merged 2026-09-02T04:35:11Z
- `fix/v811-eof-newline-hygiene` — PR #103, tip `04d91640ab07dc2fb669623f628d09d5e591f3f5`, merged 2026-09-02T15:07:44Z
- `fix/v811-skill-authority-pointer-health` — PR #102, tip `9118262785872b18a6f535aefc32849052074492`, merged 2026-09-02T14:56:56Z
- `fix/v900-characterization-baseline` — PR #126, tip `2c2737c800dd1a3e6026442b345143deed201a3a`, merged 2026-09-06T09:14:26Z
- `fix/v900-runtime-assurance-framework-evidence` — PR #127, tip `bd648a7eb3afa41255acac2fa71f7efa673cda77`, merged 2026-09-06T09:23:50Z
- `fix/v900-semantic-identity-surface-closure` — PR #131, tip `5dec1f07a2a84eb571311bc82ba8f27421afdc92`, merged 2026-09-06T12:38:38Z
- `harden/v8.0.1-chapter-capability-preservation` — PR #88, tip `d5583795c816e66e1b2c6549f73d50ca25f1383f`, merged 2026-09-01T06:53:20Z
- `maintenance/v802-entrypoint-slimming` — PR #94, tip `2ece6fdfd9241afc4746dd83493f96abef26fefa`, merged 2026-09-02T01:44:03Z
- `maintenance/v803-health-hardening` — PR #96, tip `7dff37f4d7257a41df330d988e8826aece0aff19`, merged 2026-09-02T04:28:43Z
- `maintenance/writing-runtime-v9-wording` — PR #150, tip `55c69a48d509ef3621cce4157d2768aa2b900dc7`, merged 2026-09-09T04:14:09Z
- `phase-d/state-transition-engine` — PR #132, tip `ccf7323df01ad738cf917a54de0c7874933d1825`, merged 2026-09-06T13:25:55Z
- `phase-e/artifact-naming-migration` — PR #133, tip `0651aee2423db70aaa0f7b808633077d4c6f741e`, merged 2026-09-06T14:15:53Z
- `phase-f/transactional-project-writes` — PR #134, tip `191debc81c478bff376e6482564a7d8f65a71f83`, merged 2026-09-06T15:00:33Z
- `phase-g/competition-writing-runtime` — PR #135, tip `c66f35e7255fbfa988b0d8d827fc8ca42077267c`, merged 2026-09-06T15:38:05Z
- `phase-h/sync-project-mechanical-split` — PR #136, tip `0e2365a8ef138e326d4e4a9455e999d87b1ae95c`, merged 2026-09-07T00:45:21Z
- `refactor/optimization-p1-baseline` — PR #152, tip `37f42089ca104e2586f882a76cf2c034a7279842`, merged 2026-09-15T02:28:46Z
- `refactor/optimization-p2-reading-plan` — PR #153, tip `e3e70dea27a5b7586a5b040640e97c7bf09cf239`, merged 2026-09-15T03:37:05Z
- `refactor/optimization-p3a-core-policy` — PR #154, tip `436abc25ea769490a88ddb5837b2987c21b63f03`, merged 2026-09-15T06:22:20Z
- `refactor/optimization-p3b-writing-roles` — PR #155, tip `883c00662a2cbc82c6a8cf18238e7f091daa323a`, merged 2026-09-15T14:21:20Z
- `refactor/optimization-p4-compact-framework` — PR #156, tip `2b50dfc11f2e67d191dee207c0121473dc7d6d2e`, merged 2026-09-15T14:46:17Z
- `refactor/optimization-p5a-run-config` — PR #157, tip `1cdcb307bcdc4c6aa007f71afb4951db80af6250`, merged 2026-09-15T15:51:33Z
- `refactor/optimization-p5b-run-receipt` — PR #158, tip `65dce8b23fc77482f568d80d11a66aeeda24837b`, merged 2026-09-15T16:22:18Z
- `refactor/optimization-p6a-legend-profile` — PR #159, tip `f27e169f360037e7849c3beab83008ad098c3699`, merged 2026-09-15T17:23:18Z
- `refactor/optimization-p6b-matlab-preview` — PR #160, tip `a68262258bbc1941d310494da098e8bb1fcc86d7`, merged 2026-09-15T17:47:37Z
- `refactor/optimization-p7-conditional-analysis-appendix` — PR #161, tip `aaf144d243ac5f7b394a4d28c01f9dafa5a38660`, merged 2026-09-15T20:37:35Z
- `refactor/optimization-p8a-infrastructure-measurement` — PR #162, tip `29411e81078038e1f84b3525566d1f057085db42`, merged 2026-09-16T00:03:35Z
- `refactor/optimization-p8b-ci-dispatch-surface` — PR #163, tip `9204de7e4e9d95dce13a077f3c1da5280bbc11f6`, merged 2026-09-16T00:19:48Z
- `refactor/optimization-p8b-generated-final-head-dispatch` — PR #164, tip `9523075403734b25bb32e7c4e1703b66f2370840`, merged 2026-09-16T00:25:39Z
- `refactor/optimization-p8c-run-config-parser-final` — PR #166, tip `40843f4b55928c5e4785e8ee32377a1253d31aa6`, merged 2026-09-16T00:50:12Z
- `refactor/optimization-p8d-lint-function-metrics` — PR #169, tip `8adea98b8b7968992bd044e860fde84a7d32622d`, merged 2026-09-16T00:58:11Z
- `refactor/optimization-p8e-validator-no-split-closeout` — PR #170, tip `a98dcd532e9f79e3914f29d45ff1d0c3d564771a`, merged 2026-09-16T01:43:22Z
- `refactor/repository-hygiene-cleanup` — PR #120, tip `dd8526689fecd337cd7c724c3189ad486d9e6ee8`, merged 2026-09-05T07:31:24Z
- `refactor/v8-writing-template-decoupling` — PR #87, tip `4ed9a37ae063928792d5e4582b80778968a02413`, merged 2026-09-01T03:21:06Z
- `refactor/v8.7.3-mechanism-monochrome` — PR #121, tip `9cebf171ab6221493d0a1b85f4f15858c91ac6b2`, merged 2026-09-05T09:00:07Z
- `refactor/v9.3.0-domain-reduction-cues` — PR #179, tip `3bb66e2adcf2bf6a61f0c4049cdf3734a59cf651`, merged 2026-09-18T00:30:47Z
- `refactor/v9.3.0-initial-modeling-core` — PR #178, tip `fc4e31a976e030b82d86f744d0f51648e93386e8`, merged 2026-09-17T23:43:37Z
- `refactor/v9.3.1-active-index-segmentation` — PR #190, tip `6fd687bdc13d1137dd2ea4352bb844274ed0af63`, merged 2026-09-18T16:34:47Z
- `refactor/v900-phase-i-i2-retire-legacy-semantic-writers` — PR #143, tip `235cbe87a2d33190fc7b0de7dd82f8fe64b004ef`, merged 2026-09-07T06:13:25Z
- `refactor/v900-phase-i-i3a-retire-active-artifact-aliases` — PR #144, tip `a93cdd95365d8f4f85d53c34b726b25f86b28c34`, merged 2026-09-07T06:35:35Z
- `refactor/v900-phase-i-i3b-remove-obsolete-artifact-state-fields` — PR #145, tip `4dabf394c6de566418284778f5a5f057c9f91805`, merged 2026-09-07T07:26:21Z
- `refactor/v900-phase-i-i4a-v9-applicability` — PR #146, tip `c26bcb5494c45bcd1ea378d7aa5720ca3e09cbe7`, merged 2026-09-07T07:59:22Z
- `refactor/v900-phase-i-migration-baseline` — PR #138, tip `b3c68f4a999336efb23926380b28bcbc050f4fad`, merged 2026-09-07T04:10:48Z
- `release/v9.2.1-p7-closeout` — PR #176, tip `888aeac0ccf6a9eb3210e620792173660b91f18d`, merged 2026-09-16T11:05:17Z
- `release/v9.3.0-closeout` — PR #180, tip `b956c4c6da964fd5e5c461778a2ed82c5480942e`, merged 2026-09-18T02:27:40Z
- `release/v9.3.1-closeout` — PR #187, tip `3609f424f099ab857e13385d2663151c6fd03ef3`, merged 2026-09-18T15:52:41Z
- `release/v900-phase-i-i4b-release-carriers` — PR #147, tip `f042d1c6fc1c119b3ea2251281fbc283bd692082`, merged 2026-09-07T08:29:35Z
- `upgrade/optimization-p9-v920-release` — PR #171, tip `d1b0b825b69e1177a2e6784a398bd1532a0d8166`, merged 2026-09-16T03:04:47Z
- `upgrade/v7.17-mechanism-structural-validity` — PR #80, tip `3eda3f1da294b86d7b2d8d7a7b87b649572ac60e`, merged 2026-08-29T06:26:37Z
- `upgrade/v7.18.0-model-solution-writing-style` — PR #84, tip `4fd694abf557452f99dbdd6565d9ce28b868b7e2`, merged 2026-08-29T10:27:59Z
- `upgrade/v7.19.0-main-body-writing-closure` — PR #86, tip `6e336c1525a1f1081aa97b9b3ffbb5133087c2e1`, merged 2026-08-30T14:38:18Z
- `upgrade/v8.2.0-final-review-compliance` — PR #105, tip `218c497046bb65d707de3c9ee22ba133a67f516f`, merged 2026-09-03T07:06:16Z
- `upgrade/v8.3.0-editable-mechanism-diagrams` — PR #107, tip `a577902fb0af065d7e1a87577c42472da7193143`, merged 2026-09-03T13:31:43Z
- `upgrade/v8.5.0-author-reasoning-voice` — PR #109, tip `ec57267f567fcb3fe737dc594ae3fa52b80bbc1c`, merged 2026-09-04T09:23:53Z
- `upgrade/v8.6.0-model-construction-solution-rationale` — PR #110, tip `8628d0870e3fe4ee948461cfe3a8b9c78f48ecc0`, merged 2026-09-04T11:35:43Z
- `upgrade/v8.7.0-writing-capability-preflight` — PR #114, tip `9a225e20d79a44d6486afe3f4cd0dcea97bb2921`, merged 2026-09-04T16:52:09Z
- `upgrade/v890-stable-compat-checkpoint` — PR #139, tip `bea2fe7afb85f411bdffd3348031f7fc03eb2cfa`, merged 2026-09-07T05:09:02Z

## 4. MANUAL_REVIEW — merged PR but branch tip differs from PR final head
- `docs/legacy-archive-hygiene` — PR #63; branch tip `84715a0cf2411fd15d9faaa163877c474e7ef4fb`; PR final head `7e29d8965e5d1d4377c3ce84815b823070a5a44f`
- `docs/main-branch-protection-plan` — PR #78; branch tip `cb1ced2b9fb235ff2d3216ee8f509deee2dc0119`; PR final head `d77d70423597771989376e54312bb43c173de911`
- `docs/v7.11-active-template-version-residue` — PR #66; branch tip `a9867d9d07182b2f43d95c85f2a3b342702d8f4e`; PR final head `84763b0f9cde9735e5bca5e82276b031f479d740`
- `docs/v7.11-read-path-approval-closure` — PR #65; branch tip `6dd7bc87cc127ddc9c24ee23774b1baf842f5874`; PR final head `1c100144b4ac475f4080df5c5ed5de878a77091c`
- `docs/v7.12-runtime-read-path-hygiene` — PR #71; branch tip `7ee3171d4b9daffeb415bc502607ae611135786c`; PR final head `9c7115a994b9b4e91de0ef012be4233589e8453a`
- `feat/modular-latex-source` — PR #58; branch tip `c0357f6af0304faa6409028f4492bb7e13dec02f`; PR final head `3416fa91ac243281d6141d5c31cc9b1e3ff18ce5`
- `feat/v7.5.3-writing-governance` — PR #53; branch tip `691c92771e7d5dd0da1162e693a8b2c9104aa102`; PR final head `147c5aea727e8b1fa21a7290109449555487b692`
- `feat/v7.7.0-paper-semantic-governance` — PR #55; branch tip `0131153754608deffb6ac4771b3d2cb5d08dee58`; PR final head `0babfbae56e809eea241a1106708f506df71329d`
- `fix/preprocessing-decision-7.2.1` — PR #34; branch tip `a373089d5e76c36c807ece29cf3549efdd170ab7`; PR final head `a660f631274cac46574cb7e9a04673a64590db58`
- `fix/v6.4.1-active-residue-cleanup` — PR #23; branch tip `dac16a7d0b962d1e8b4f32ad453db63856a9f9fb`; PR final head `e48d2a504f74743cc84c21b23eac8e9eeca145b6`
- `fix/v6.5.1-active-residue-cleanup` — PR #25; branch tip `b0c23b323af15c38fce85e6b438fea37ab42c5e3`; PR final head `e5db36316cd334a42fb4d3c71a6740c16383d789`
- `fix/v6.6.1-active-residue-cleanup` — PR #27; branch tip `9dac0e872a1de7c6242011ae93904e56741e6dae`; PR final head `e220a9fdc3a029b00fd65c132c239238a9c5ff42`
- `fix/v6.6.1-code-quality-closure` — PR #28; branch tip `d64639949a746f44123c40f2b1453e5d14292ff6`; PR final head `11cfa3717dcc2004dc253108fa7b3f41ce652a53`
- `fix/v7.0.0-separate-analysis-code` — PR #29; branch tip `a4492102a95f8ddef8c53170c1000e877f43c893`; PR final head `7b6740268c7b67031c857507fb328f0f517e6ecb`
- `fix/v7.0.1-stage-boundary-closure` — PR #30; branch tip `424d1e9018517c3ba978965425e9a3815f89c408`; PR final head `a83933189cb0bb1240216566c9f19d2061c66cc3`
- `fix/v7.1.1-release-note-governance` — PR #33; branch tip `b675ebe33fbd65dfeb85724228244a9d687deb30`; PR final head `54233fe55989d5a0ee8569c8a8a0f7dcc8d2ac9f`
- `fix/v7.2.2-generic-preprocessing-judgment` — PR #35; branch tip `b1ef991797e2fcc02e5d847ec1965f830c567612`; PR final head `2c3fff7cb9dc9b3d13e81f76376c2cdde2c45e87`
- `fix/v7.2.3-preprocessing-paper-evidence` — PR #37; branch tip `d0f5e6dcb92be940c253d3862057643f0b0c4f52`; PR final head `051fbf397fb42bb8ecd96771a37ff34edd634943`
- `fix/v7.2.4-preprocessing-figure-gates` — PR #38; branch tip `4751d0029c59e1a9272f4b2171db693c80038aa9`; PR final head `52647f4bc291045d92ab80e375799dcca00cc569`
- `fix/v7.2.5-preprocessing-runtime-closure` — PR #39; branch tip `6745079a9de4ff5b1e26a60c3fe58860c054921d`; PR final head `18cb25e54243e810479861444de84232375aae04`
- `fix/v7.2.6-active-consistency-cleanup` — PR #40; branch tip `9841374d1bc52882a34e1971fbc3c55a98c10c14`; PR final head `d0cb1cb683b740208170b3bafa1ef390dde4319a`
- `fix/v7.2.6-framework-project-memory` — PR #41; branch tip `6ff19d9a96d91cac38997eedcfb10245fdf98098`; PR final head `03e87ec8510700fef56c14d71ff9ddfb7a4a7b55`
- `fix/v7.4.1-skill-closure-hygiene` — PR #44; branch tip `b644eba6485dd774e72c90f263fed892e4d2a52c`; PR final head `45f59a13230d0fe7084380be7b7407c69a6223d9`
- `fix/v7.4.2-dynamic-figure-layout` — PR #45; branch tip `b8ef58b8d2335b6f398da8e7986b2eadba6248c0`; PR final head `2fd022b410e4cab876ee8ac079eba5cfd3aea2a1`
- `fix/v7.4.3-read-path-closure` — PR #46; branch tip `b06e4384867606183f1edaf268641b973255d36d`; PR final head `f9f935df4ca7b9442d9657fbf27d7f3a3813b4f9`
- `fix/v7.4.5-writing-contract-prose-audit` — PR #49; branch tip `2707ee2ac057d187ae20ab976c34b7939a7e2fb4`; PR final head `e42afc2bc7f50aefb0165eb51e2ab4294b60c29e`
- `fix/v7.5.1-architecture-slimming` — PR #51; branch tip `22121f2d4bd972728dfe3cea268af4abea9d569e`; PR final head `14ea8876ceb96bebc4d858432703661d0e9f8302`
- `fix/v7.5.2-entrypoint-parity` — PR #52; branch tip `f2a8e7b7c56d4d0b70833c041d4861b042dc5d24`; PR final head `68b00e6c92ac03cb78660e030f27c97c89f77241`
- `fix/v7.8.1-algorithm-closure` — PR #57; branch tip `f38e83b5c9c108633958cd4ce0fa437a53f21f3c`; PR final head `735f556aba4f9ca4db25aba6327e9b284d109351`
- `fix/v7.10.1-read-path-closure` — PR #61; branch tip `9cdf42d1e40498ced20b57b0fd2e9608a0b5e613`; PR final head `9bd132aea32a95dfb5681a070110f6bc63b36f84`
- `fix/v7.11.2-runtime-health-coherence` — PR #69; branch tip `f18341d8649852e499c6b636621df27f2612ebb2`; PR final head `0f5ecfcc581ed8b339738aaef416cde5a0c7e012`
- `fix/v7.13-figure-stabilization` — PR #73; branch tip `c3ed86c956ba476e3ea0fc1dfd193ca2da241d70`; PR final head `9db431ce0f5a698c9bba7a84c35c56bd50c429aa`
- `fix/v7.14.1-skill-health-hygiene` — PR #75; branch tip `fdf891052053bdf74016ec9165da21e321d9be89`; PR final head `a3bc23e685dbca8662dce1db2f7db752571dc3cd`
- `fix/v7.14.2-chart-selection-degeneracy` — PR #76; branch tip `ff966ee3a3aa14fba2df9b4a8a67bbb6047b0335`; PR final head `a9e7f14822ca31ad94b7480d7e957c024d302e8a`
- `refactor/docx-opt-in-stable-filenames` — PR #22; branch tip `cf158502289fd1ae319f5836f68c9b099541d651`; PR final head `15fc3202a311a5af4bba6f0f6a523e64c43da4e9`
- `refactor/v7.1.0-repository-residue-cleanup` — PR #32; branch tip `43fe0293e11547ee3c517f639110890e3e1f95bb`; PR final head `e226820d81c6ef8cb5ff018464436709be401a58`
- `refactor/v7.11.1-authority-single-source` — PR #68; branch tip `4bc9a7c56f79f617427c43eeac9c152a2dceeab3`; PR final head `c2f85355deb38bc43a387374e02bc362b90c2eab`
- `upgrade/v6.5.0-user-executable-full-code` — PR #24; branch tip `a1f922951131a8ed350a90039fed03071d1e2963`; PR final head `56acf1c3178253d485d89801dfcd1021b6faace6`
- `upgrade/v6.6.0-self-contained-question-folders` — PR #26; branch tip `5e7b55ff7948397f07a0f8902544ac5aa2a461b3`; PR final head `a40f6169bdec6dfb8dafe3d6a6ee673aa3180c1e`
- `upgrade/v7.1.0-semantic-governance` — PR #31; branch tip `dbf03cd97fd22c07b14c44ff47f7486f19e58f87`; PR final head `f78b6419567e8a617bcb97c3862f7f11e14c3340`
- `upgrade/v7.3.0-writing-expression` — PR #42; branch tip `9dc6724506cbc4f8ab9ca382b6f10f8e8ffd3e07`; PR final head `91db64b0b848b48c3f63439c7e3bc310c94940c9`
- `upgrade/v7.4.0-writing-evidence-architecture` — PR #43; branch tip `8d69883ead8da28eda4d398c3a3231188990d0b3`; PR final head `d949155afc569a562ee6da6d9ba73c79e120faea`
- `upgrade/v7.4.3-writing-structure-style` — PR #47; branch tip `64327635a10abd07f944f88c0e81a1cda8967aa1`; PR final head `706d760eee078403676a6c4f59a8f7cde70ba4a0`
- `upgrade/v7.4.4-natural-paper-flow` — PR #48; branch tip `7d61c6fc4010a29a5f1fc55a40836c8364d6eb78`; PR final head `57e01959451bd93b5917fad07e5901175cba446e`
- `upgrade/v7.8.0-algorithm-presentation` — PR #56; branch tip `37a5b116980d6c03fb4787f46048e0079b2b81f7`; PR final head `8d9812269077c59121e9ed22985dede1dc0ce32b`
- `upgrade/v7.9.0-latex-runtime-closure` — PR #59; branch tip `db2ba5480ad1b85b2cb0ce81b3534b6a7d54957d`; PR final head `b5803adfbcad14d3c77d5e512bad004f30867b8a`
- `upgrade/v7.10.0-delivery-attestation` — PR #60; branch tip `93066a6a8f5e199b7279583d0baf7ff1074d8516`; PR final head `bc50c8c4d013fa8824a3f6594e49f55d2c7251ff`
- `upgrade/v7.11.0-model-approval-gate` — PR #64; branch tip `9fa705a26255fd55e530fa3762e40435d5ddefbf`; PR final head `962812dc60c2341cb4b1a02a530a33c19b3568df`
- `upgrade/v7.12.0-declarative-runtime-assurance` — PR #70; branch tip `65a0553f22f06e259aeb949e2b71120f9f4f3681`; PR final head `118e9e9d6bb71979b8881e899ad16305cf0b11d1`
- `upgrade/v7.13.0-figure-enhancement` — PR #72; branch tip `3543a75505802d537af0e9451e9347685ccc7145`; PR final head `0c84829da03114c16a144f604a1274e0a6956aee`
- `upgrade/v7.14-primary-numerical-validity` — PR #74; branch tip `2f94814945cc55ec785a528d7b699a0fc19c69ff`; PR final head `f5fa7501a1144505996246f131afe59310f27f48`
- `upgrade/v7.16.0-paper-writing-spec` — PR #77; branch tip `82db46bbfdc8bf7f742bec9fac4f206187a6f177`; PR final head `a6e721f3e9a873208f5e8b49d72b214d6eee780a`
- `v7.5.0-writing-reasoning` — PR #50; branch tip `03cc165e7ee10cb49e240e66d7c07c0fa8a77dd9`; PR final head `6baf8fece364a614ac34a9cfbbde3c523f12ec20`

## 5. MANUAL_REVIEW — closed but unmerged PR
- `agent/v6.4.0-latex-first-zero-comments` — closed PR #21; tip `2078546815925ad76616408afc034b3702c4461b`
- `docs/v900-phase-i-i1-migration-contract` — closed PR #140; tip `806eda49cd57d1a13fe2afe0790f08b90d0bff33`
- `feat/v7.2.3-preprocessing-visual-evidence` — closed PR #36; tip `c9d5b3d70cfd14979f61ef8a4d03aaaec8e45025`
- `maintenance/p8c-run-config-parser` — closed PR #165; tip `5fd0c5307435a224a74a54da970feaa476d2cfa7`
- `refactor/optimization-p8d-lint-structure-measurement` — closed PR #168; tip `f794ab856ad24067be822c6d9d12a526e301bcfb`
- `test/v900-refactor-characterization` — closed PR #125; tip `f83739836d96c866283b36ae917d8536cb721629`
- `upgrade/v7.7.0-paper-semantic-governance` — closed PR #54; tip `0c84d3319f3e964b2332684f3604719fb23ce6ec`

## 6. MANUAL_REVIEW — no PR association
- `docs/main-protection-status-record` — tip `b75feb8be1ca79694237e12242e7e48172807dd4`
- `feat/v7.2.3-data-process-visual-evidence` — tip `a18e0294398b057f2020af85a03edcb5700b6212`
- `fix/v7.12-default-runtime-ci-smoke` — tip `acf3128bd90493fd712aa761d4bce4db2eed6748`
- `maintenance/p8c-drift-rebaseline` — tip `40843f4b55928c5e4785e8ee32377a1253d31aa6`
- `maintenance/p8d-validator-split-transform` — tip `6e467bd3aac3db56136e75f4b39a93f38d137f69`
- `maintenance/v803-core-summary-vocabulary` — tip `2a5477cf6a0a44576fc3f93c6983268cc1e55cfd`
- `refactor/optimization-p8b-run-config-parser` — tip `d2c4f199b7c133add8d78e8d0995c4d10d44b6d4`
- `refactor/optimization-p8d-validator-split` — tip `d8fc5a9868f11d95d9c424619383d10bb89d45d6`
- `refactor/v9.3.0-release-metadata-refresh` — tip `3767804c47ff83c5c22b5f255d597692739e99f4`
- `refactor/v9.3.1-release-metadata-refresh` — tip `bb5d51a7c17d4ebf2e116bfe7b36f22640ea8f7c`
- `refactor/v900-state-transition-engine` — tip `706fc842fa30f5dc3093b70e312dc51b8c2b4051`
- `release-v7.5.0-closure-prep` — tip `ccd553780b9f239ce958a27ab263d466b986fdab`
- `release-v7.5.0-prep` — tip `0bf969e0d2d1fb2fb4e595175f9961beeba3decc`
- `test/v900-phase-i-migration-baseline` — tip `98c82a22e2e92cadec01050195529e8092b81ae2`
- `upgrade/v7.5.0-reasoning-closure` — tip `03cc165e7ee10cb49e240e66d7c07c0fa8a77dd9`
- `upgrade/v7.5.0-release-finalize` — tip `e3927fe789a2abffc065af42aa2115cdf368ab82`
- `upgrade/v810-cross-file-chapter-handoff` — tip `19f9e89e6ffc29d675efa9c8b2d853ca7f821992`
- `v7.11.1-authority-consolidation` — tip `cb1fb1149be324b85016dfb0c1ac0e1d4f259ee9`
- `v7.11.1-authority-consolidation-final` — tip `fd2d7072215a7232dd4d704d86028e5e394ae4d3`
- `v7.11.1-stabilization` — tip `d4918daf1592ff32a1eea18a5ab5f314708decce`

## 7. KEEP
- `docs/v9.3.1-branch-cleanup-manifest` — current H2 working branch
- `main` — default branch

## 8. Tool capability boundary

The connected GitHub tool surface in this chat exposes branch creation/update, file writes, PR operations and merge operations, but **does not expose a delete-ref / delete-branch action**. GitHub fetch is GET-only. Therefore this manifest prepares and revalidates the deletion cohort, but the assistant cannot honestly claim that remote branches were deleted through the current connector.

Actual deletion must wait for a GitHub connection/tool surface that supports deleting refs, or be executed by the repository owner outside this chat. No branch is force-moved or repurposed as a substitute for deletion.

## 9. H3 disposition

H1 semantic index segmentation already separates active runtime/reference files from maintenance, migration and historical provenance while keeping every path and MANIFEST coverage stable. Therefore physical docs migration/deletion is currently **DEFERRED_NOT_NEEDED_AFTER_H1**. Re-open H3 only if future search measurements show the segmented index is insufficient.

## 10. Revalidation requirement before actual deletion

Immediately before deleting any branch from Section 3, re-fetch current branch tip and PR state. If the tip changed, a new/open PR appeared, protection changed, or a retention request exists, remove it from the deletion cohort and classify it for manual review.
