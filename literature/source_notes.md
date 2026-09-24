# Literature source notes and closest-work delta

## Historical ancestor

Suh and Devadas (DAC 2007) define PUF-based authentication and secret-key generation around physical challenge-response behavior, discuss unused challenge-response pairs, response correlations, noise and public assistance, and provide device-oriented evidence. The legitimate reuse here is motivational: challenge labels are not automatically independent secrets, and public information/noise must enter the security account. Their paper does not supply the affine-shadow lemma, the exact worst-code multi-ball quantity, the sequential product certificate, the one-time average-min-entropy transfer, or the BSC/coset recurrence used here. Those require new proofs under the present declared finite model.

## Established foundations that narrow the claim

Fuzzy extractors and reusable fuzzy extractors already address stable key derivation from noisy, nonuniform and repeatedly observed sources. Generalized gain functions already cover approximate and multiple-guess adversarial objectives. Channel-mixture methods already use input-independent components. Accordingly, the manuscript does not claim a new general notion of entropy, leakage, extraction, or channel decomposition. It claims a specialized, mechanically evaluable conditional false-accept bound for affine raw-response tests with Hamming tolerance, bounded retries and explicitly declared observation channels.

## Closest venue work

The twelve TDSC papers in `source_matrix.csv` cover computational fuzzy extraction, helper-data attacks, physical entropy/reliability, trial-and-error reverse authentication, multiple PUF authentication/AKE protocols, OS integration, tag architectures and modeling-attack-resistant PUF design. Their evidence is often hardware-, protocol- or deployment-centered. This project has none of that evidence and therefore makes none of those physical or full-protocol claims. Its distinctive object is the conditional event probability for a user-declared finite affine channel: residual rank selects a sharp worst-code Hamming multi-ball hazard, rejection histories compose sequentially, and independent-BSC observations admit a coherent/coset refinement.

## Newest close work: Panja, Tripathi, and Safavi-Naini (2025)

The 2025 PUF-AKE paper reports attacks on earlier PUF authentication/AKE proposals, including schemes represented in the TDSC calibration set, then develops entropy-aware reusable robust fuzzy extraction and post-quantum authenticated key exchange. Its source model, construction goal and security notion are materially different from the present work. It establishes computational AKE/mAKE properties under cryptographic assumptions and reports APUF-oriented experiments/simulation. The present work neither constructs AKE nor estimates hardware entropy; it assumes a declared finite affine raw-response model and bounds information-theoretic eventual false acceptance.

The reverse non-subsumption is also limited and precise: the 2025 paper does not present the exact minimax identity between rank-only affine-code risk and `M(r,t,q)`, nor the particular shadow-fiber/coset recurrence for sequential Hamming-tolerant retry trees. This comparison supports a non-identity claim, not priority. A broader or unpublished result could still overlap; no claim of being first, optimal in all models, or venue-level novelty is made.

## Adversarial reading retained in the manuscript

1. A new challenge name may encode no new linear information.
2. Rejection makes later risk conditional and can create non-affine posteriors.
3. A rank-only bound loses code geometry and rejected-region geometry.
4. Giving analytical BSC flags can reveal more information than the real channel.
5. Independent marginal BSC descriptions are unsound for correlated errors.
6. Finite exhaustive checks validate only the declared bounded families.
7. Physical entropy, device reliability, unclonability and protocol AKE security need evidence absent here.

## Access and licensing

Full texts were read from publisher pages, author-hosted manuscripts, institutional repositories, IACR ePrint, or arXiv as recorded in `source_matrix.csv`. Those papers are cited, not redistributed. The repository contains no third-party paper PDF. Open licenses are recorded only where the source explicitly exposed one; lack of a recorded open license means citation-only use.
