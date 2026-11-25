"""Exact test-only version-header inverse for the accepted W3 source identities."""
import hashlib

# (W3 SHA-256, v11.2.0 SHA-256). This is not a business authority.
V1120_SOURCE_IDENTITIES = {
    'core/workflow_router.yaml': (
        'c9164051c5fe343ef7e8bb34bb6afc2f2a3beaa47d48a6610aa9a43aae2d9981',
        'fcfb4c1da8ceedf2c0fafdf1371832a7d4147c36f9fb03df36ffcd677d46911a',
    ),
    'core/bootstrap.yaml': (
        'df54cb35feee76dced9d46f944011a4d2968f01bb77251985822c132974c5298',
        'f0d1314f657e7c6ef47b052ad018511ad58fef16578660a087a093606fa6a43c',
    ),
    'core/hsk_core_policy.md': (
        '3059ad8708b0a539bc55cd857d7dc6dd18833dc370d795861f5f3e54b727d784',
        '35aded644ce7b978a02498d93c00a1f5e59e54d3f70a8d80efef7facac585a73',
    ),
    'core/writing_runtime_contract.yaml': (
        'f30a6133ab1a8c3f97fc6a26e873518e303fae0c2a8a1bd7dac48cd62fdb6e57',
        '80b0ecff6a962fef52aad606e2bff9b0abb3501d8a9fe9b248a0c70584c1cc38',
    ),
    'core/output_contract.yaml': (
        '11a647712355a29de942062fa26c09d21baa5bfe3360c79df90d34021a78be05',
        '7e69b8b4f7c6c4225c65fd0f37a93dcc1239ce18fabccb5cef02af5d0a62fd67',
    ),
}


def prior_v1120_release_bytes(relative: str, raw: bytes) -> bytes:
    """Reverse just the one registered version line after binding actual bytes."""
    prior_sha, current_sha = V1120_SOURCE_IDENTITIES[relative]
    if hashlib.sha256(raw).hexdigest() != current_sha:
        raise ValueError(f"{relative}: v11.2.0 release source identity drift")
    if raw.count(b"11.2.0") != 1:
        raise ValueError(f"{relative}: missing or duplicate release marker")
    predecessor = raw.replace(b"11.2.0", b"11.1.0", 1)
    if hashlib.sha256(predecessor).hexdigest() != prior_sha:
        raise ValueError(f"{relative}: v11.2.0 predecessor identity drift")
    return predecessor
