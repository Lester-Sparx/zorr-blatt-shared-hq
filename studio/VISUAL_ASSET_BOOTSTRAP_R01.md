# ZORR VISUAL ASSET BOOTSTRAP R01

STATUS = CANDIDATE
PURPOSE = make every production visual reference directly addressable and byte-verifiable from a fresh session without storing large binaries in `main`
INDEX = `studio/VISUAL_ASSET_INDEX_R01.json`

## PRODUCT BLOCKER THIS REMOVES

Current character references were recorded by hash and/or old ChatGPT Library IDs, but several exact source bytes are not directly retrievable in the current runtime. That forces repeated archive searches before ordinary shot work.

The repair is deliberately small: one index plus one retrieval law. No database, daemon, custom asset server, second archive, or large binary storage in Git is introduced.

## HARD READY LAW

A visual source is production-ready only when all of the following are present:

```text
STABLE ASSET ID
+ SHA-256 OF EXACT BYTES
+ IMMUTABLE DURABLE LOCATOR
+ MEDIA TYPE
+ AUTHORITY REF
+ RETRIEVAL STATE = READY
```

`KNOWN HASH != RETRIEVABLE ASSET`

`LEGACY CHATGPT LIBRARY ID != DURABLE LOCATOR`

`APPROVED VISUAL MEANING != SOURCE BYTES READY`

Missing any required field means the source remains blocked for fresh-session production use. Never substitute a similar-looking image.

## STORAGE LAW

Keep the existing large-binary rule:

```text
large visual bytes -> immutable/versioned GitHub Release asset
metadata/index -> repository text file
```

Do not place large PNG/JPG/ZIP production packs directly into `main`.

Preferred durable locator fields after migration:

```text
locator_type = GITHUB_RELEASE_ASSET
release_tag = <immutable/versioned tag>
asset_name = <exact filename>
asset_id = <GitHub release asset id when available>
browser_download_url = <exact release asset URL>
sha256 = <exact bytes>
```

## FRESH-SESSION RETRIEVAL

For every required shot/source asset:

```text
1. resolve stable asset_id in VISUAL_ASSET_INDEX_R01.json
2. require retrieval_state == READY
3. fetch exact immutable locator
4. materialize exact bytes
5. compute SHA-256
6. require computed SHA-256 == indexed SHA-256
7. only then expose/use the asset for production
```

If steps 2-6 fail:

`VISUAL_SOURCE_BYTES_NOT_READY`

Stop that asset path immediately; do not search by appearance and do not invent a substitute.

## LEGACY MIGRATION

Legacy sources are migrated one asset at a time, only from exact bytes whose SHA-256 matches the existing authority record.

Migration:

```text
recover exact legacy bytes
-> verify old authoritative SHA-256
-> publish once as versioned GitHub Release asset
-> record exact release coordinates in index
-> fresh download
-> fresh SHA-256 verify
-> retrieval_state = READY
```

A migration may not change the image bytes, redraw the source, or promote a different visual because it looks similar.

## CURRENT IMMEDIATE BLOCKER

`C00_D_BODY_TURNAROUND` is the required source for the requested side-view work.

Known authoritative SHA-256:

`49f1c5fa9973f185c4ed7441325e2705d392449f6d59b4592ec6d81bc4b4da82`

Current state:

`BLOCKED_NO_DURABLE_LOCATOR`

The old suit five-view reference also has a known ChatGPT Library file ID:

`file_0000000004f882469dfa7a8b272ac5c4`

but prior fresh retrieval attempts recorded in #248 proved that this Library ID is not visible/materializable in the current runtime. It therefore remains legacy discovery metadata, not a production locator.

## ACCEPTANCE FOR THIS BOOTSTRAP

The asset-bootstrap repair is not terminally proven until at least one required production visual passes the complete real retrieval loop:

```text
INDEX LOOKUP
-> IMMUTABLE DOWNLOAD
-> SHA-256 MATCH
-> EXACT ASSET AVAILABLE IN FRESH SESSION
```

The first intended proof is `C00_D_BODY_TURNAROUND`.

Until that proof exists:

`VISUAL_ASSET_BOOTSTRAP_R01 = CANDIDATE / INDEXED / PHYSICAL RETRIEVAL NOT YET PROVEN`
