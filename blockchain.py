"""
CampusChain blockchain module — Phase 4.

Design: a single-node, append-only SHA-256 hash chain. No mining, no
networked consensus — the goal is tamper-evidence for completed
transactions, not a distributed ledger. Blocks are stored as rows in
the `blockchain_blocks` MySQL table (see models.BlockchainBlock);
this module only contains the hashing and validation logic.

Only transaction IDs and user/product IDs go into a block — never
private data like emails or phone numbers.
"""

import hashlib
from datetime import datetime, timezone
from extensions import db
from models import BlockchainBlock

GENESIS_PREVIOUS_HASH = "0" * 64


def _compute_hash(index, transaction_id, product_id, seller_id, buyer_id, timestamp, previous_hash):
    """
    SHA-256 over the block's own fields plus the previous block's hash.
    Changing any field of any past block changes its hash, which breaks
    the previous_hash link for every block after it — that break is what
    makes tampering detectable.
    """
    payload = f"{index}|{transaction_id}|{product_id}|{seller_id}|{buyer_id}|{timestamp}|{previous_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_last_block():
    return BlockchainBlock.query.order_by(BlockchainBlock.id.desc()).first()


def init_genesis_block_if_needed():
    """Call once at startup. Creates block #0 if the chain is empty."""
    if BlockchainBlock.query.first() is not None:
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    genesis_hash = _compute_hash(0, "genesis", 0, 0, 0, timestamp, GENESIS_PREVIOUS_HASH)

    genesis = BlockchainBlock(
        transaction_id=0,
        seller_id=0,
        buyer_id=0,
        product_id=0,
        timestamp=datetime.now(timezone.utc),
        previous_hash=GENESIS_PREVIOUS_HASH,
        current_hash=genesis_hash,
    )
    db.session.add(genesis)
    db.session.commit()


def add_block(transaction):
    """
    Append a new block for a completed Transaction (models.Transaction).
    Returns the created BlockchainBlock. Call this from
    routes/products.py -> complete_transaction(), inside the same
    request so the DB row and the block are written together.
    """
    last_block = _get_last_block()
    previous_hash = last_block.current_hash if last_block else GENESIS_PREVIOUS_HASH
    index = (last_block.id + 1) if last_block else 0

    timestamp_dt = datetime.now(timezone.utc)
    timestamp_str = timestamp_dt.isoformat()

    current_hash = _compute_hash(
        index,
        transaction.id,
        transaction.product_id,
        transaction.seller_id,
        transaction.buyer_id,
        timestamp_str,
        previous_hash,
    )

    block = BlockchainBlock(
        transaction_id=transaction.id,
        seller_id=transaction.seller_id,
        buyer_id=transaction.buyer_id,
        product_id=transaction.product_id,
        timestamp=timestamp_dt,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.session.add(block)
    db.session.flush()  # get block.id without committing yet

    transaction.block_id = block.id
    db.session.commit()
    return block


def validate_chain():
    """
    Walk every block, recompute its hash from its stored fields, and
    check it against what's stored — and that previous_hash correctly
    points at the prior block's hash. Returns a dict summary used by
    the admin dashboard's "Validate chain integrity" button.
    """
    blocks = BlockchainBlock.query.order_by(BlockchainBlock.id.asc()).all()
    if not blocks:
        return {"valid": True, "blocks_checked": 0, "broken_at_block_id": None}

    expected_previous = GENESIS_PREVIOUS_HASH
    for i, block in enumerate(blocks):
        recomputed = _compute_hash(
            i,
            block.transaction_id,
            block.product_id,
            block.seller_id,
            block.buyer_id,
            block.timestamp.isoformat(),
            block.previous_hash,
        )

        if block.previous_hash != expected_previous or recomputed != block.current_hash:
            return {
                "valid": False,
                "blocks_checked": i + 1,
                "broken_at_block_id": block.id,
            }

        expected_previous = block.current_hash

    return {"valid": True, "blocks_checked": len(blocks), "broken_at_block_id": None}
