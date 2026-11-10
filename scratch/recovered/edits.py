src = open('/tmp/base-ci.yml').read()

def rep(old, new, n=1):
    global src
    assert src.count(old) == n, 'anchor count %d != %d for: %r' % (src.count(old), n, old[:70])
    src = src.replace(old, new)

# ---- 1. Concurrency: never cancel the default branch mid-flight ----
rep('''# One run per ref at a time. Rapid successive pushes used to queue
# duplicate runs behind each other, each paying the full multi-minute
# KiCad install; now a new push cancels the stale run on the same ref.
# (On 2026-11-03 the main and routing-history runs also installed
# KiCad CONCURRENTLY from the same Launchpad mirror and both crawled
# for 7+ minutes — per-ref groups don't prevent that cross-branch
# case, but they stop the self-inflicted same-ref pile-ups.)
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true''',
'''# One run per ref at a time. Rapid successive pushes used to queue
# duplicate runs behind each other, each paying the full multi-minute
# KiCad install; now a new push cancels the stale run on the same ref.
# (On 2026-11-03 the main and routing-history runs also installed
# KiCad CONCURRENTLY from the same Launchpad mirror and both crawled
# for 7+ minutes — per-ref groups don't prevent that cross-branch
# case, but they stop the self-inflicted same-ref pile-ups.)
# Exception (2026-11-04, apt-cache round 2): the DEFAULT branch is
# never cancelled mid-flight. Step timings showed main runs
# 41814248099 and 41815056150 cancelled while the sim job's install
# step was mid-crawl (456 s and 309 s in) — in the Actions UI a
# cancelled run looks exactly like a 5-10 minute install, and the
# work is thrown away either way. With cancel-in-progress off for
# main, a new push queues as the group's one pending run (a third
# push supersedes the pending one, never the running one), so the
# in-flight run finishes and lands its site/status. 'main' is this
# repo's default branch (verified via the API). Feature branches
# and PRs keep cancel-in-progress: their stale runs are worthless.
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}''')

# ---- 2. kicad-validate: stale runtime comment ----
rep('''    # Healthy total runtime for this job is ~5 minutes, almost all of
    # it the KiCad install below. A sick Launchpad mirror turned that
    # install into a 7+ minute silent crawl on 2026-11-03 (twice,
    # concurrently); 25 minutes is generous headroom that still fails
    # a truly stuck job fast instead of eating a runner for an hour.''',
'''    # Healthy total runtime for this job is ~1.5 minutes (step
    # timings, 2026-11-04: 51-120 s across the day's runs), most of
    # it the KiCad install below. A sick Launchpad mirror turned that
    # install into a 7+ minute silent crawl on 2026-11-03 (twice,
    # concurrently); 25 minutes is generous headroom that still fails
    # a truly stuck job fast instead of eating a runner for an hour.''')

# ---- 3. kicad restore: rolling key, restore-only action ----
rep('''      # .deb cache for the install step below. Keyed on this file's
      # hash because the install package list lives in this file —
      # change the list and the key changes; the restore-keys prefix
      # still gives best-effort reuse across unrelated workflow edits.
      # apt reuses a version-exact .deb already sitting in
      # /var/cache/apt/archives instead of re-downloading it, so on a
      # cache hit the slow PPA mirror is barely touched. A cache miss
      # behaves exactly like the pre-cache workflow.
      - name: Restore cached .deb packages
        id: apt-cache
        uses: actions/cache@v4
        with:
          path: /var/cache/apt/archives
          key: apt-kicad8-${{ runner.os }}-${{ hashFiles('.github/workflows/ci.yml') }}
          restore-keys: |
            apt-kicad8-${{ runner.os }}-''',
'''      # .deb cache for the install step below. apt reuses a
      # version-exact .deb already sitting in /var/cache/apt/archives
      # instead of re-downloading it, so on a cache hit the slow PPA
      # mirror is barely touched. A cache miss behaves exactly like
      # the pre-cache workflow.
      # Rolling key (2026-11-04, apt-cache round 2): cache entries
      # are IMMUTABLE — a save under an already-used key is refused.
      # The old key (hash of this file) therefore froze the cached
      # set at whatever the first run under that hash downloaded: a
      # PPA point release afterwards meant every run restored the
      # stale .debs, re-downloaded the changed ones, and could never
      # save the fresh set. Now the primary key carries the run id —
      # unique per run, so the save below always lands — and
      # restore-keys fetches the NEWEST entry under the prefix,
      # i.e. the previous run's set. A changed package list or a PPA
      # bump self-heals on the next run instead of freezing. The
      # restore/save pair replaces the combined actions/cache action,
      # whose post-step auto-save duplicated the explicit save step
      # (visible as the extra "Post Restore cached .deb packages"
      # step in run logs).
      - name: Restore cached .deb packages
        id: apt-cache
        uses: actions/cache/restore@v4
        with:
          path: /var/cache/apt/archives
          key: apt-kicad8-${{ runner.os }}-${{ github.run_id }}
          restore-keys: |
            apt-kicad8-${{ runner.os }}-

      # Makes the restore legible from the job page: on a working
      # hit the matched key names the previous run that saved the
      # set, and this step + the save below take real seconds
      # (measured 0-1 s for this job's small set). An empty matched
      # key means the install below is paying full mirror price.
      - name: Report .deb cache restore
        run: |
          echo "cache primary key: ${{ steps.apt-cache.outputs.cache-primary-key }}"
          echo "cache matched key: ${{ steps.apt-cache.outputs.cache-matched-key }}"''')

# ---- 4. sim job: timeout + cache + docker-clean ----
rep('''  sim-and-firmware:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - name: Install simulation toolchain — ngspice, no KiCad
        run: |
          # Same one-retry guard as the KiCad job: this install is
          # small and normally takes ~45 s from the Ubuntu archive,
          # but a transient mirror hiccup should retry inside the
          # step instead of reddening the whole job. (No .deb cache
          # here — the archive is fast and the packages are modest;
          # caching machinery would cost more than it saves.)
          for attempt in 1 2; do''',
'''  sim-and-firmware:
    runs-on: ubuntu-22.04
    # The install step below is this job's only long pole; 25
    # minutes (mirroring kicad-validate) caps a truly hung apt
    # instead of letting it eat the 360-minute default.
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4

      # .deb cache (2026-11-04, apt-cache round 2). This job's
      # install turned out to be the workflow's real multi-minute
      # step — NOT the KiCad install. Step timings across
      # 2026-11-04's runs are bimodal: 47-73 s on a healthy mirror,
      # but 429 s (run 41752803331), 479 s (41787142236), 371 s
      # (41787138138), and 456 s / 309 s in runs 41814248099 /
      # 41815056150, which were still crawling when cancelled. The
      # set is big (gcc-arm-none-eabi + newlib + scipy = several
      # hundred MB) and comes from the Ubuntu archive; when that
      # mirror trickles at ~1.5 MB/s the step eats 5-8 minutes and
      # no retry loop helps — attempt 1 eventually SUCCEEDS, just
      # slowly. With the .debs restored from cache, apt downloads
      # ~nothing on a hit and mirror health barely matters. Same
      # rolling-key scheme as the KiCad job (immutable entries;
      # run-id primary key so the save always lands; restore-keys
      # fetches the newest set). Separate key namespace: the two
      # jobs' package sets barely overlap.
      - name: Restore cached .deb packages (sim)
        id: apt-cache-sim
        uses: actions/cache/restore@v4
        with:
          path: /var/cache/apt/archives
          key: apt-sim-${{ runner.os }}-${{ github.run_id }}
          restore-keys: |
            apt-sim-${{ runner.os }}-

      - name: Report .deb cache restore (sim)
        run: |
          echo "cache primary key: ${{ steps.apt-cache-sim.outputs.cache-primary-key }}"
          echo "cache matched key: ${{ steps.apt-cache-sim.outputs.cache-matched-key }}"

      - name: Install simulation toolchain — ngspice, no KiCad
        run: |
          # Same docker-clean removal as the KiCad job, and here it
          # is load-bearing for the cache: GitHub's ubuntu images
          # ship an apt config that deletes downloaded .debs after
          # every transaction — without removing it, the archives
          # directory is empty again by the time the save step runs
          # and the cache would save nothing, forever.
          sudo rm -f /etc/apt/apt.conf.d/docker-clean
          # Same one-retry guard as the KiCad job: a transient mirror
          # hiccup should retry inside the step instead of reddening
          # the whole job.
          for attempt in 1 2; do''')

# ---- 5. sim save step, right after the install step ----
rep('''            echo "apt attempt $attempt failed — retrying in 20 s" >&2
            sleep 20
          done

      - name: Simulations, codec, firmware, host tool (ci.sh steps 1-9)''',
'''            echo "apt attempt $attempt failed — retrying in 20 s" >&2
            sleep 20
          done

      - name: Save .deb packages to cache (sim)
        if: success()
        uses: actions/cache/save@v4
        with:
          path: /var/cache/apt/archives
          key: ${{ steps.apt-cache-sim.outputs.cache-primary-key }}

      - name: Simulations, codec, firmware, host tool (ci.sh steps 1-9)''')

open('/tmp/my-ci.yml', 'w').write(src)
print('edits applied OK')
