from __future__ import annotations

import unittest

from fastapi_silk.profiler import _extract_table_refs


class TestProfilerTableExtraction(unittest.TestCase):
    def test_extracts_schema_and_table_for_join_queries(self) -> None:
        statement = (
            'SELECT * FROM "public"."users" u JOIN public.orders o ON o.user_id = u.id'
        )

        refs = _extract_table_refs(statement)

        self.assertEqual(
            refs,
            [
                {"schema": "public", "table": "users"},
                {"schema": "public", "table": "orders"},
            ],
        )

    def test_extracts_table_for_delete_update_insert(self) -> None:
        delete_refs = _extract_table_refs("DELETE FROM logs WHERE id = 1")
        update_refs = _extract_table_refs("UPDATE users SET name='x' WHERE id = 1")
        insert_refs = _extract_table_refs("INSERT INTO users (name) VALUES ('x')")

        self.assertEqual(delete_refs, [{"schema": None, "table": "logs"}])
        self.assertEqual(update_refs, [{"schema": None, "table": "users"}])
        self.assertEqual(insert_refs, [{"schema": None, "table": "users"}])


if __name__ == "__main__":
    unittest.main()
