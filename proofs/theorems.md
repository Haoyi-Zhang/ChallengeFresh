# Affine noisy-identity certificates: mathematical arguments

These are written proofs, not proof-assistant certificates. The executable checks cover finite instances only. All vector spaces are over F_2; logarithms are base two. The identity dimension is d, output length n, and Hamming tolerance t. A public affine offset can be absorbed into an adversary's candidate, so matrices suffice below.

## 1. Games and histories

An identity X lies in F_2^d. Initial finite side information Z is arbitrary. The reference law U makes X uniform and independent of Z. A public transcript contains adaptively selected matrices, observation outputs, and guess/rejection events. At an observation, the public matrix L and kernel K_h are chosen using only the public history and independent coins, and the observation has law K_h(o | L X). At an epoch, a fixed matrix A and tolerance t are tested against at most q guesses; only the acceptance bit is returned, and the experiment ends at the first acceptance. There is no other secret-dependent output during an epoch. After all rejections the protocol may select another epoch or an observation. The horizon is finite.

The shadow S at an epoch entrance contains the row spaces of all earlier observation matrices and all response matrices used in completed unsuccessful epochs. Certificate histories are evaluated at observation or epoch entrances, after all earlier tested response maps have been charged. They do not include partial-retry states as fresh fiber states. S is a proof variable; the actual observer need not know S X. For the noise refinement, only the analytically revealed observation rows are inserted. Its proof history includes the earlier analytical flags as well as the public transcript; the fiber lemma is applied to this enlarged history, not to a marginal history that has forgotten flags. The innovation is r = rank(S; A) - rank(S), where the semicolon stacks rows. Necessarily 0 <= r <= min(d-rank(S),n).

## 2. Shadow-fiber lemma

**Lemma 1.** Fix Z=z, all independent adversary coins, a positive-probability live history h at an observation or epoch entrance with all prior response maps charged, and a feasible shadow value S X=s. Use the full-revelation shadow with the public history, or the flag-refined shadow with the history enlarged by earlier analytical flags. Under U, X is uniform on the affine fiber {x:Sx=s}.

**Proof.** Follow the particular history. In the full-revelation case, every earlier kernel likelihood K_{h'}(o | Lx) is constant on the final S-fiber because every row of that L lies in S. In the flag-refined case, fix the earlier flags: the flagged rows lie in S, and erased outputs contribute input-independent likelihood. Thus observation factors are constant in both cases. Every earlier rejection indicator is constant on the fiber because its response rows lie in S. Public choices and independent coins are fixed. Multiplying these factors gives equal likelihood for every x in the fiber under the uniform reference prior. Conditioning preserves uniformity; zero-likelihood fibers are excluded. This proves the invariant inductively under adaptive choices. The posterior conditioned only on the public history is generally a mixture of such fibers, with analytical flags retained in the proof branches. During a partial retry, rejecting one exact guess from a uniform four-element source leaves three points, so this boundary lemma cannot be reapplied there. QED.

During a partial retry epoch, the response map is not yet in S. Rejecting one exact candidate from a uniform four-point identity then leaves three points even conditional on the current shadow. The lemma does not apply there. It applies at node entrances; the whole-epoch union argument below does not invoke it again after each retry.

The image of an S-fiber under A is an affine code of dimension r: the restricted linear map A:ker S -> F_2^n has rank rank(S;A)-rank(S), and all image points have equal-size preimages. Thus A X is uniform on that affine code when the entrance fiber is fixed.

## 3. Exact multi-ball lifting

Write B_t(y) for a radius-t Hamming ball in the indicated cube, and let

M(r,t,q) = max_{y_1,...,y_q in F_2^r} |union_j B_t(y_j)|,

with M(r,t,0)=0. For q>=1, M(0,t,q)=1 and M(r,t,q)=2^r when t>=r. Repeated centers are allowed and never improve a union. Let v(r,t,q)=M(r,t,q)/2^r.

**Lemma 2 (worst-code lifting).** If C is any rank-r affine subspace of F_2^n, then the intersection of C with any q ambient radius-t balls contains at most M(r,t,q) points. This upper bound is attained by some rank-r affine code for every n>=r.

**Proof.** Choose r information coordinates J such that projection pi_J is injective on C. It is a bijection from C to F_2^r, up to the affine translation. Projection cannot increase Hamming distance. The image of the intersection is therefore contained in the union of the q projected radius-t balls, which has at most M(r,t,q) points. Injectivity gives the same bound before projection. For equality choose the coordinate code F_2^r x {0}^{n-r} and pad maximizing cube centers with zeros. Its distance from each padded center is exactly the projected distance. QED.

This is an exact minimax statement over the class of codes with the specified rank, not an equality for each code. For example, at n=3,r=1,t=1,q=1, a coordinate code has success probability 1 while {000,111} has probability 1/2.

**Lemma 3 (monotonicity).** For fixed t,q, v(r+1,t,q)<=v(r,t,q).

**Proof.** Split the (r+1)-cube by its last coordinate. In each slice, projection of a union of q radius-t balls is contained in q radius-t balls in the r-cube. Each slice contains at most M(r,t,q) covered points, so M(r+1,t,q)<=2M(r,t,q). QED.

For q=1, M is the ball volume B(r,t)=sum_{j=0}^{min(r,t)} binom(r,j). For q=2, antipodal centers prove M(r,t,2)=min(2^r,2B(r,t)): when 2t<r their balls are disjoint, and when 2t>=r they cover the cube. At odd r with 2t=r-1 they are both disjoint and exhaustive.

## 4. Retry epochs and sequential composition

**Lemma 4 (epoch hazard).** At the entrance of any live epoch satisfying the game above, under U the conditional probability of an acceptance during the whole epoch is at most v(r,t,q).

**Proof.** Fix the history and an S-fiber. Follow the strategy's all-reject branch. This determines at most q candidates. Since success terminates the experiment, the event of any success is precisely the union of the acceptance sets for those candidates; behavior after a success is irrelevant. The image of the fiber is uniform on an affine rank-r code. Apply Lemma 2 and divide by 2^r. The same bound holds on every feasible fiber, so averaging over the conditional fiber distribution preserves it. Finally average independent adversary coins. No independence between attempts, or between successive posteriors, is assumed. QED.

**Theorem 1 (uniform stagewise product).** Fix constants v_1,...,v_m. If, for every stage i and every live public history that reaches that stage, the next epoch's conditional hazard is bounded above by the same fixed value v_i, then

Pr_U[win] <= w = 1 - product_i (1-v_i).

**Proof.** If p_i is the probability of still being alive before epoch i, Lemma 4 gives p_{i+1}>=p_i(1-v_i). Starting from p_1=1, induction bounds survival below by the product. This reasoning permits adaptive maps only when each stage retains its stated uniform bound over all live histories reaching that stage. For sharpness over the declared class, use disjoint coordinate blocks of sizes r_i, use optimal q_i-ball covers, and use no additional observations. The acceptance events depend on independent coordinate blocks; the product is attained whenever the latent dimension can hold the blocks. QED.

A history-dependent path value cannot be substituted for a fixed stage-wide v_i. As a finite witness, let one public fair bit choose between one exact guess of two fresh fair bits (conditional risk 1/4) and one exact guess of one fresh fair bit (conditional risk 1/2). The overall risk is (1/2)(1/4)+(1/2)(1/2)=3/8. A uniform one-stage bound may use v_1=1/2. The pathwise admission theorem below certifies alpha=1/2 on both branches; recovering the sharper 3/8 requires averaging the fair public branch in the complete recurrence. The executable witness is retained in `results/cases/path_budget_witness.json`.

**Theorem 2 (adaptive admission filter).** Let v_i in [0,1] be predictable at the live history before epoch i and upper-bound its conditional acceptance probability under U at every such history. Let 0<=alpha<1, and admit an epoch only when the running product of (1-v_i), including that epoch, is at least 1-alpha on every live permitted path. Then Pr_U[win]<=alpha.

**Proof.** Let P_j be the admitted product up to step j and A_j the event of remaining alive. Define Y_j=1_{A_j}/P_j, with the product fixed after stopping. Given a live past, the next conditional survival is at least 1-v_{j+1}; hence E[Y_{j+1}|past]>=Y_j. The finite horizon gives E Y_T>=Y_0=1 by iterated conditional expectation. On live terminal paths, P_T>=1-alpha, so Y_T<=1_{A_T}/(1-alpha). It follows that Pr(A_T)>=1-alpha. No optional-stopping limit argument or infinite horizon is used. QED.

## 5. One global entropy deficit

Average conditional min-entropy is defined by 2^{-Htilde_inf(X|Z)}=sum_z max_x P(x,z).

**Theorem 3 (one-time average-min-entropy transfer).** Suppose Htilde_inf(X|Z)>=k and a reference bound w holds for every independent initial Z-law and the same allowed policy. Then

Pr_P[win] <= min(1, 2^{d-k} w).

If P is within total variation epsilon of a normalized law Q with that entropy property, the bound is min(1,2^{d-k}w+epsilon).

**Proof.** Put m_z=max_x P(x,z), M=sum_z m_z, and nu(z)=m_z/M. Let mu(x,z)=2^{-d}nu(z), so X is uniform and independent of Z under mu. Pointwise P(x,z)<=m_z=(2^d M)mu(x,z). The entire interactive experiment, including all adaptive decisions and noise, is a single stochastic kernel from (x,z) and the independent coins to a terminal outcome. Applying the same kernel preserves pointwise measure domination. Thus Pr_P(win)<=2^d M Pr_mu(win)<=2^{d-k}w. This charges the entropy deficit once to the terminal event; applying it separately to every epoch would unnecessarily compound the loss. Total variation cannot increase through a stochastic kernel, giving the additive epsilon term outside the multiplier. QED.

For constant Z and a fixed coordinate-block winning set E of uniform mass w, this is sharp over distributions with maximum point probability 2^{-k}. If |E|2^{-k}<=1, assign each point in E mass 2^{-k} and distribute the remaining probability over the complement without exceeding the cap. If |E|2^{-k}>=1, support the whole distribution on E with the same cap. Such distributions exist because 2^d 2^{-k}>=1. A cap rather than an exact equality of entropy is the theorem's assumption.

## 6. Noise-sensitive observation rule

For a binary symmetric observation bit with error eta, let rho=|1-2eta|. Independently of the input, choose a flag F with probability rho of being one. If F=1 output the input bit for eta<=1/2, or its complement for eta>1/2. Otherwise output a fresh independent fair bit. Directly, the error probability is (1-rho)/2 for eta<=1/2 and rho+(1-rho)/2 for eta>1/2, in each case eta. Giving the flags to the analysis is a refinement of the original channel. This is a standard randomizer decomposition, not a new channel identity.

For m conditionally independent observation errors, let I be the set of flagged coordinates, with probability p_I=product_{j in I}rho_j product_{j notin I}(1-rho_j). Let f_o(S') be a certified lower bound on eventual survival in the public-output-o continuation, valid for every feasible shadow value. Define S_I=span(S, {L_j:j in I}). Then the refined observation recurrence is

f_obs(S) = sum_{I subset [m]} p_I min_{v in F_2^I} [2^{-|I^c|} sum_{u in F_2^{I^c}} f_{(v,u)}(S_I)].

Here (v,u) inserts bits at their original positions. Complementing flagged coordinates merely permutes the values over which the minimum is taken. The implementation strengthens the rule by taking this minimum only over the projected image of L, with the known complement applied. These are all globally feasible revealed signals; excluding other bit patterns is sound because their probability is zero. It does not assume a particular unobserved shadow value.

**Theorem 4 (flag-recurrence soundness).** Together with f_stop=1 and f_epoch(S)=(1-v(r,t,q))f_next(span(S,A)), this recurrence lower-bounds survival under U. Therefore 1-f_root is an eventual-success upper bound, to which the one-time average-min-entropy transfer theorem above applies once.

**Proof.** Induct backward over the finite protocol tree. The stop case is exact. The epoch case is Lemma 4 followed by the continuation guarantee on every all-reject fiber. At an observation, condition on a fixed flag set I. Erased outputs U are uniform and independent of X and the revealed output V. Conditional on I,V,U and the augmented shadow value, the fiber invariant holds: a flagged bit imposes a linear constraint and an erased bit contributes a likelihood independent of X. By induction the continuation survival is at least f_{(V,U)}(S_I). Average U first. Whatever the conditional distribution of V, the remaining average is at least its minimum over v. Then average the input-independent flags. All operations preserve a lower bound. QED.

The minimum outside the average matters. Pure noise (all rho_j=0) takes the actual uniform average of public continuations rather than charging their worst branch. The flags are proof-only and must not be reported as measured physical erasures.

For exact coverage values, this bound is never worse than charging every observation row. Lemma 3 implies that adding shadow rows cannot increase certified survival: innovation can only decrease, and future shadows remain nested. Backward induction shows that every refined continuation is at least the smallest full-revelation continuation. Weighted averages preserve this inequality. This dominance is relative to the branch-oblivious full-revelation rule, which minimizes over every syntactic output. A stronger full-revelation baseline uses the actual observation kernel:

f_full(S) = min_{w in image L} sum_o K(o|w) f_o(span(S,L)).

It is sound because conditioning on the full signal w makes the charged fiber uniform, after which the public output follows K. The per-flag minima in the refined rule can lose coupling between different flag sets, so refinement need not dominate this stronger rule. The implementation takes the minimum of independently sound success bounds, also covering transitions between exact and conservative cover-table regimes.

The difference is witnessed by the supplied coupling case. First reveal two latent bits exactly, then observe them through independent BSC(1/4) errors. Depending on the two noisy output bits, make respectively 4, 1, 3, or 3 exact guesses on two independent fresh bits. The full-channel bound is 51/64; the uncombined refinement bound is 53/64; their combined bound is 51/64; and the exact game value is 11/16. Thus the stronger baseline is not suppressed in a comparison favorable to the new rule.

A useful closed-form special case is a single exact guess of uniform X after observing L X through independent BSC(eta) noise:

Pr[guess X] <= 2^{-d} E_I[2^{rank(L_I)}].

If the m rows of L are independent, this is 2^{-d}(1+rho)^m = 2^{m-d}(1-eta)^m for eta<=1/2, and it is exact by maximum-likelihood guessing. With dependent rows it can be strict. This is a rank-generating polynomial specialization, not a newly invented polynomial invariant.

Independent error bits are essential to this rule. For X uniform on two bits and one fair error E shared by both bits, O=X xor (E,E) reveals the parity of X. The exact guessing probability is 1/2. Treating the two marginal BSC(1/2) channels as independent would give 1/4. The general full-revelation rule is still sound for this correlated kernel.

## 7. Exact cover enumeration

Translate the first of q centers to zero. Each coordinate is now described by one of m=2^{q-1} column patterns among the other centers. Let a_p be the number of coordinates with pattern p; sum_p a_p=r. Coordinate permutations preserve all distances, and every center tuple has one of these profiles. Conversely, each profile reconstructs a center tuple. Therefore maximizing over all weak compositions of r into m parts is exhaustive (although some profiles are further symmetry-equivalent).

For a cube point, let w_p count its one-bits among the a_p coordinates. There are product_p binom(a_p,w_p) such points. Its distance to the zero center is sum_p w_p; for center j>0, add a_p-2w_p for every pattern having bit j-1 set. The smallest of those q distances determines every radius-t union membership. Summing multiplicities by smallest distance yields an exact histogram; its entries sum to 2^r. Taking cumulative maxima over every profile gives M(r,t,q) for every t.

There are binom(r+m-1,m-1) profiles. The total number of inner weight vectors over all profiles is binom(r+2m-1,2m-1), since sum_{a>=0}(a+1)z^a=(1-z)^{-2}. The algorithm is polynomial in r for fixed q, but its degree grows exponentially in q. A maximizing profile alone certifies a lower bound; exactness also requires exhaustive profile coverage and the counting proof. The code guards q<=4 and bounded r rather than silently extrapolating.

## 8. Rank budget and balanced allocation

Every increment of the shadow adds its innovation. Telescoping rank gives sum of all epoch innovations plus all observation innovations <= d. This is a finite resource bound for the declared raw affine-response certificate, not an impossibility theorem for computational MACs or reusable fuzzy extraction.

For one guess per epoch and common radius t, let F_t(r)=1-B(r,t)/2^r. This is the probability that r fair bits contain at least t+1 ones. Its first differences are a_j=binom(j-1,t)2^{-j} for j>=t+1, the mass of the time of the (t+1)-st one. For j>=t+1, a_{j+1}/a_j=j/[2(j-t)] is nonincreasing. For r>=t+1, write lambda=a_{r+1}/a_r. Since lambda a_j<=a_{j+1} for each earlier j, lambda F_t(r-1)<=F_t(r). Multiplying by a_r gives a_{r+1}F_t(r-1)<=a_r F_t(r). Using F_t(r)=F_t(r-1)+a_r proves F_t(r)^2>=F_t(r-1)F_t(r+1); zero initial values cause no exception. Thus F_t is log-concave.

When a+2<=b and a>=t+1, log-concavity gives F_t(a+1)F_t(b-1)>=F_t(a)F_t(b). Repeatedly transferring one rank unit from a largest to a smallest block shows that balanced integer ranks (differing by at most one) maximize product_i F_t(r_i) under a fixed sum R and fixed number m of epochs. If R<m(t+1), every allocation has a block of rank at most t and hence product zero. No corresponding optimal allocation theorem is asserted for unequal radii or q>1.

## 9. What the arguments do not establish

The shadow refinement can discard valuable rejection geometry. Repeating the same rank-three map in a later epoch makes its new innovation zero and yields the upper bound one, although four exact distinct guesses on the original cube succeed with probability one half. Keeping those guesses in one epoch avoids that loss. The BSC refinement can reveal more information than the actual channel. A coordinate-code worst case need not describe a measured device. The source entropy cap, map declarations, observation independence, trusted acceptance rule, and epoch discipline are assumptions supplied to the checker, not facts learned by it. No theorem in this file establishes hardware unclonability, practical reliability, peer-reviewed novelty, machine-checked general correctness, or full protocol key security.


## 10. Coherent signal and affine-coset observation rules

**Theorem 5 (coset soundness and exact-domain hierarchy).** The coherent and affine-coset recurrences below are sound under the declared independent-BSC model. In the exact local-coverage domain, their complete risks satisfy `B_C <= B_H <= min(B_R,B_F) <= B_0`.

Let the old proof shadow be S and a new observation have linear map L. For each independently generated flag set I let p_I be its exact probability, S_I the span of S and flagged rows, and c_I the public complement on flagged bits for crossover above one half. For continuation survival bounds f_o, define

    g_S(w) = sum_I p_I 2^(-|I^c|) sum_u f_(w_I+c_I,u)(S_I).

The coherent rule is min_{w in im L} g_S(w). The coset rule is the minimum, over cosets C of D_S = L ker S in im L, of the uniform average of g_S on C. Evaluators use their own continuation bounds recursively and the existing epoch recurrence.

### Soundness

Fix a live observation-entrance history h and a feasible value SX=s. The conditional identity is uniform on its affine fiber. Therefore W=LX is uniform on one coset C of D_S. For each I, the continuation inequality is justified conditional on I, the flagged signal W_I, the independent fair output U, and the augmented shadow. It is NOT asserted conditional on the full W. First average these valid inequalities over W_I and U, then over I. Rewriting the resulting finite sums gives E[g_S(W) | h,SX=s], exactly the uniform average on C. This is an algebraic exchange of expectations, not stronger conditioning of the continuation. The minimum coset average bounds it from below, as does the minimum individual signal cost. Average over old shadow values and use finite backward induction. The existing one-time average-min-entropy transfer applies without alteration.

### Domination in the exact-coverage domain

First prove shadow monotonicity of each new evaluator. When row(S) is a subspace of row(T), epoch innovation cannot increase, so exact rank-monotone hazards cannot decrease; continuation survival also decreases by induction. At an observation, every partial extension S_I is contained in T_I, so g_S(w) is at least g_T(w) pointwise by induction. Moreover L ker(T) is contained in L ker(S). Each old coset partitions into refined cosets, and its average is at least their minimum. These facts prove monotonicity of both coherent and coset survival evaluators.

Comparing evaluators by backward induction, a coset average is at least a minimum over individual signals, and a minimum after summing flag costs is at least the sum of flag-wise minima. Hence F_C >= F_H >= F_R. To compare F_H with F_F, use monotonicity to replace every partially charged continuation f_o(S_I) by the no-larger f_o(S+L), then apply the induction comparison at that continuation. The flag mixture now recombines into the original channel kernel K(o|w), giving precisely the full-channel expression after minimizing w. Consequently B_C <= B_H <= min(B_R,B_F) <= B_0. A local conservative hazard still gives soundness. Domination across a numerical exact/upper-bound regime switch is not claimed without its additional monotonicity check; issued bounds take a minimum of independently sound bounds there.

### Distinct remaining precision losses

The stored refinement-coupling case changes raw flag-wise risk 53/64 to coherent and coset risk 51/64; the posterior oracle remains 11/16 because the abstraction does not retain shadow values. In flag-information, X is uniform on two bits, L is identity, independent crossover is 1/4, and one epoch permits two exact guesses of X. Coherent and coset risk is 7/8: with no flag, success is 1/2, while at least one flag permits both possible values of the remaining bit. No-flag probability is (1-rho)^2=1/4. Actual posterior masses are 9/16,3/16,3/16,1/16 for each output, so its two largest masses sum to 3/4. This is an information grant by proof flags, not a soundness violation.

### Computing the coset partition

Reduce S over GF(2). Every free column yields a nullspace generator by setting that free bit to one and solving the pivot bits. Apply L to these generators and row-reduce their m-bit images to obtain D_S. Enumerate its span and partition im L into its translates. This requires at most 2^m image elements, plus polynomial binary linear algebra in d. No enumeration of the 2^d latent identities occurs in this certificate step. The separate finite checker enumerates actual fibers only in its tightly bounded validation domain.
