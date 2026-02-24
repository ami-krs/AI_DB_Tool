"""
Smart CSV/table import: auto-map columns (case-insensitive) and handle primary key
duplicates (remap numeric PKs, skip duplicate rows for non-numeric PKs).
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from ai_db_tool.connectors.base import DatabaseManager


def _quote_identifier(identifier: str, db_type: str) -> str:
    if (db_type or "").lower() == "mysql":
        return f"`{identifier.replace('`', '``')}`"
    return f'"{identifier.replace(chr(34), chr(34) + chr(34))}"'


def _quote_table(table_name: str, db_type: str) -> str:
    if "." in table_name:
        s, t = table_name.split(".", 1)
        return f"{_quote_identifier(s, db_type)}.{_quote_identifier(t, db_type)}"
    return _quote_identifier(table_name, db_type)


def smart_import(
    dbm: DatabaseManager,
    table_name: str,
    rows: List[Dict[str, Any]],
    db_type: str = "postgresql",
) -> Dict[str, Any]:
    """
    Import rows into table with auto column mapping and PK handling.
    rows: list of dicts with keys = CSV/upload column names (any case).
    Returns: inserted, skipped_existing_pk, skipped_file_duplicate_pk,
             remapped_pk_count, remapped_pk_column, hint (optional message).
    """
    schema = dbm.get_table_schema(table_name)
    table_columns = [c.get("name") for c in (schema.get("columns") or []) if c.get("name")]
    if not table_columns:
        raise ValueError(f"Could not fetch columns for table '{table_name}'.")

    # Case-insensitive map: upload key -> table column name
    table_lookup = {str(c).strip().lower(): c for c in table_columns}
    rename_map: Dict[str, str] = {}
    unmatched: List[str] = []
    for raw_key in (rows[0].keys() if rows else []):
        norm = str(raw_key).strip().lower()
        if norm in table_lookup:
            rename_map[raw_key] = table_lookup[norm]
        else:
            unmatched.append(str(raw_key))

    if unmatched:
        raise ValueError(
            "File has columns that do not exist in target table: " + ", ".join(unmatched)
        )

    # Build prepared rows: list of dicts with table column names only
    ordered_cols = [c for c in table_columns if any(rename_map.get(k) == c for k in rename_map)]
    if not ordered_cols:
        raise ValueError("No matching columns between file and table.")

    prepared = []
    for row in rows:
        prep: Dict[str, Any] = {}
        for upload_key, table_col in rename_map.items():
            if table_col in ordered_cols and upload_key in row:
                prep[table_col] = row[upload_key]
        prepared.append(prep)

    if not prepared:
        raise ValueError("Uploaded file has no rows to insert.")

    # Primary key handling
    primary_keys = [pk for pk in (schema.get("primary_keys") or []) if pk]
    remapped_pk_count = 0
    remapped_pk_column = ""
    skipped_existing_pk = 0
    skipped_file_duplicate_pk = 0

    if len(primary_keys) == 1:
        pk_col = primary_keys[0]
        if pk_col not in ordered_cols:
            primary_keys = []
        else:
            pk_ident = _quote_identifier(pk_col, db_type)
            table_ref = _quote_table(table_name, db_type)
            df = pd.DataFrame(prepared)

            numeric_pk = pd.to_numeric(df[pk_col], errors="coerce")
            has_non_numeric = bool(numeric_pk.isna().any() and df[pk_col].notna().any())

            if not has_non_numeric:
                # Numeric PK: get max, find overlapping, remap duplicates
                try:
                    max_df = dbm.execute_query(
                        f"SELECT COALESCE(MAX({pk_ident}), 0) AS mx FROM {table_ref}"
                    )
                    max_existing = int(max_df.iloc[0, 0]) if max_df is not None and len(max_df) else 0
                except Exception:
                    max_existing = 0

                upload_ids = [int(float(v)) if v is not None and str(v).strip() != "" else 0 for v in df[pk_col].tolist()]
                unique_ids = sorted(set(u for u in upload_ids if u != 0))
                existing_ids: set = set()
                if unique_ids:
                    in_clause = ", ".join(str(v) for v in unique_ids)
                    try:
                        overlap_df = dbm.execute_query(
                            f"SELECT {pk_ident} AS id FROM {table_ref} WHERE {pk_ident} IN ({in_clause})"
                        )
                        if overlap_df is not None and len(overlap_df):
                            existing_ids = {int(float(v)) for v in overlap_df["id"].tolist() if v is not None}
                    except Exception:
                        pass

                seen: set = set()
                next_id = max_existing + 1
                remapped: List[int] = []
                for orig in upload_ids:
                    if orig in existing_ids or orig in seen or orig == 0:
                        while next_id in existing_ids or next_id in seen:
                            next_id += 1
                        remapped.append(next_id)
                        seen.add(next_id)
                        remapped_pk_count += 1
                        next_id += 1
                    else:
                        remapped.append(orig)
                        seen.add(orig)
                df[pk_col] = remapped
                remapped_pk_column = pk_col
                prepared = df.to_dict(orient="records")
            else:
                # Non-numeric PK: skip rows that already exist or are duplicate in file
                pk_vals = [v for v in df[pk_col].tolist() if v is not None and pd.notna(v)]
                unique_pk_vals = list(dict.fromkeys(pk_vals))
                existing_pk_vals: set = set()
                chunk_size = 500
                for start in range(0, len(unique_pk_vals), chunk_size):
                    chunk = unique_pk_vals[start : start + chunk_size]
                    if not chunk:
                        continue
                    safe = []
                    for v in chunk:
                        if v is None or (isinstance(v, float) and pd.isna(v)):
                            continue
                        s = str(v).replace("'", "''")
                        safe.append(f"'{s}'")
                    in_clause = ", ".join(safe)
                    try:
                        overlap_df = dbm.execute_query(
                            f"SELECT {pk_ident} AS id FROM {table_ref} WHERE {pk_ident} IN ({in_clause})"
                        )
                        if overlap_df is not None and len(overlap_df):
                            for val in overlap_df["id"].tolist():
                                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                                    existing_pk_vals.add(str(val))
                    except Exception:
                        pass

                pk_str = df[pk_col].astype(str)
                existing_mask = pk_str.isin(existing_pk_vals)
                dup_mask = pk_str.duplicated(keep="first")
                keep = ~(existing_mask | dup_mask)
                skipped_existing_pk = int(existing_mask.sum())
                skipped_file_duplicate_pk = int((~existing_mask & dup_mask).sum())
                df = df.loc[keep].copy()
                prepared = df.to_dict(orient="records")

    if not prepared:
        if skipped_existing_pk > 0 or skipped_file_duplicate_pk > 0:
            raise ValueError(
                "No rows inserted: all uploaded rows had duplicate primary key values "
                "that already exist (or were duplicated in the uploaded file)."
            )
        raise ValueError("Uploaded file has no rows to insert.")

    inserted = dbm.insert_rows(table_name, ordered_cols, prepared)

    hints: List[str] = []
    if remapped_pk_count > 0 and remapped_pk_column:
        hints.append(
            f"Auto-adjusted {remapped_pk_count} duplicate `{remapped_pk_column}` value(s) to the next available IDs."
        )
    if skipped_existing_pk > 0 or skipped_file_duplicate_pk > 0:
        hints.append(
            f"Skipped {skipped_existing_pk} row(s) with PK already in table and "
            f"{skipped_file_duplicate_pk} duplicate PK row(s) in the file."
        )

    return {
        "inserted": inserted,
        "table": table_name,
        "loaded_columns": ordered_cols,
        "remapped_pk_count": remapped_pk_count,
        "remapped_pk_column": remapped_pk_column or None,
        "skipped_existing_pk_count": skipped_existing_pk,
        "skipped_file_duplicate_pk_count": skipped_file_duplicate_pk,
        "hint": " ".join(hints) if hints else None,
    }
