from p36.cleaning import apply_canonical_dtypes
from p36.dataset import DEDUPED_PATH, PROCESSED_DIR, RAW_PATH
from p36.ingest import deduplicate_by_eid, load_all_universities

def main() -> None:
    print("Loading all 8 university exports...")
    df = load_all_universities()
    df = apply_canonical_dtypes(df)
    print(f"  raw rows: {len(df):,} ({df['source_university'].nunique()} universities)")

    deduped = deduplicate_by_eid(df)
    print(f"  deduplicated rows: {len(deduped):,}")
    dup_pct = 100 * (1 - len(deduped) / len(df))
    print(f"  cross-university duplication: {dup_pct:.1f}%")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(RAW_PATH, index=False)
    deduped.to_parquet(DEDUPED_PATH, index=False)
    print(f"Wrote {RAW_PATH}")
    print(f"Wrote {DEDUPED_PATH}")

if __name__ == "__main__":
    main()
