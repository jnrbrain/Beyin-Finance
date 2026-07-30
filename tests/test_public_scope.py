from pathlib import Path
import json
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = (ROOT / "docs" / "endpoints.md").read_text(encoding="utf-8")
PUBLISHED_SOURCE = "\n".join(
    [
        (ROOT / "README.md").read_text(encoding="utf-8"),
        (ROOT / "docs" / "index.rst").read_text(encoding="utf-8"),
        ENDPOINTS,
    ]
)


class PublicReferenceScopeTests(unittest.TestCase):
    PUBLIC_USER_OPERATIONS = {
        "account_info",
        "active_signals",
        "available_coins",
        "backtest_history",
        "binance_balance",
        "binance_order",
        "binance_order_preview",
        "community_chat_send",
        "community_follow",
        "community_leader_apply",
        "community_leader_update",
        "community_post_comment",
        "community_post_create",
        "community_post_like",
        "community_post_report",
        "community_unfollow",
        "credits_history",
        "economic_calendar",
        "economic_news",
        "login_history",
        "marketplace_listing_detail",
        "marketplace_my_listings",
        "marketplace_my_subscriptions",
        "marketplace_publish",
        "marketplace_review",
        "marketplace_subscribe",
        "marketplace_unpublish",
        "marketplace_unsubscribe",
        "marketplace_update_listing",
        "notifications_list",
        "notifications_mark_read",
        "order_history",
        "signal_history",
        "strategy_delete",
        "strategy_detail",
        "strategy_edit",
        "strategy_generate",
        "strategy_rollback",
        "strategy_versions",
        "strategy_visibility",
    }
    PUBLIC_BACKTEST_ACTIONS = {
        "delete_backtest",
        "estimate",
        "full_range",
        "info",
        "list_timeframes",
        "result",
        "run",
        "status",
    }
    PUBLIC_TRADING_DATA_OPERATIONS = {
        "community_chat",
        "community_leaders",
        "community_posts",
        "market_quote",
        "marketplace_browse",
        "marketplace_listing",
        "marketplace_reviews",
        "platform_notifications",
        "trend_indicator",
        "trend_indicator_history",
        "trend_signal_detail",
        "trend_signals",
    }

    def test_published_operations_exactly_match_public_allowlist(self):
        user_operations = set(
            re.findall(r"POST /user\?request_type=([a-z0-9_]+)", ENDPOINTS)
        )
        trading_data_operations = set(
            re.findall(
                r"GET /tradingdata\?request_type=([a-z0-9_]+)",
                ENDPOINTS,
            )
        )
        backtest_actions = set(
            re.findall(r"/backtest\?action=([a-z0-9_]+)", ENDPOINTS)
        )
        backtest_actions.discard("action")
        self.assertEqual(user_operations, self.PUBLIC_USER_OPERATIONS)
        self.assertEqual(
            trading_data_operations,
            self.PUBLIC_TRADING_DATA_OPERATIONS,
        )
        self.assertEqual(backtest_actions, self.PUBLIC_BACKTEST_ACTIONS)

    def test_unavailable_routes_are_not_advertised(self):
        self.assertNotIn(
            "GET /tradingdata?request_type=market_ticker",
            PUBLISHED_SOURCE,
        )

    def test_public_docs_do_not_expose_internal_system_details(self):
        forbidden_terms = [
            "execute-api",
            "Lambda",
            "DynamoDB",
            "S3",
            "worker",
            "concurrency",
            "Fair-Share",
            "fair-share",
            "max_workers",
            "active_workers",
            "queued_workers",
            "chunks_total",
            "chunks_done",
            "signal_position_key",
            "local_order_key",
            "request_hash",
            "BFOCO",
            "binanceExchangeInfo",
            "unknown_checking",
            "No authentication is required",
            "No auth required",
            "Public Trading Data routes",
            "credential-free",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, PUBLISHED_SOURCE)

    def test_repository_metadata_is_real_and_buildable(self):
        metadata = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        project = metadata["project"]
        self.assertEqual(project["readme"], "README.md")
        self.assertTrue((ROOT / project["readme"]).is_file())
        self.assertEqual(project["version"], "2.0.0")
        self.assertEqual(project["dependencies"], [])
        serialized = json.dumps(metadata, ensure_ascii=False)
        for placeholder in ("Senin Adın", "sen@example.com", "kullaniciadi"):
            self.assertNotIn(placeholder, serialized)


if __name__ == "__main__":
    unittest.main()
