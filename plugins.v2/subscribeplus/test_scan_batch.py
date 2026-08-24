import unittest

from scan_batch import select_scan_batch


class SelectScanBatchTest(unittest.TestCase):
    def test_rotates_past_first_batch(self):
        items = list(range(25))

        first, next_cursor = select_scan_batch(items, limit=20, cursor=0)
        second, final_cursor = select_scan_batch(items, limit=20, cursor=next_cursor)

        self.assertEqual(first, list(range(20)))
        self.assertEqual(next_cursor, 20)
        self.assertEqual(second[:5], list(range(20, 25)))
        self.assertEqual(final_cursor, 15)

    def test_normalizes_cursor_after_candidate_count_changes(self):
        batch, next_cursor = select_scan_batch(list(range(3)), limit=2, cursor=8)

        self.assertEqual(batch, [2, 0])
        self.assertEqual(next_cursor, 1)

    def test_empty_items_reset_cursor(self):
        batch, next_cursor = select_scan_batch([], limit=20, cursor=12)

        self.assertEqual(batch, [])
        self.assertEqual(next_cursor, 0)


if __name__ == "__main__":
    unittest.main()
